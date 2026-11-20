"""Carga completa: atomicidade no PostgreSQL e reprocessamento do Parquet.

Integração (precisa de POSTGRES_HOST, roda no container Linux): a carga troca tudo ou nada.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

from pipeline.generate_data import gerar, gerar_lotes
from pipeline.incremental import criar_modelo
from pipeline.load_postgres import _conexao, _executar_em_transacao, consultar_inteiro, load_gold
from pipeline.modelo import ORDEM_DE_CARGA
from pipeline.run_pipeline import stage_gold, stage_silver
from pipeline.transform import build_gold, build_silver

DDL = Path(__file__).resolve().parents[1] / "sql" / "01_ddl_estrela.sql"
S, ST = "t_full", "t_full_stage"

so_linux = pytest.mark.skipif(sys.platform == "win32", reason="grava Parquet: roda no container Linux")


@pytest.fixture
def banco(spark):
    if not os.getenv("POSTGRES_HOST"):
        pytest.skip("integração: defina POSTGRES_HOST (rode no container com docker compose)")
    limpar = [f"DROP SCHEMA IF EXISTS {S} CASCADE", f"DROP SCHEMA IF EXISTS {ST} CASCADE"]
    _executar_em_transacao(spark, limpar)
    criar_modelo(spark, S, DDL)
    yield
    _executar_em_transacao(spark, limpar)


def _contagens(spark):
    return {t: consultar_inteiro(spark, f"SELECT count(*) FROM {S}.{t}") for t in ORDEM_DE_CARGA}


@pytest.mark.integration
@so_linux
def test_carga_completa_confere_com_a_gold_e_uma_falha_na_troca_preserva_a_anterior(spark, banco, tmp_path):
    raw, gold_dir = tmp_path / "raw", tmp_path / "gold"
    gerar(orders=1500, out=raw, seed=4)
    gold = build_gold(spark, build_silver(spark, raw))
    for nome, df in gold.items():
        df.write.mode("overwrite").parquet(str(gold_dir / nome))

    antes = load_gold(spark, gold_dir, schema=S, stage=ST)
    assert antes == {t: gold[t].count() for t in ORDEM_DE_CARGA}  # contagens lidas do banco = as do Spark

    # regra nova que os dados violam, só para inserções novas: o erro acontece no INSERT da troca, depois do TRUNCATE
    _executar_em_transacao(spark, [f"ALTER TABLE {S}.dim_canal ADD CONSTRAINT sabotagem CHECK (canal <> 'site') NOT VALID"])
    with pytest.raises(Exception, match="sabotagem"):
        load_gold(spark, gold_dir, schema=S, stage=ST)
    assert _contagens(spark) == antes  # o TRUNCATE foi desfeito junto: nada ficou pela metade

    _executar_em_transacao(spark, [f"ALTER TABLE {S}.dim_canal DROP CONSTRAINT sabotagem"])
    assert load_gold(spark, gold_dir, schema=S, stage=ST) == antes  # e a carga seguinte passa


def _particoes(pasta: Path) -> set[str]:
    return {p.name for p in pasta.iterdir() if p.name.startswith("ano_mes=")}


@so_linux
def test_reprocessar_nao_deixa_particoes_antigas_do_parquet(spark, tmp_path):
    saida = tmp_path / "out"

    raw1 = tmp_path / "raw1"
    gerar(orders=1500, out=raw1, seed=2)  # pedidos espalhados por 2024-2025
    stage_silver(spark, raw1, saida)
    stage_gold(spark, saida)
    antes = _particoes(saida / "gold" / "fato_vendas")
    assert len(antes) > 3

    raw2 = tmp_path / "raw2"
    gerar_lotes(1, 300, raw2, seed=2)  # só janeiro de 2025
    shutil.copy(raw2 / "lotes" / "lote_0001.jsonl", raw2 / "orders.jsonl")
    stage_silver(spark, raw2, saida)
    stage_gold(spark, saida)

    # com sobrescrita "dynamic" as partições de 2024 sobrariam e entrariam na carga do banco
    assert _particoes(saida / "gold" / "fato_vendas") == {"ano_mes=2025-01"}
