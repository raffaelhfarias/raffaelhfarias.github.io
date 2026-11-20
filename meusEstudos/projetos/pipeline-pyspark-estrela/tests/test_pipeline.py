import json
from decimal import Decimal

import pytest
from pyspark.sql import SparkSession

from pipeline.generate_data import gerar
from pyspark.sql import functions as F

from pipeline.transform import build_gold, build_silver, reconcile, validate_star


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[2]")
        .appName("testes")
        .config("spark.sql.shuffle.partitions", 2)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.sources.partitionColumnTypeInference.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()


def _pedido(order_id, itens, status="ENTREGUE", cliente="C1", ts="2025-03-10T10:00:00", cidade="Recife"):
    return {
        "order_id": order_id, "order_ts": ts, "status": status, "channel": "Site ",
        "customer": {"id": cliente, "name": "Ana", "city": cidade, "state": "PE", "segment": "varejo"},
        "payment": {"method": "pix", "installments": 1},
        "items": itens,
    }


def _item(sku="SKU00001", qty=2, preco=100.0, desc=0.1):
    return {"sku": sku, "qty": qty, "unit_price": preco, "discount": desc}


def _montar_raw(tmp_path, pedidos, linhas_extras=(), catalogo=None):
    raw = tmp_path / "raw"
    raw.mkdir()
    with (raw / "orders.jsonl").open("w", encoding="utf-8") as f:
        for p in pedidos:
            f.write(json.dumps(p) + "\n")
        for linha in linhas_extras:
            f.write(linha + "\n")
    (raw / "products.csv").write_text(
        catalogo
        or (
            "sku,product_name,category,subcategory,brand,cost\n"
            "SKU00001,Fone,Eletrônicos,Áudio,Aurora,40.00\n"
            "SKU00002,Livro,Livros,Técnicos,Atlas,10.00\n"
        ),
        encoding="utf-8",
    )
    return raw


def _motivos(silver):
    return {r["motivo"]: r["count"] for r in silver.rejected.groupBy("motivo").count().collect()}


def test_regras_de_qualidade_enviam_registros_para_quarentena(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item()]),
        _pedido("O1", [_item()]),  # duplicata exata
        _pedido("O2", [_item(qty=0)]),  # quantidade inválida
        _pedido("O3", [_item(sku="SKU99999")]),  # fora do catálogo
        _pedido("O4", [_item()], cliente=None),  # cliente obrigatório ausente
        _pedido("O5", []),  # pedido sem itens
    ]
    raw = _montar_raw(tmp_path, pedidos, linhas_extras=['{"order_id": "O6", "items": [{"sku"'])
    silver = build_silver(spark, raw)

    assert silver.items.select("order_id").collect()[0]["order_id"] == "O1"
    assert silver.items.count() == 1
    assert _motivos(silver) == {
        "pedido_duplicado": 1,
        "item_invalido": 2,  # qty=0 e pedido sem itens
        "sku_fora_do_catalogo": 1,
        "campo_obrigatorio_ausente": 1,
        "json_malformado": 1,
    }


def test_normaliza_status_e_canal(spark, tmp_path):
    raw = _montar_raw(tmp_path, [_pedido("O1", [_item()], status=" entregue")])
    linha = build_silver(spark, raw).items.collect()[0]
    assert linha["status"] == "ENTREGUE"
    assert linha["channel"] == "site"


def test_fato_calcula_valores_e_exclui_cancelados(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item(qty=2, preco=100.0, desc=0.1)]),
        _pedido("O2", [_item()], status="CANCELADO"),
    ]
    gold = build_gold(spark, build_silver(spark, _montar_raw(tmp_path, pedidos)))
    fato = gold["fato_vendas"].collect()

    assert len(fato) == 1
    linha = fato[0]
    assert linha["valor_bruto"] == Decimal("200.00")
    assert linha["valor_desconto"] == Decimal("20.00")
    assert linha["valor_liquido"] == Decimal("180.00")
    assert linha["custo_total"] == Decimal("80.00")  # 2 x 40.00
    assert linha["margem"] == Decimal("100.00")
    assert linha["ano_mes"] == "2025-03"
    assert linha["date_key"] == 20250310


def test_dim_cliente_usa_ultimo_valor_nao_nulo(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item()], ts="2025-01-01T08:00:00", cidade="Recife"),
        _pedido("O2", [_item()], ts="2025-02-01T08:00:00", cidade=None),
    ]
    gold = build_gold(spark, build_silver(spark, _montar_raw(tmp_path, pedidos)))
    clientes = gold["dim_cliente"].collect()
    assert len(clientes) == 1
    assert clientes[0]["cidade"] == "Recife"  # o nulo mais novo não apaga o valor conhecido


def test_dim_data_nao_tem_lacunas(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item()], ts="2025-03-01T08:00:00"),
        _pedido("O2", [_item()], ts="2025-03-10T08:00:00"),
    ]
    gold = build_gold(spark, build_silver(spark, _montar_raw(tmp_path, pedidos)))
    datas = gold["dim_data"]
    assert datas.count() == 10
    sabado = datas.where("date_key = 20250301").collect()[0]
    assert sabado["dia_semana"] == "Sábado" and sabado["fim_de_semana"] is True
    assert sabado["nome_mes"] == "Março"


def test_pipeline_ponta_a_ponta_com_dados_gerados(spark, tmp_path):
    raw = tmp_path / "raw"
    gerar(orders=3000, out=raw, seed=7)
    silver = build_silver(spark, raw)
    gold = build_gold(spark, silver)

    violacoes = validate_star(gold)
    assert all(v == 0 for v in violacoes.values()), violacoes

    nao_cancelados = silver.items.where("status != 'CANCELADO'").count()
    assert gold["fato_vendas"].count() == nao_cancelados
    # o gerador injeta problemas: a quarentena precisa ter capturado ao menos alguns
    assert silver.rejected.count() > 0


