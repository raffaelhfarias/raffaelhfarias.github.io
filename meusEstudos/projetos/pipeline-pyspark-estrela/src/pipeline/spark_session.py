"""Criação da SparkSession com configurações explícitas e justificadas."""

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import SparkSession

# Drivers JDBC (PostgreSQL, SQL Server...) ficam em uma pasta; todos os .jar dela entram na sessão.
JDBC_DIR = Path(os.getenv("JDBC_JARS_DIR", "/opt/jars"))


def get_spark(
    app_name: str = "pipeline-estrela", shuffle_partitions: int | None = None, ui: bool = True
) -> SparkSession:
    # O padrão do Spark é 200 partições de shuffle, excessivo para um volume
    # pequeno em uma única máquina: gera 200 tarefas minúsculas. Ajustável por env.
    partitions = shuffle_partitions or int(os.getenv("SHUFFLE_PARTITIONS", "16"))

    builder = (
        SparkSession.builder.master(os.getenv("SPARK_MASTER", "local[*]"))
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", partitions)
        # "2024-01" deve continuar sendo texto, não ser inferido como data.
        .config("spark.sql.sources.partitionColumnTypeInference.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.ui.enabled", str(ui).lower())
    )
    jars = sorted(str(j) for j in JDBC_DIR.glob("*.jar")) if JDBC_DIR.is_dir() else []
    if jars:
        # extraClassPath coloca os drivers no classpath do sistema, o que o DriverManager do JDBC
        # exige para as transações abertas direto pela JVM (ver load_postgres.py).
        builder = builder.config("spark.jars", ",".join(jars)).config("spark.driver.extraClassPath", os.pathsep.join(jars))

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
