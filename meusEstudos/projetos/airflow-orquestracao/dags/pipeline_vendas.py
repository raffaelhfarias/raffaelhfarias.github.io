"""DAG que orquestra a pipeline PySpark de vendas (raw -> silver -> gold -> qualidade -> DW).

Cada etapa da pipeline roda como uma tarefa, em um processo próprio, e as etapas trocam
dados por Parquet em disco. Por isso uma etapa que falha pode ser repetida sozinha sem
refazer as anteriores (``Clear`` na UI ou o retry automático).
"""

from __future__ import annotations

import logging
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils.trigger_rule import TriggerRule

log = logging.getLogger(__name__)

DATA = "/opt/airflow/data"
PIPELINE = "python -m pipeline.run_pipeline"


def alerta_falha(context: dict) -> None:
    """Chamada quando uma tarefa esgota os retries.

    Aqui só registra em log. Em produção seria o ponto de enviar uma mensagem (Slack,
    e-mail, WhatsApp) para quem responde pela pipeline.
    """
    ti = context["task_instance"]
    log.error(
        "FALHA na pipeline: dag=%s tarefa=%s execução=%s tentativa=%s motivo=%s",
        ti.dag_id, ti.task_id, context["run_id"], ti.try_number, context.get("exception"),
    )


def escolher_origem(**context) -> str:
    """Decide entre gerar dados novos ou reprocessar os que já estão em disco."""
    return "gerar_dados" if context["params"]["gerar_dados"] else "usar_dados_existentes"


default_args = {
    "owner": "raffael",
    # Falhas transitórias (banco indisponível, disco ocupado) costumam passar sozinhas.
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,  # 1 min, depois ~2 min...
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=30),  # uma etapa travada não prende o worker para sempre
    "on_failure_callback": alerta_falha,
}

with DAG(
    dag_id="pipeline_vendas",
    description="PySpark: JSON de pedidos -> modelo estrela -> PostgreSQL, com quarentena e quality gate",
    doc_md=__doc__,
    schedule="0 2 * * *",  # todo dia às 02h, horário de Recife
    start_date=pendulum.datetime(2025, 1, 1, tz="America/Recife"),
    catchup=False,  # não recupera execuções passadas: a pipeline sempre reprocessa tudo
    max_active_runs=1,  # duas execuções ao mesmo tempo disputariam os mesmos arquivos e o mesmo DW
    default_args=default_args,
    params={
        "gerar_dados": Param(True, type="boolean", description="Gera um novo lote sintético antes de processar"),
        "pedidos": Param(50000, type="integer", minimum=1000, description="Quantidade de pedidos do lote"),
        "seed": Param(42, type="integer", description="Semente do gerador (mesmo valor = mesmo lote)"),
    },
    tags=["pyspark", "estrela", "portfolio"],
) as dag:
    decidir_geracao = BranchPythonOperator(
        task_id="decidir_geracao",
        python_callable=escolher_origem,
    )

    gerar_dados = BashOperator(
        task_id="gerar_dados",
        bash_command=(
            "python -m pipeline.generate_data "
            f"--orders {{{{ params.pedidos }}}} --seed {{{{ params.seed }}}} --out {DATA}/raw"
        ),
    )

    usar_dados_existentes = EmptyOperator(task_id="usar_dados_existentes")

    silver = BashOperator(
        task_id="silver",
        bash_command=f"{PIPELINE} --stage silver --raw {DATA}/raw --out {DATA}",
        # A tarefa anterior da branch que NÃO foi escolhida fica "skipped". Sem esta regra,
        # o padrão (all_success) também pularia a silver.
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    gold = BashOperator(
        task_id="gold",
        bash_command=f"{PIPELINE} --stage gold --out {DATA}",
    )

    qualidade = BashOperator(
        task_id="qualidade",
        bash_command=f"{PIPELINE} --stage quality --out {DATA}",
        # Quality gate: dado inconsistente não melhora repetindo, então não faz retry.
        # Falhar aqui impede que a carga abaixo publique dados ruins no DW.
        retries=0,
    )

    carregar_dw = BashOperator(
        task_id="carregar_dw",
        bash_command=f"{PIPELINE} --stage load --out {DATA}",
        # Retry é seguro: a carga é atômica (staging + troca em uma transação), então uma
        # tentativa que falhou deixa o DW como estava.
    )

    concluir = EmptyOperator(task_id="concluir")

    decidir_geracao >> [gerar_dados, usar_dados_existentes] >> silver >> gold >> qualidade >> carregar_dw >> concluir
