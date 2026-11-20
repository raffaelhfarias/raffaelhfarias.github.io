"""Orquestra a pipeline: raw -> silver -> gold (-> PostgreSQL).

Uso:
    python -m pipeline.run_pipeline                    # só parquet
    python -m pipeline.run_pipeline --load-postgres    # parquet + carga no DW
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from pipeline.spark_session import get_spark
from pipeline.transform import build_gold, build_silver, reconcile, validate_star

log = logging.getLogger("pipeline")


def run(raw_dir: Path, out_dir: Path, load_postgres: bool = False) -> dict:
    spark = get_spark()
    inicio = time.perf_counter()
    silver_dir, gold_dir, rejected_dir = out_dir / "silver", out_dir / "gold", out_dir / "rejected"

    log.info("[1/4] Silver: leitura, limpeza e validação")
    silver = build_silver(spark, raw_dir)
    silver.items.write.mode("overwrite").parquet(str(silver_dir / "itens_pedido"))
    # Reprocessamento completo: "static" apaga partições antigas que não receberam dados
    # nesta execução (com "dynamic" elas sobrariam e entrariam na carga do banco).
    (silver.rejected.write.mode("overwrite").option("partitionOverwriteMode", "static")
        .partitionBy("motivo").parquet(str(rejected_dir)))

    # Relê do disco: as etapas seguintes partem do dado já materializado,
    # sem recalcular a cadeia de transformações do raw.
    itens = spark.read.parquet(str(silver_dir / "itens_pedido"))
    silver.items = itens

    log.info("[2/4] Gold: modelo dimensional em estrela")
    gold = build_gold(spark, silver)
    for nome, df in gold.items():
        escritor = df.write.mode("overwrite")
        if nome == "fato_vendas":
            # poda de partições em consultas por período; "static" pelo mesmo motivo acima
            escritor = escritor.option("partitionOverwriteMode", "static").partitionBy("ano_mes")
        escritor.parquet(str(gold_dir / nome))

    log.info("[3/4] Verificações de qualidade")
    gold_lido = {n: spark.read.parquet(str(gold_dir / n)) for n in gold}
    violacoes = validate_star(gold_lido) | reconcile(itens, gold_lido)
    falhas = {k: v for k, v in violacoes.items() if v}
    if falhas:
        raise RuntimeError(f"Qualidade do modelo violada: {falhas}")
    linhas_fato = gold_lido["fato_vendas"].count()

    resumo = {
        "itens_silver": itens.count(),
        "linhas_fato": linhas_fato,
        "rejeitados": {r["motivo"]: r["count"] for r in
                       spark.read.parquet(str(rejected_dir)).groupBy("motivo").count().collect()},
        "tabelas_gold": {n: df.count() for n, df in gold_lido.items()},
    }

    if load_postgres:
        from pipeline.load_postgres import load_gold

        log.info("[4/4] Carga no PostgreSQL")
        resumo["postgres"] = load_gold(spark, gold_dir)

    resumo["segundos"] = round(time.perf_counter() - inicio, 1)
    spark.stop()
    return resumo


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data"))
    parser.add_argument("--load-postgres", action="store_true")
    args = parser.parse_args()

    resumo = run(args.raw, args.out, args.load_postgres)
    log.info("Concluído em %ss", resumo.pop("segundos"))
    for chave, valor in resumo.items():
        log.info("%s: %s", chave, valor)
    return 0


if __name__ == "__main__":
    sys.exit(main())
