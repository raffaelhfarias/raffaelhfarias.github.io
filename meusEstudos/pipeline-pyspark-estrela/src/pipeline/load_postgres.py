"""Carga da camada gold no PostgreSQL via JDBC.

As tabelas e constraints são criadas por ``sql/01_ddl_estrela.sql`` (o schema
é responsabilidade do banco, não do Spark). Aqui só carregamos os dados:
``truncate=true`` esvazia a tabela em vez de recriá-la, preservando PKs/FKs.
A ordem importa: dimensões antes da fato.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from pyspark.sql import SparkSession

log = logging.getLogger(__name__)

ORDEM_DE_CARGA = ["dim_data", "dim_cliente", "dim_produto", "dim_pagamento", "dim_canal", "fato_vendas"]


def jdbc_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "dw")
    return f"jdbc:postgresql://{host}:{port}/{db}"


def load_gold(spark: SparkSession, gold_dir: str | Path, schema: str = "dw") -> dict[str, int]:
    gold_dir = Path(gold_dir)
    contagens: dict[str, int] = {}
    for tabela in ORDEM_DE_CARGA:
        df = spark.read.parquet(str(gold_dir / tabela))
        if tabela == "fato_vendas":
            # reparticiona para paralelizar as conexões JDBC sem abrir dezenas delas
            df = df.repartition(4)
        (
            df.write.format("jdbc")
            .option("url", jdbc_url())
            .option("dbtable", f"{schema}.{tabela}")
            .option("user", os.getenv("POSTGRES_USER", "dw"))
            .option("password", os.getenv("POSTGRES_PASSWORD", "dw"))
            .option("driver", "org.postgresql.Driver")
            .option("truncate", "true")
            # Sem CASCADE o Postgres recusa esvaziar uma dimensão referenciada pela fato.
            # Seguro aqui: a fato é a última a ser carregada e é recarregada por inteiro.
            .option("cascadeTruncate", "true")
            .option("batchsize", 10_000)
            .mode("overwrite")
            .save()
        )
        contagens[tabela] = df.count()
        log.info("Carregado %s.%s (%d linhas)", schema, tabela, contagens[tabela])
    return contagens
