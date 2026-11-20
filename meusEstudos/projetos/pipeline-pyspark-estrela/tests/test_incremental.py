"""Testes da carga incremental.

Unitários (sem banco): SQL gerado, lista de colunas contra o DDL, geração de lotes, silver de lote.
Integração (``-m integration``, precisam de PostgreSQL em POSTGRES_HOST): MERGE de verdade, num
schema isolado (``t_dw``/``t_stage``), sem tocar nos dados do laboratório.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from pipeline.generate_data import gerar_lotes
from pipeline.incremental import (
    ATUALIZACAO_CLIENTE,
    ATUALIZACAO_FATO,
    COLUNAS,
    comandos_de_mescla,
    criar_modelo,
    listar_lotes,
    processar_lote,
    preparar_banco,
    run_incremental,
    sha256_arquivo,
    sql_criar_controle,
    sql_merge_atualizar,
    sql_merge_inserir,
    sql_registrar_lote,
    trava_do_schema,
)
from pipeline.load_postgres import _conexao, _executar_em_transacao
from pipeline.transform import build_dim_canal, build_dim_cliente, build_dim_data, build_dim_pagamento
from pipeline.transform import build_dim_produto, build_fato_vendas, build_silver_from_orders, clean_products, read_products

DDL = Path(__file__).resolve().parents[1] / "sql" / "01_ddl_estrela.sql"
CATALOGO = (
    "sku,product_name,category,subcategory,brand,cost\n"
    "SKU00001,Fone,Eletrônicos,Áudio,Aurora,40.00\n"
    "SKU00002,Livro,Livros,Técnicos,Atlas,10.00\n"
)


# --------------------------------------------------------------------------- #
# Auxiliares
# --------------------------------------------------------------------------- #
def _item(sku="SKU00001", qty=2, preco=100.0, desc=0.0):
    return {"sku": sku, "qty": qty, "unit_price": preco, "discount": desc}


def _pedido(order_id, itens, status="ENTREGUE", cliente="C1", cidade="Recife", ts="2025-01-01T10:00:00"):
    return {
        "order_id": order_id, "order_ts": ts, "status": status, "channel": "site",
        "customer": {"id": cliente, "name": "Ana", "city": cidade, "state": "PE", "segment": "varejo"},
        "payment": {"method": "pix", "installments": 1},
        "items": itens,
    }


def _escrever_lote(pasta: Path, nome: str, pedidos: list[dict]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"{nome}.jsonl"
    arquivo.write_text("\n".join(json.dumps(p) for p in pedidos) + "\n", encoding="utf-8")
    return arquivo


@pytest.fixture
def produtos_csv(tmp_path) -> Path:
    arquivo = tmp_path / "products.csv"
    arquivo.write_text(CATALOGO, encoding="utf-8")
    return arquivo


# --------------------------------------------------------------------------- #
# Unitários
# --------------------------------------------------------------------------- #
def _colunas_do_ddl(tabela: str) -> list[str]:
    texto = DDL.read_text(encoding="utf-8")
    corpo = re.search(rf"CREATE TABLE {tabela} \((.*?)\n\);", texto, re.S).group(1)
    colunas = []
    for linha in corpo.splitlines():
        palavra = linha.strip().split(" ")[0] if linha.strip() else ""
        if palavra and not palavra.startswith("--") and palavra.upper() not in {"PRIMARY", "UNIQUE", "CONSTRAINT", "FOREIGN", "CHECK"}:
            colunas.append(palavra)
    return colunas


@pytest.mark.parametrize("tabela", list(COLUNAS))
def test_colunas_do_merge_batem_com_o_ddl(tabela):
    # se alguém mudar o DDL e esquecer o MERGE (ou vice-versa), este teste quebra
    assert COLUNAS[tabela] == _colunas_do_ddl(tabela)


def test_colunas_do_merge_batem_com_os_dataframes_da_gold(spark, tmp_path, produtos_csv):
    produtos, _ = clean_products(read_products(spark, produtos_csv))
    arquivo = _escrever_lote(tmp_path / "l", "lote_0001", [_pedido("O1", [_item()])])
    itens = build_silver_from_orders(spark, arquivo, produtos).items
    gold = {
        "dim_data": build_dim_data(spark, itens), "dim_cliente": build_dim_cliente(itens),
        "dim_produto": build_dim_produto(produtos), "dim_pagamento": build_dim_pagamento(itens),
        "dim_canal": build_dim_canal(itens), "fato_vendas": build_fato_vendas(itens, produtos),
    }
    # o Spark grava no staging por NOME de coluna: precisa haver exatamente as colunas do MERGE
    for tabela, df in gold.items():
        assert df.columns == COLUNAS[tabela], tabela


def test_sql_do_merge_tem_a_forma_esperada():
    fato = sql_merge_atualizar("dw", "stage_inc", "fato_vendas", ATUALIZACAO_FATO)
    assert fato.startswith("MERGE INTO dw.fato_vendas AS t USING stage_inc.fato_vendas AS s")
    assert "ON t.pedido_id = s.pedido_id AND t.item_seq = s.item_seq" in fato  # chave composta
    assert "WHEN MATCHED AND" in fato and "IS DISTINCT FROM" in fato  # não reescreve linha igual
    assert "WHEN NOT MATCHED THEN INSERT" in fato

    dimensao = sql_merge_inserir("dw", "stage_inc", "dim_data")
    assert "UPDATE" not in dimensao and "WHEN NOT MATCHED THEN INSERT" in dimensao  # dimensão imutável


def test_ordem_dos_comandos_remocao_e_dimensoes_antes_da_fato():
    comandos = comandos_de_mescla("dw", "stage_inc")
    assert comandos[0].startswith("DELETE FROM dw.fato_vendas")
    assert comandos[-1].startswith("MERGE INTO dw.fato_vendas")
    posicao_dim = max(i for i, c in enumerate(comandos) if "MERGE INTO dw.dim_" in c)
    assert posicao_dim < len(comandos) - 1  # toda dimensão antes da fato (que as referencia)


def test_dimensao_de_cliente_nao_deixa_um_nao_informado_apagar_valor_conhecido():
    sql = sql_merge_atualizar("dw", "stage_inc", "dim_cliente", ATUALIZACAO_CLIENTE)
    assert "CASE WHEN s.cidade = 'Não informada' THEN t.cidade ELSE s.cidade END" in sql


def test_registro_do_lote_e_um_upsert_na_tabela_de_controle():
    sql = sql_registrar_lote("dw", "lote_0001", "a" * 64, {
        "itens_validos": 10, "fato_inseridas": 8, "fato_atualizadas": 1, "fato_removidas": 1, "rejeitados": 2})
    assert "INSERT INTO dw.controle_cargas" in sql and "ON CONFLICT (lote) DO UPDATE" in sql


def test_nome_de_lote_invalido_e_recusado_antes_de_tocar_no_banco(tmp_path):
    arquivo = tmp_path / "lote'; DROP TABLE x; --.jsonl"
    try:
        arquivo.write_text("{}", encoding="utf-8")
    except OSError:
        pytest.skip("o sistema de arquivos não aceita este nome")
    with pytest.raises(ValueError, match="Nome de lote inválido"):
        processar_lote(None, arquivo, None)


def test_listar_lotes_em_ordem_de_chegada_e_checksum_detecta_mudanca(tmp_path):
    pasta = tmp_path / "lotes"
    for nome in ["lote_0003", "lote_0001", "lote_0002"]:
        _escrever_lote(pasta, nome, [_pedido("O1", [_item()])])
    (pasta / "ignorar.txt").write_text("x", encoding="utf-8")
    assert [a.stem for a in listar_lotes(pasta)] == ["lote_0001", "lote_0002", "lote_0003"]

    antes = sha256_arquivo(pasta / "lote_0001.jsonl")
    _escrever_lote(pasta, "lote_0001", [_pedido("O1", [_item(qty=9)])])
    assert sha256_arquivo(pasta / "lote_0001.jsonl") != antes


def test_gerador_de_lotes_e_deterministico_e_traz_reenvios_com_mudanca(tmp_path):
    a = gerar_lotes(3, 200, tmp_path / "a", seed=5)
    gerar_lotes(3, 200, tmp_path / "b", seed=5)
    assert a["atualizacoes"] > 0
    for nome in ["lote_0001.jsonl", "lote_0002.jsonl", "lote_0003.jsonl"]:
        assert (tmp_path / "a" / "lotes" / nome).read_bytes() == (tmp_path / "b" / "lotes" / nome).read_bytes()

    primeiro = {json.loads(l)["order_id"]: json.loads(l) for l in (tmp_path / "a/lotes/lote_0001.jsonl").read_text(encoding="utf-8").splitlines()}
    segundo = [json.loads(l) for l in (tmp_path / "a/lotes/lote_0002.jsonl").read_text(encoding="utf-8").splitlines()]
    reenvios = [p for p in segundo if p["order_id"] in primeiro]
    assert reenvios and all(p != primeiro[p["order_id"]] for p in reenvios)  # reenvio sempre traz alguma mudança
    assert all(p["order_ts"] == primeiro[p["order_id"]]["order_ts"] for p in reenvios)  # mesma data do pedido original


def test_gerar_mais_lotes_nao_altera_os_anteriores(tmp_path):
    # A DAG incremental gera N+1 lotes a cada execução e conta com os N primeiros idênticos (mesmo checksum).
    # Uma versão anterior do gerador quebrava isso a partir do 3º lote (o nº de clientes dependia de `lotes`).
    for total in (2, 3, 5):
        gerar_lotes(total, 300, tmp_path / f"n{total}", seed=42)
    for numero in (1, 2):
        nome = f"lote_{numero:04d}.jsonl"
        referencia = (tmp_path / "n5" / "lotes" / nome).read_bytes()
        assert (tmp_path / "n3" / "lotes" / nome).read_bytes() == referencia, nome
        assert (tmp_path / "n2" / "lotes" / nome).read_bytes() == referencia, nome
    assert (tmp_path / "n3/lotes/lote_0003.jsonl").read_bytes() == (tmp_path / "n5/lotes/lote_0003.jsonl").read_bytes()


def test_controle_cargas_e_definido_igual_no_ddl_e_no_codigo():
    # a tabela nasce do DDL (1ª subida do banco) ou de sql_criar_controle (schema criado pela carga): têm de coincidir
    no_codigo = re.findall(r"(\w+) (?:VARCHAR|CHAR|INTEGER|TIMESTAMPTZ)", sql_criar_controle("dw"))
    assert no_codigo == _colunas_do_ddl("controle_cargas")


def test_schema_e_staging_com_nome_perigoso_sao_recusados():
    with pytest.raises(ValueError, match="Schema inválido"):
        preparar_banco(None, "dw; DROP TABLE x", "stage_ok")
    with pytest.raises(ValueError, match="staging inválido"):
        preparar_banco(None, "dw", "stage-ruim")


def test_silver_lista_pedidos_validos_mesmo_quando_todos_os_itens_foram_rejeitados(spark, tmp_path, produtos_csv):
    produtos, _ = clean_products(read_products(spark, produtos_csv))
    arquivo = _escrever_lote(tmp_path / "l", "lote_0001", [
        _pedido("O1", [_item(qty=0)]),                      # cabeçalho válido, único item inválido
        _pedido("O2", [_item()]),
        _pedido("O3", [_item()], cliente=None),             # cabeçalho inválido: fora de `pedidos`
    ])
    silver = build_silver_from_orders(spark, arquivo, produtos)
    assert {r["order_id"] for r in silver.items.collect()} == {"O2"}
    assert {r["order_id"] for r in silver.pedidos.collect()} == {"O1", "O2"}


# --------------------------------------------------------------------------- #
# Integração (PostgreSQL real)
# --------------------------------------------------------------------------- #
S, ST = "t_dw", "t_stage"


def _consulta(spark, sql: str):
    url, usuario, senha = _conexao()
    return (
        spark.read.format("jdbc").option("url", url).option("query", sql).option("user", usuario)
        .option("password", senha).option("driver", "org.postgresql.Driver").load().collect()
    )


def _fato(spark):
    return [
        (r["pedido_id"], r["item_seq"], r["quantidade"], float(r["valor_liquido"]))
        for r in _consulta(spark, f"SELECT pedido_id, item_seq, quantidade, valor_liquido FROM {S}.fato_vendas ORDER BY 1, 2")
    ]


def _retrato(spark):
    r = _consulta(
        spark,
        f"SELECT count(*) AS n, coalesce(sum(valor_liquido * 100), 0)::bigint AS soma, "
        f"coalesce(md5(string_agg(f::text, ',' ORDER BY pedido_id, item_seq)), '') AS h FROM {S}.fato_vendas f",
    )[0]
    return (r["n"], r["soma"], r["h"])


@pytest.fixture
def banco(spark):
    """Schema isolado e recriado a cada teste, a partir do mesmo DDL do projeto."""
    if not os.getenv("POSTGRES_HOST"):
        pytest.skip("integração: defina POSTGRES_HOST (rode no container com docker compose)")
    _executar_em_transacao(spark, [f"DROP SCHEMA IF EXISTS {S} CASCADE", f"DROP SCHEMA IF EXISTS {ST} CASCADE"])
    criar_modelo(spark, S, DDL)  # o mesmo caminho que a DAG usa para criar o schema do incremental
    yield
    _executar_em_transacao(spark, [f"DROP SCHEMA IF EXISTS {S} CASCADE", f"DROP SCHEMA IF EXISTS {ST} CASCADE"])


def _lote1(pasta):
    return _escrever_lote(pasta, "lote_0001", [
        _pedido("O1", [_item(qty=2, preco=100.0, desc=0.1), _item("SKU00002", 1, 50.0)], cliente="C1"),
        _pedido("O2", [_item(qty=1, preco=100.0)], cliente="C2", cidade="Recife"),
        _pedido("O3", [_item("SKU00002", 2, 50.0)], cliente="C3", cidade="Recife"),
        _pedido("O5", [_item(qty=1, preco=100.0), _item("SKU00002", 1, 50.0)], cliente="C5"),
    ])


def _lote2(pasta):
    return _escrever_lote(pasta, "lote_0002", [
        _pedido("O1", [_item(qty=2, preco=100.0, desc=0.1), _item("SKU00002", 1, 50.0)], status="CANCELADO", cliente="C1"),
        _pedido("O2", [_item(qty=1, preco=100.0)], status="ENVIADO", cliente="C2", cidade="Olinda"),
        _pedido("O3", [_item("SKU00002", 5, 50.0)], cliente="C3", cidade=None),
        _pedido("O5", [_item(qty=1, preco=100.0)], cliente="C5"),
        _pedido("O4", [_item(qty=1, preco=100.0)], cliente="C4", ts="2025-01-02T09:00:00"),
    ])


@pytest.mark.integration
def test_lotes_com_atualizacoes_mesclam_sem_duplicar(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    r1 = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    assert [(r["lote"], r["fato_inseridas"], r["fato_atualizadas"], r["fato_removidas"]) for r in r1] == [("lote_0001", 6, 0, 0)]
    assert len(_fato(spark)) == 6

    _lote2(lotes)
    r2 = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    assert [r["lote"] for r in r2] == ["lote_0002"]  # só o lote novo é processado
    # O4 entra (+1); O3 muda a quantidade (~1); O1 cancelado (-2) e O5 perde um item (-1); O2 só mudou o status (0)
    assert (r2[0]["fato_inseridas"], r2[0]["fato_atualizadas"], r2[0]["fato_removidas"]) == (1, 1, 3)

    assert _fato(spark) == [
        ("O2", 0, 1, 100.0),
        ("O3", 0, 5, 250.0),  # quantidade 2 -> 5
        ("O4", 0, 1, 100.0),
        ("O5", 0, 1, 100.0),  # o segundo item saiu
    ]

    # dimensão com SCD tipo 1: valor novo atualiza; "não informado" não apaga o que já se sabia
    cidades = {r["cliente_id"]: r["cidade"] for r in _consulta(spark, f"SELECT cliente_id, cidade FROM {S}.dim_cliente")}
    assert cidades["C2"] == "Olinda" and cidades["C3"] == "Recife"

    # nada pendente: o controle registra os dois lotes, e rodar de novo não faz nada
    assert run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST) == []
    assert _consulta(spark, f"SELECT count(*) AS n FROM {S}.controle_cargas")[0]["n"] == 2


@pytest.mark.integration
def test_reaplicar_um_lote_e_idempotente_e_arquivo_alterado_volta_a_ser_pendente(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    _lote2(lotes)
    run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    antes = _retrato(spark)

    so_o_ultimo = tmp_path / "so_ultimo"
    so_o_ultimo.mkdir()
    (so_o_ultimo / "lote_0002.jsonl").write_bytes((lotes / "lote_0002.jsonl").read_bytes())
    replay = run_incremental(spark, so_o_ultimo, produtos_csv, schema=S, stage=ST, reprocessar=True)
    assert (replay[0]["fato_inseridas"], replay[0]["fato_atualizadas"], replay[0]["fato_removidas"]) == (0, 0, 0)
    assert _retrato(spark) == antes  # exatamente o mesmo estado, bit a bit

    # mesmo nome, conteúdo diferente (checksum muda): o lote volta a ser pendente e é reaplicado
    _escrever_lote(lotes, "lote_0002", [_pedido("O3", [_item("SKU00002", 9, 50.0)], cliente="C3")])
    pendente = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    assert [r["lote"] for r in pendente] == ["lote_0002"]
    assert ("O3", 0, 9, 450.0) in _fato(spark), (pendente, _fato(spark))


@pytest.mark.integration
def test_falha_no_meio_nao_deixa_o_dw_pela_metade_e_o_lote_continua_pendente(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    antes = _retrato(spark)

    # lote 2 cancela O1 (o DELETE roda primeiro!) e traz um item que viola uma regra do banco no MERGE
    _escrever_lote(lotes, "lote_0002", [
        _pedido("O1", [_item(qty=2, preco=100.0, desc=0.1), _item("SKU00002", 1, 50.0)], status="CANCELADO", cliente="C1"),
        _pedido("O6", [_item(qty=7, preco=100.0)], cliente="C6"),
    ])
    _executar_em_transacao(spark, [f"ALTER TABLE {S}.fato_vendas ADD CONSTRAINT sabotagem CHECK (quantidade <> 7) NOT VALID"])
    # match: o erro tem de vir do MERGE da fato (depois do DELETE), não de um passo anterior
    with pytest.raises(Exception, match="sabotagem"):
        run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)

    assert _retrato(spark) == antes  # o DELETE de O1 foi desfeito junto com o resto
    assert _consulta(spark, f"SELECT count(*) AS n FROM {S}.controle_cargas")[0]["n"] == 1  # lote 2 não foi registrado

    _executar_em_transacao(spark, [f"ALTER TABLE {S}.fato_vendas DROP CONSTRAINT sabotagem"])
    recuperado = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    assert [r["lote"] for r in recuperado] == ["lote_0002"]  # continuou pendente e agora passa
    assert {p for p, *_ in _fato(spark)} == {"O2", "O3", "O5", "O6"}


@pytest.mark.integration
def test_pedido_reenviado_com_todos_os_itens_rejeitados_sai_da_fato(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _escrever_lote(lotes, "lote_0001", [
        _pedido("O1", [_item(), _item("SKU00002", 1, 50.0)]),
        _pedido("O2", [_item()]),
    ])
    run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    assert len(_fato(spark)) == 3

    # a versão nova de O1 só tem um item inválido: nenhuma linha válida, então as antigas têm de sair
    _escrever_lote(lotes, "lote_0002", [_pedido("O1", [_item(qty=0)])])
    relatorio = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)[0]
    assert (relatorio["fato_inseridas"], relatorio["fato_atualizadas"], relatorio["fato_removidas"]) == (0, 0, 2)
    assert {p for p, *_ in _fato(spark)} == {"O2"}


@pytest.mark.integration
def test_pedido_cancelado_que_volta_a_ficar_ativo_e_inserido(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _escrever_lote(lotes, "lote_0001", [_pedido("O1", [_item()], status="CANCELADO")])
    primeiro = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)[0]
    assert primeiro["fato_inseridas"] == 0 and _fato(spark) == []  # cancelado nunca esteve na fato

    _escrever_lote(lotes, "lote_0002", [_pedido("O1", [_item()], status="ENTREGUE")])
    segundo = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)[0]
    assert segundo["fato_inseridas"] == 1 and {p for p, *_ in _fato(spark)} == {"O1"}


@pytest.mark.integration
def test_lote_sem_nenhum_pedido_valido_e_registrado_e_nao_altera_o_dw(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    antes = _retrato(spark)

    (lotes / "lote_0002.jsonl").write_text('{"quebrado": \n{"order_id": "X"\nlixo\n', encoding="utf-8")
    relatorio = run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)[0]
    assert (relatorio["itens_validos"], relatorio["fato_inseridas"], relatorio["fato_removidas"]) == (0, 0, 0)
    assert relatorio["rejeitados"] > 0
    assert _retrato(spark) == antes
    assert _consulta(spark, f"SELECT count(*) AS n FROM {S}.controle_cargas")[0]["n"] == 2


@pytest.mark.integration
def test_duas_cargas_ao_mesmo_tempo_no_mesmo_schema_nao_sao_permitidas(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    with trava_do_schema(spark, S):  # outra carga "em andamento"
        with pytest.raises(RuntimeError, match="já está em execução"):
            run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    # a trava é liberada ao terminar: agora a carga roda
    assert len(run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)) == 1


@pytest.mark.integration
def test_verificacao_antes_do_commit_desfaz_a_transacao_inteira(spark, banco, produtos_csv, tmp_path):
    lotes = tmp_path / "lotes"
    _lote1(lotes)
    run_incremental(spark, lotes, produtos_csv, schema=S, stage=ST)
    antes = _retrato(spark)

    # o DELETE funciona, mas a verificação (valor errado de propósito) falha: nada pode ficar
    with pytest.raises(RuntimeError, match="Verificação antes do commit falhou"):
        _executar_em_transacao(
            spark,
            [f"DELETE FROM {S}.fato_vendas"],
            verificacoes=[(f"SELECT count(*) FROM {S}.fato_vendas", 999)],
        )
    assert _retrato(spark) == antes
