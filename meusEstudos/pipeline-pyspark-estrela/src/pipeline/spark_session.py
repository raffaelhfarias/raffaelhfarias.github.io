"""Criação da SparkSession com configurações explícitas e justificadas."""

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import SparkSession

JDBC_JAR = Path(os.getenv("PG_JDBC_JAR", "/opt/jars/postgresql.jar"))


def get_spark(app_name: str = "pipeline-estrela", shuffle_partitions: int | None = None) -> SparkSession:
    # O padrão do Spark é 200 partições de shuffle, excessivo para um volume
    # pequeno em uma única máquina: gera 200 tarefas minúsculas. Ajustável por env.
    partitions = shuffle_partitions or int(os.getenv("SHUFFLE_PARTITIONS", "16"))

    builder = (
        SparkSession.builder.master(os.getenv("SPARK_MASTER", "local[*]"))
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", partitions)
        # Sobrescreve só as partições que recebem dados novos (reprocessamento idempotente).
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        # "2024-01" deve continuar sendo texto, não ser inferido como data.
        .config("spark.sql.sources.partitionColumnTypeInference.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
    )
    if JDBC_JAR.exists():
        builder = builder.config("spark.jars", str(JDBC_JAR))

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
