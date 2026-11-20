"""Orquestra a pipeline: raw -> silver -> gold -> qualidade (-> PostgreSQL).

A pipeline tem etapas independentes que trocam dados por Parquet em disco. Isso permite
rodar tudo de uma vez ou etapa por etapa (cada uma em seu próprio processo Spark), que
é como um orquestrador como o Airflow as executa.

Uso:
    python -m pipeline.run_pipeline                          # tudo, só Parquet
    python -m pipeline.run_pipeline --load-postgres          # tudo + carga no DW
    python -m pipeline.run_pipeline --stage silver           # só uma etapa
    (etapas: silver, gold, quality, load, all)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from pyspark.sql import SparkSession

from pipeline.spark_session import get_spark
from pipeline.transform import Silver, build_gold, build_silver, reconcile, validate_star

log = logging.getLogger("pipeline")

GOLD_TABLES = ["dim_data", "dim_cliente", "dim_produto", "dim_pagamento", "dim_canal", "fato_vendas"]
STAGES = ["silver", "gold", "quality", "load", "all"]


def _dirs(out_dir: Path) -> tuple[Path, Path, Path]:
    return out_dir / "silver", out_dir / "gold", out_dir / "rejected"


# --------------------------------------------------------------------------- #
# Etapas
# --------------------------------------------------------------------------- #
def stage_silver(spark: SparkSession, raw_dir: Path, out_dir: Path) -> None:
    """raw -> silver: leitura, limpeza, validação e quarentena."""
    silver_dir, _, rejected_dir = _dirs(out_dir)
    log.info("Silver: leitura, limpeza e validação")
    silver = build_silver(spark, raw_dir)
    silver.items.write.mode("overwrite").parquet(str(silver_dir / "itens_pedido"))
    silver.products.write.mode("overwrite").parquet(str(silver_dir / "produtos"))
    # Reprocessamento completo: "static" apaga partições antigas que não receberam dados
    # nesta execução (com "dynamic" elas sobrariam e entrariam na carga do banco).
    (silver.rejected.write.mode("overwrite").option("partitionOverwriteMode", "static")
        .partitionBy("motivo").parquet(str(rejected_dir)))


def load_silver(spark: SparkSession, out_dir: Path) -> Silver:
    """Relê a silver do disco: as etapas seguintes partem do dado já materializado,
    sem recalcular a cadeia de transformações do raw."""
    silver_dir, _, rejected_dir = _dirs(out_dir)
    return Silver(
        items=spark.read.parquet(str(silver_dir / "itens_pedido")),
        products=spark.read.parquet(str(silver_dir / "produtos")),
        rejected=spark.read.parquet(str(rejected_dir)),
    )


def stage_gold(spark: SparkSession, out_dir: Path) -> None:
    """silver -> gold: modelo dimensional em estrela."""
    _, gold_dir, _ = _dirs(out_dir)
    log.info("Gold: modelo dimensional em estrela")
    gold = build_gold(spark, load_silver(spark, out_dir))
    for nome, df in gold.items():
        escritor = df.write.mode("overwrite")
        if nome == "fato_vendas":
            # poda de partições em consultas por período; "static" pelo mesmo motivo acima
            escritor = escritor.option("partitionOverwriteMode", "static").partitionBy("ano_mes")
        escritor.parquet(str(gold_dir / nome))


def stage_quality(spark: SparkSession, out_dir: Path) -> dict:
    """Confere a gold. Lança RuntimeError se houver qualquer violação (a etapa falha)."""
    silver_dir, gold_dir, _ = _dirs(out_dir)
    log.info("Verificações de qualidade")
    itens = spark.read.parquet(str(silver_dir / "itens_pedido"))
    gold = {n: spark.read.parquet(str(gold_dir / n)) for n in GOLD_TABLES}
    violacoes = validate_star(gold) | reconcile(itens, gold)
    falhas = {k: v for k, v in violacoes.items() if v}
    if falhas:
        raise RuntimeError(f"Qualidade do modelo violada: {falhas}")
    return {"linhas_fato": gold["fato_vendas"].count()}


def stage_load(spark: SparkSession, out_dir: Path) -> dict[str, int]:
    """gold -> PostgreSQL (staging + troca atômica)."""
    from pipeline.load_postgres import load_gold

    _, gold_dir, _ = _dirs(out_dir)
    log.info("Carga no PostgreSQL")
    return load_gold(spark, gold_dir)


def summarize(spark: SparkSession, out_dir: Path) -> dict:
    silver_dir, gold_dir, rejected_dir = _dirs(out_dir)
    return {
        "itens_silver": spark.read.parquet(str(silver_dir / "itens_pedido")).count(),
        "rejeitados": {r["motivo"]: r["count"] for r in
                       spark.read.parquet(str(rejected_dir)).groupBy("motivo").count().collect()},
        "tabelas_gold": {n: spark.read.parquet(str(gold_dir / n)).count() for n in GOLD_TABLES},
    }


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #
def run(raw_dir: Path, out_dir: Path, load_postgres: bool = False, stage: str = "all") -> dict:
    spark = get_spark()
    inicio = time.perf_counter()
    resumo: dict = {}
    try:
        if stage in ("silver", "all"):
            stage_silver(spark, raw_dir, out_dir)
        if stage in ("gold", "all"):
            stage_gold(spark, out_dir)
        if stage in ("quality", "all"):
            resumo.update(stage_quality(spark, out_dir))
        if stage == "all":
            resumo.update(summarize(spark, out_dir))
        if stage == "load" or (stage == "all" and load_postgres):
            resumo["postgres"] = stage_load(spark, out_dir)
    finally:
        spark.stop()
    resumo["segundos"] = round(time.perf_counter() - inicio, 1)
    return resumo


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data"))
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument("--load-postgres", action="store_true", help="com --stage all, também carrega no PostgreSQL")
    args = parser.parse_args()

    resumo = run(args.raw, args.out, args.load_postgres, args.stage)
    log.info("Etapa '%s' concluída em %ss", args.stage, resumo.pop("segundos"))
    for chave, valor in resumo.items():
        log.info("%s: %s", chave, valor)
    return 0


if __name__ == "__main__":
    sys.exit(main())