# --- Regressões dos bugs apontados na revisão ------------------------------------------------ #
def test_status_nulo_ou_fora_do_dominio_vai_para_quarentena_e_nao_some(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item()]),
        _pedido("O2", [_item()], status=None),
        _pedido("O3", [_item()], status="DEVOLVIDO"),
    ]
    silver = build_silver(spark, _montar_raw(tmp_path, pedidos))
    assert [r["order_id"] for r in silver.items.collect()] == ["O1"]
    assert _motivos(silver) == {"status_invalido": 2}


def test_desconto_fora_da_faixa_e_rejeitado_em_vez_de_virar_nulo_ou_receita_negativa(spark, tmp_path):
    pedidos = [
        _pedido("O1", [_item(desc=0.1)]),
        _pedido("O2", [_item(desc=1.5)]),   # maior que 100%
        _pedido("O3", [_item(desc=-0.2)]),  # negativo
        _pedido("O4", [_item(desc=123456.0)]),  # estouraria decimal(5,4)
    ]
    silver = build_silver(spark, _montar_raw(tmp_path, pedidos))
    assert [r["order_id"] for r in silver.items.collect()] == ["O1"]
    assert _motivos(silver) == {"desconto_fora_da_faixa": 3}
    fato = build_gold(spark, silver)["fato_vendas"]
    assert fato.where("valor_liquido < 0 OR desconto_pct IS NULL").count() == 0


def test_catalogo_com_sku_duplicado_ou_custo_invalido_vai_para_quarentena(spark, tmp_path):
    catalogo = (
        "sku,product_name,category,subcategory,brand,cost\n"
        "SKU00001,Fone,Eletrônicos,Áudio,Aurora,40.00\n"
        "SKU00001,Fone duplicado,Eletrônicos,Áudio,Aurora,45.00\n"  # duplicado: ambíguo
        "SKU00002,Livro,Livros,Técnicos,Atlas,\n"  # custo ausente
        "SKU00003,Bolsa,Moda,Bolsas,Prisma,25.00\n"
    )
    pedidos = [_pedido("O1", [_item(sku="SKU00001")]), _pedido("O2", [_item(sku="SKU00003")])]
    silver = build_silver(spark, _montar_raw(tmp_path, pedidos, catalogo=catalogo))

    assert [r["sku"] for r in silver.products.collect()] == ["SKU00003"]
    motivos = _motivos(silver)
    assert motivos["sku_duplicado_no_catalogo"] == 2
    assert motivos["produto_invalido"] == 1
    assert motivos["sku_fora_do_catalogo"] == 1  # o item de SKU00001 não tem catálogo confiável
    # e a fato não multiplica linhas por causa do duplicado
    assert build_gold(spark, silver)["fato_vendas"].count() == 1


def test_dedupe_com_mesmo_timestamp_escolhe_sempre_o_mesmo_vencedor(spark, tmp_path):
    def vencedor(subdir):
        pedidos = [
            _pedido("O1", [_item()], cidade="Recife"),
            _pedido("O1", [_item()], cidade="Olinda"),  # mesmo order_id e mesmo order_ts
        ]
        pasta = tmp_path / subdir
        pasta.mkdir()
        silver = build_silver(spark, _montar_raw(pasta, pedidos))
        return silver.items.collect()[0]["customer_city"]

    resultados = {vencedor(f"rodada{i}") for i in range(3)}
    assert len(resultados) == 1


def _gold_pequeno(spark, tmp_path):
    pedidos = [_pedido(f"O{i}", [_item(), _item(sku="SKU00002")], cliente=f"C{i}") for i in range(1, 4)]
    silver = build_silver(spark, _montar_raw(tmp_path, pedidos))
    return silver, build_gold(spark, silver)


def test_validate_star_detecta_erros_de_verdade(spark, tmp_path):
    _, gold = _gold_pequeno(spark, tmp_path)
    assert all(v == 0 for v in validate_star(gold).values())  # modelo íntegro

    sem_cliente = {**gold, "dim_cliente": gold["dim_cliente"].limit(1)}
    assert validate_star(sem_cliente)["orfaos_cliente_key"] > 0  # fato aponta para dimensão ausente

    fato_duplicada = {**gold, "fato_vendas": gold["fato_vendas"].unionByName(gold["fato_vendas"].limit(1))}
    assert validate_star(fato_duplicada)["grao_duplicado"] > 0

    dim_duplicada = {**gold, "dim_canal": gold["dim_canal"].unionByName(gold["dim_canal"])}
    assert validate_star(dim_duplicada)["chave_duplicada_dim_canal"] > 0


def test_reconcile_detecta_perda_de_linhas_e_erro_de_valor(spark, tmp_path):
    silver, gold = _gold_pequeno(spark, tmp_path)
    assert all(v == 0 for v in reconcile(silver.items, gold).values())

    perdeu_linha = {**gold, "fato_vendas": gold["fato_vendas"].limit(gold["fato_vendas"].count() - 1)}
    assert reconcile(silver.items, perdeu_linha)["divergencia_linhas"] == 1

    valor_errado = {**gold, "fato_vendas": gold["fato_vendas"].withColumn("valor_liquido", F.col("valor_liquido") * 2)}
    assert reconcile(silver.items, valor_errado)["divergencia_valor"] == 1

    sem_dias = {**gold, "dim_data": gold["dim_data"].limit(0)}
    assert reconcile(silver.items, sem_dias)["divergencia_dias"] > 0
