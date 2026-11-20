"""Carga atômica da camada gold no SQL Server via JDBC.

Mesma estratégia de ``load_postgres`` (staging + troca em uma única transação), com as
diferenças do SQL Server que obrigam a um código próprio:

* **O T-SQL recusa TRUNCATE em tabela referenciada por FK** (Msg 4712) e **nem aceita listar várias
  tabelas** num TRUNCATE (erro de sintaxe), o que o PostgreSQL permite. A troca usa ``DELETE`` na
  ordem certa: fato primeiro, dimensões depois, e o inverso para inserir.
* O staging nasce de ``SELECT TOP 0 * INTO`` (copia colunas e nulabilidade, sem constraints).
* ``CREATE SCHEMA`` precisa de lote próprio, então cada comando vai em uma execução separada.

Variáveis de ambiente: SQLSERVER_HOST, SQLSERVER_PORT, SQLSERVER_DB, SQLSERVER_USER,
SQLSERVER_PASSWORD.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from pyspark.sql import SparkSession

from pipeline.load_postgres import _executar_em_transacao, consultar_inteiro
from pipeline.modelo import COLUNAS, ORDEM_DE_CARGA

log = logging.getLogger(__name__)

SQLSERVER_DRIVER = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
IDENTIFICADOR = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,40}$")


def conexao_sqlserver() -> tuple[str, str, str, str]:
    """(url, usuário, senha, classe do driver)."""
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    db = os.getenv("SQLSERVER_DB", "dw")
    # encrypt=false + trustServerCertificate: container de estudo com certificado autoassinado.
    url = f"jdbc:sqlserver://{host}:{port};databaseName={db};encrypt=false;trustServerCertificate=true"
    # Senha padrão SÓ PARA ESTUDO LOCAL (container do compose). Em qualquer outro ambiente, defina SQLSERVER_PASSWORD.
    return url, os.getenv("SQLSERVER_USER", "sa"), os.getenv("SQLSERVER_PASSWORD", "Dw_Estudo_2026!"), SQLSERVER_DRIVER


def _validar(nome: str) -> str:
    if not IDENTIFICADOR.match(nome):
        raise ValueError(f"Identificador inválido: {nome!r}")
    return nome


def comandos_de_staging(schema: str, stage: str) -> list[str]:
    """Cria o schema de staging e uma cópia estrutural (sem constraints) de cada tabela do modelo."""
    _validar(schema), _validar(stage)
    comandos = [f"IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{stage}') EXEC('CREATE SCHEMA {stage}')"]
    comandos += [
        f"IF OBJECT_ID('{stage}.{t}', 'U') IS NULL SELECT TOP 0 * INTO {stage}.{t} FROM {schema}.{t}"
        for t in ORDEM_DE_CARGA
    ]
    return comandos


def comandos_de_troca(schema: str, stage: str) -> list[str]:
    """Esvazia o modelo e o repovoa a partir do staging. A ordem é imposta pelas FKs:
    apaga fato → dimensões; insere dimensões → fato."""
    _validar(schema), _validar(stage)
    apagar = [f"DELETE FROM {schema}.{t}" for t in reversed(ORDEM_DE_CARGA)]
    inserir = [
        f"INSERT INTO {schema}.{t} ({', '.join(COLUNAS[t])}) SELECT {', '.join(COLUNAS[t])} FROM {stage}.{t}"
        for t in ORDEM_DE_CARGA
    ]
    return apagar + inserir


def load_gold(spark: SparkSession, gold_dir: str | Path, schema: str = "dw", stage: str = "stage") -> dict[str, int]:
    """Carrega a gold no SQL Server. Devolve as contagens lidas **do banco** após a carga."""
    gold_dir = Path(gold_dir)
    conexao = conexao_sqlserver()
    url, usuario, senha, driver = conexao

    # cada comando em uma execução própria (CREATE SCHEMA/SELECT INTO exigem lotes separados)
    for comando in comandos_de_staging(schema, stage):
        _executar_em_transacao(spark, [comando], conexao_jdbc=conexao)

    esperado: dict[str, int] = {}
    for tabela in ORDEM_DE_CARGA:
        df = spark.read.parquet(str(gold_dir / tabela))
        if tabela == "fato_vendas":
            df = df.repartition(4)
        esperado[tabela] = df.count()
        (
            df.write.format("jdbc")
            .option("url", url)
            .option("dbtable", f"{stage}.{tabela}")
            .option("user", usuario)
            .option("password", senha)
            .option("driver", driver)
            .option("truncate", "true")  # staging não tem FK: o TRUNCATE do SQL Server é permitido aqui
            .option("batchsize", 10_000)
            .mode("overwrite")
            .save()
        )
        log.info("Staging %s.%s carregado (%d linhas)", stage, tabela, esperado[tabela])

    # Troca atômica. Verifica antes do commit que cada tabela ficou com o que o staging trouxe.
    _executar_em_transacao(
        spark,
        comandos_de_troca(schema, stage),
        verificacoes=[(f"SELECT COUNT(*) FROM {schema}.{t}", esperado[t]) for t in ORDEM_DE_CARGA],
        conexao_jdbc=conexao,
    )

    contagens = {t: consultar_inteiro(spark, f"SELECT COUNT(*) AS total FROM {schema}.{t}", conexao) for t in ORDEM_DE_CARGA}
    for tabela, total in contagens.items():
        log.info("%s.%s: %d linhas no banco", schema, tabela, total)
    return contagens
