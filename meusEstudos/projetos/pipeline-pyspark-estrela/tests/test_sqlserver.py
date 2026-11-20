"""Testes da carga no SQL Server.

Unitários (sem banco): DDL T-SQL contra a lista de colunas do modelo e comandos da troca.
Integração (``RUN_SQLSERVER_TESTS=1``, precisam do SQL Server no ar): carga real, integridade
referencial, atomicidade e as consultas analíticas em T-SQL, tudo num schema isolado.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

from pipeline.generate_data import gerar
from pipeline.load_postgres import _executar_em_transacao, consultar_inteiro
from pipeline.load_sqlserver import comandos_de_staging, comandos_de_troca, conexao_sqlserver, load_gold
from pipeline.modelo import COLUNAS, ORDEM_DE_CARGA
from pipeline.transform import build_gold, build_silver

RAIZ = Path(__file__).resolve().parents[1] / "sql" / "sqlserver"
DDL = RAIZ / "01_ddl_estrela.sql"
CONSULTAS = RAIZ / "02_consultas_analiticas.sql"


# --------------------------------------------------------------------------- #
# Unitários
# --------------------------------------------------------------------------- #
def _colunas_do_ddl_tsql(tabela: str) -> list[str]:
    texto = DDL.read_text(encoding="utf-8")
    corpo = re.search(rf"CREATE TABLE dw\.{tabela} \((.*?)\n\);", texto, re.S).group(1)
    colunas = []
    for linha in corpo.splitlines():
        palavra = linha.strip().split(" ")[0] if linha.strip() else ""
        if palavra and not palavra.startswith("--") and palavra.upper() not in {"CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK", "FOREIGN"}:
            colunas.append(palavra)
    return colunas


@pytest.mark.parametrize("tabela", ORDEM_DE_CARGA)
def test_colunas_do_ddl_tsql_batem_com_o_modelo(tabela):
    # a carga insere por lista de colunas: se o T-SQL e o modelo divergirem, este teste quebra
    assert _colunas_do_ddl_tsql(tabela) == COLUNAS[tabela]


def test_troca_apaga_a_fato_antes_das_dimensoes_e_insere_dimensoes_antes_da_fato():
    comandos = comandos_de_troca("dw", "stage")
    apagar = [c for c in comandos if c.startswith("DELETE")]
    inserir = [c for c in comandos if c.startswith("INSERT")]
    assert apagar[0] == "DELETE FROM dw.fato_vendas"  # o SQL Server não deixa apagar dimensão referenciada
    assert inserir[-1].startswith("INSERT INTO dw.fato_vendas")
    assert comandos.index(apagar[-1]) < comandos.index(inserir[0])  # tudo apagado antes de qualquer insert


def test_troca_nao_usa_truncate_porque_o_sql_server_nao_permite_com_fk():
    assert not any("TRUNCATE" in c.upper() for c in comandos_de_troca("dw", "stage"))


def test_staging_copia_a_estrutura_sem_constraints_e_so_se_ainda_nao_existe():
    comandos = comandos_de_staging("dw", "stage")
    assert "EXEC('CREATE SCHEMA stage')" in comandos[0]
    assert all("SELECT TOP 0 *" in c and "IF OBJECT_ID" in c for c in comandos[1:])


def test_identificador_invalido_e_recusado():
    with pytest.raises(ValueError, match="Identificador inválido"):
        comandos_de_troca("dw; DROP TABLE x", "stage")


# --------------------------------------------------------------------------- #
# Integração (SQL Server real)
# --------------------------------------------------------------------------- #
S, ST = "dw_teste", "stage_teste"
CONEXAO = None  # preenchido pelo fixture (lê as variáveis de ambiente na hora)


def _consulta_int(spark, sql: str) -> int:
    return consultar_inteiro(spark, sql, conexao_sqlserver())


def _executar(spark, *comandos: str) -> None:
    for comando in comandos:
        _executar_em_transacao(spark, [comando], conexao_jdbc=conexao_sqlserver())


def _linhas_do_primeiro_resultado(spark, sql: str) -> int:
    """Executa um lote T-SQL e conta as linhas do primeiro resultado (erros do servidor sobem como exceção)."""
    url, usuario, senha, driver = conexao_sqlserver()
    jvm = spark._jvm  # noqa: SLF001
    jvm.java.lang.Class.forName(driver)
    conexao = jvm.java.sql.DriverManager.getConnection(url, usuario, senha)
    try:
        instrucao = conexao.createStatement()
        if not instrucao.execute(sql):
            return 0
        resultado = instrucao.getResultSet()
        linhas = 0
        while resultado.next():
            linhas += 1
        return linhas
    finally:
        conexao.close()


@pytest.fixture
def banco(spark):
    if not os.getenv("RUN_SQLSERVER_TESTS"):
        pytest.skip("integração: defina RUN_SQLSERVER_TESTS=1 e suba o SQL Server (docker compose --profile sqlserver up -d)")
    limpar = [f"DROP TABLE IF EXISTS {esquema}.{t}" for esquema in (ST, S) for t in reversed(ORDEM_DE_CARGA)]
    limpar += [f"DROP SCHEMA IF EXISTS {ST}", f"DROP SCHEMA IF EXISTS {S}"]
    _executar(spark, *limpar)
    ddl = re.sub(r"\bdw\b", S, DDL.read_text(encoding="utf-8"))
    _executar(spark, ddl)  # o DDL inteiro é um lote só: roda igual pelo sqlcmd e por JDBC
    yield
    _executar(spark, *limpar)


@pytest.fixture
def gold_em_disco(spark, tmp_path):
    raw, saida = tmp_path / "raw", tmp_path / "gold"
    gerar(orders=2000, out=raw, seed=3)
    gold = build_gold(spark, build_silver(spark, raw))
    for nome, df in gold.items():
        df.write.mode("overwrite").parquet(str(saida / nome))
    return gold, saida


pytestmark_integracao = pytest.mark.skipif(sys.platform == "win32", reason="grava Parquet: roda no container Linux")


@pytest.mark.integration
@pytestmark_integracao
def test_carga_confere_com_a_gold_e_o_banco_impoe_integridade(spark, banco, gold_em_disco):
    gold, saida = gold_em_disco
    contagens = load_gold(spark, saida, schema=S, stage=ST)

    for tabela in ORDEM_DE_CARGA:
        assert contagens[tabela] == gold[tabela].count(), tabela  # lido do banco, comparado ao Spark
    receita_spark = gold["fato_vendas"].agg({"valor_liquido": "sum"}).first()[0]
    receita_banco = _consulta_int(spark, f"SELECT CAST(SUM(valor_liquido) * 100 AS BIGINT) AS v FROM {S}.fato_vendas")
    assert receita_banco == int(round(float(receita_spark) * 100))

    # a FK de verdade é a do banco: uma linha de fato apontando para uma dimensão inexistente é recusada
    with pytest.raises(Exception, match="FOREIGN KEY|foreign key|conflicted"):
        _executar(
            spark,
            f"INSERT INTO {S}.fato_vendas (pedido_id, item_seq, date_key, cliente_key, produto_key, pagamento_key, canal_key, "
            f"quantidade, preco_unitario, desconto_pct, valor_bruto, valor_desconto, valor_liquido, custo_total, margem, ano_mes) "
            f"VALUES ('ORFAO', 0, 20250101, -1, -1, -1, -1, 1, 1, 0, 1, 0, 1, 1, 0, '2025-01')",
        )


@pytest.mark.integration
@pytestmark_integracao
def test_falha_na_troca_preserva_a_carga_anterior(spark, banco, gold_em_disco):
    _, saida = gold_em_disco
    antes = load_gold(spark, saida, schema=S, stage=ST)

    # regra nova que os dados violam, aplicada só a inserções novas: o DELETE da troca roda antes do INSERT que falha
    _executar(spark, f"ALTER TABLE {S}.dim_canal WITH NOCHECK ADD CONSTRAINT sabotagem CHECK (canal <> 'site')")
    # match="sabotagem": o erro tem de vir do INSERT da troca (depois dos DELETEs), não de um passo anterior
    with pytest.raises(Exception, match="sabotagem"):
        load_gold(spark, saida, schema=S, stage=ST)

    depois = {t: _consulta_int(spark, f"SELECT COUNT(*) AS n FROM {S}.{t}") for t in ORDEM_DE_CARGA}
    assert depois == antes  # o DELETE foi desfeito junto: nada ficou pela metade


@pytest.mark.integration
@pytestmark_integracao
def test_consultas_analiticas_em_tsql_executam_e_retornam_dados(spark, banco, gold_em_disco):
    _, saida = gold_em_disco
    load_gold(spark, saida, schema=S, stage=ST)

    texto = re.sub(r"\bdw\.", f"{S}.", CONSULTAS.read_text(encoding="utf-8"))
    blocos = re.split(r"(?m)^-- (?=\d\) )", texto)[1:]
    assert len(blocos) == 6
    linhas = [_linhas_do_primeiro_resultado(spark, "SET NOCOUNT ON;\n-- " + b) for b in blocos]
    # 1 receita mensal, 2 top produtos, 3 curva ABC, 5 ticket médio: sempre trazem linhas.
    # 4 e 6 têm piso de volume/variedade (HAVING) que a amostra de 2 mil pedidos pode não atingir.
    assert linhas[0] > 0 and linhas[1] > 0 and linhas[2] > 0 and linhas[4] == 2
