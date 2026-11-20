"""Carga atômica da camada gold no PostgreSQL via JDBC.

O schema e as constraints são criados por ``sql/01_ddl_estrela.sql`` (o schema é
responsabilidade do banco, não do Spark). A carga acontece em duas fases:

1. **Staging:** o Spark grava cada tabela em ``stage.<tabela>`` (cópias sem PK/FK).
   Se qualquer dado violar um NOT NULL ou o job falhar aqui, o schema ``dw`` não
   foi tocado e continua com a carga anterior.
2. **Swap:** uma única transação esvazia as tabelas de ``dw`` e as repovoa a partir
   do staging. O PostgreSQL desfaz tudo se algo falhar no meio, e quem consulta
   ``dw`` nunca vê dimensões novas com a fato antiga (nem a fato vazia).

O Spark escreve cada tabela em uma transação própria, por isso o staging: o JDBC
do Spark não tem como abrir uma transação única englobando várias escritas.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from pyspark.sql import SparkSession

log = logging.getLogger(__name__)

# Dimensões antes da fato (a fato referencia as dimensões).
ORDEM_DE_CARGA = ["dim_data", "dim_cliente", "dim_produto", "dim_pagamento", "dim_canal", "fato_vendas"]


def _conexao() -> tuple[str, str, str]:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "dw")
    return (
        f"jdbc:postgresql://{host}:{port}/{db}",
        os.getenv("POSTGRES_USER", "dw"),
        os.getenv("POSTGRES_PASSWORD", "dw"),
    )


def jdbc_url() -> str:
    return _conexao()[0]


def _executar_em_transacao(spark: SparkSession, comandos: list[str]) -> None:
    """Executa os comandos numa única transação (tudo ou nada) usando o driver JDBC do Spark."""
    url, usuario, senha = _conexao()
    jvm = spark._jvm  # noqa: SLF001 - py4j é o único caminho para uma transação multi-comando
    jvm.java.lang.Class.forName("org.postgresql.Driver")
    conexao = jvm.java.sql.DriverManager.getConnection(url, usuario, senha)
    try:
        conexao.setAutoCommit(False)
        instrucao = conexao.createStatement()
        for comando in comandos:
            instrucao.execute(comando)
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def _contar_no_banco(spark: SparkSession, tabela: str) -> int:
    url, usuario, senha = _conexao()
    linha = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("query", f"SELECT count(*) AS total FROM {tabela}")
        .option("user", usuario)
        .option("password", senha)
        .option("driver", "org.postgresql.Driver")
        .load()
        .first()
    )
    return int(linha["total"])


def load_gold(spark: SparkSession, gold_dir: str | Path, schema: str = "dw", stage: str = "stage") -> dict[str, int]:
    """Carrega a gold no banco. Devolve as contagens lidas **do PostgreSQL** após a carga."""
    gold_dir = Path(gold_dir)
    url, usuario, senha = _conexao()

    # Staging com a mesma estrutura de dw (colunas e NOT NULL), sem PK/FK.
    _executar_em_transacao(
        spark,
        [f"CREATE SCHEMA IF NOT EXISTS {stage}"]
        + [f"CREATE TABLE IF NOT EXISTS {stage}.{t} (LIKE {schema}.{t} INCLUDING DEFAULTS)" for t in ORDEM_DE_CARGA],
    )

    for tabela in ORDEM_DE_CARGA:
        df = spark.read.parquet(str(gold_dir / tabela))
        if tabela == "fato_vendas":
            df = df.repartition(4)  # paraleliza as conexões JDBC sem abrir dezenas delas
        (
            df.write.format("jdbc")
            .option("url", url)
            .option("dbtable", f"{stage}.{tabela}")
            .option("user", usuario)
            .option("password", senha)
            .option("driver", "org.postgresql.Driver")
            .option("truncate", "true")  # staging não tem FK: truncar é seguro
            .option("batchsize", 10_000)
            .mode("overwrite")
            .save()
        )
        log.info("Staging %s.%s carregado", stage, tabela)

    # Swap atômico. Um único TRUNCATE com todas as tabelas é permitido mesmo com FKs entre elas.
    _executar_em_transacao(
        spark,
        [f"TRUNCATE TABLE {', '.join(f'{schema}.{t}' for t in ORDEM_DE_CARGA)}"]
        + [f"INSERT INTO {schema}.{t} SELECT * FROM {stage}.{t}" for t in ORDEM_DE_CARGA],
    )

    contagens = {t: _contar_no_banco(spark, f"{schema}.{t}") for t in ORDEM_DE_CARGA}
    for tabela, total in contagens.items():
        log.info("%s.%s: %d linhas no banco", schema, tabela, total)
    return contagens
