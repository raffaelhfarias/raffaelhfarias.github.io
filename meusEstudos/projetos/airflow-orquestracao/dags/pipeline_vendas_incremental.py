"""DAG da carga incremental: a cada execução, só o lote novo é processado e mesclado no DW.

Diferença para ``pipeline_vendas`` (carga completa):

* A completa reprocessa **tudo** e troca o conteúdo do DW: é um *rebuild*.
* Esta processa **apenas os lotes pendentes** e aplica as mudanças com MERGE: o DW é mantido.

As duas usam schemas diferentes (``dw`` e ``dw_incremental``), porque misturar um rebuild com
uma carga que guarda o que já foi processado deixaria o controle mentindo sobre o conteúdo.
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

log = logging.getLogger(__name__)

DATA = "/opt/airflow/data"
SCHEMA = "dw_incremental"


def alerta_falha(context: dict) -> None:
    ti = context["task_instance"]
    log.error(
        "FALHA na carga incremental: tarefa=%s execução=%s tentativa=%s motivo=%s",
        ti.task_id, context["run_id"], ti.try_number, context.get("exception"),
    )


default_args = {
    "owner": "raffael",
    "retries": 2,  # padrão; só a carga_incremental o aproveita: é atômica e idempotente, então repetir nunca duplica
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": alerta_falha,
}

with DAG(
    dag_id="pipeline_vendas_incremental",
    description="Carga incremental com MERGE: processa só os lotes novos, com controle no banco",
    doc_md=__doc__,
    schedule="0 3 * * *",  # todo dia às 03h, horário de Recife
    start_date=pendulum.datetime(2025, 1, 1, tz="America/Recife"),
    catchup=False,
    max_active_runs=1,  # dois processos mesclando no mesmo DW ao mesmo tempo disputariam as mesmas linhas
    default_args=default_args,
    params={
        "pedidos_por_lote": Param(2000, type="integer", minimum=100, description="Pedidos novos em cada lote diário"),
        "seed": Param(42, type="integer", description="Semente do gerador (mesmo valor = mesma sequência de lotes)"),
    },
    tags=["pyspark", "incremental", "merge", "portfolio"],
) as dag:
    receber_lote = BashOperator(
        task_id="receber_lote",
        # Simula a chegada do lote do dia. O gerador é determinístico: gerar N+1 lotes reproduz os N
        # primeiros byte a byte (o controle por checksum não os vê como novos) e acrescenta o lote N+1.
        # SEM retry: a tarefa não é idempotente. Ela decide o número do próximo lote contando os arquivos
        # que já existem, então repetir depois de uma falha parcial geraria um lote a mais.
        retries=0,
        bash_command=(
            f"mkdir -p {DATA}/raw_inc/lotes && "
            f"n=$(ls {DATA}/raw_inc/lotes/*.jsonl 2>/dev/null | wc -l) && "
            "python -m pipeline.generate_data --lotes $((n + 1)) "
            "--pedidos-por-lote {{ params.pedidos_por_lote }} --seed {{ params.seed }} "
            f"--out {DATA}/raw_inc"
        ),
    )

    carga_incremental = BashOperator(
        task_id="carga_incremental",
        bash_command=(
            "python -m pipeline.incremental "
            f"--lotes {DATA}/raw_inc/lotes --produtos {DATA}/raw_inc/products.csv "
            f"--rejeitados {DATA}/incremental/rejeitados --schema {SCHEMA}"
        ),
    )

    concluir = EmptyOperator(task_id="concluir")

    receber_lote >> carga_incremental >> concluir
