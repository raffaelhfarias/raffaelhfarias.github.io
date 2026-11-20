"""Testes de estrutura da DAG. Não executam o Spark: validam o contrato do orquestrador.

Rodar dentro do container do Airflow:
    docker compose run --rm --no-deps --entrypoint python airflow-scheduler -m pytest /opt/airflow/tests -q
"""

from __future__ import annotations

import pytest
from airflow.models import DagBag
from airflow.utils.trigger_rule import TriggerRule

DAG_ID = "pipeline_vendas"


@pytest.fixture(scope="module")
def dagbag() -> DagBag:
    return DagBag(dag_folder="/opt/airflow/dags", include_examples=False)


@pytest.fixture(scope="module")
def dag(dagbag):
    # dagbag.dags lê direto do arquivo; get_dag() consultaria o banco de metadados,
    # e estes testes de estrutura devem rodar sem nenhum serviço no ar.
    return dagbag.dags[DAG_ID]


def test_dags_importam_sem_erro_nem_ciclo(dagbag):
    # o DagBag registra ciclos e erros de import em import_errors
    assert dagbag.import_errors == {}
    assert DAG_ID in dagbag.dags


def test_tarefas_esperadas(dag):
    assert {t.task_id for t in dag.tasks} == {
        "decidir_geracao", "gerar_dados", "usar_dados_existentes",
        "silver", "gold", "qualidade", "carregar_dw", "concluir",
    }


def test_ordem_das_etapas(dag):
    def depois(task_id):
        return dag.get_task(task_id).downstream_task_ids

    assert depois("decidir_geracao") == {"gerar_dados", "usar_dados_existentes"}
    assert depois("gerar_dados") == {"silver"}
    assert depois("usar_dados_existentes") == {"silver"}
    assert depois("silver") == {"gold"}
    assert depois("gold") == {"qualidade"}
    assert depois("qualidade") == {"carregar_dw"}  # a carga só roda depois do quality gate
    assert depois("carregar_dw") == {"concluir"}


def test_silver_nao_e_pulada_pela_branch(dag):
    # sem esta regra, o ramo não escolhido (skipped) também pularia a silver
    assert dag.get_task("silver").trigger_rule == TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS


def test_politica_de_retry(dag):
    assert dag.default_args["retries"] == 2
    assert dag.default_args["retry_exponential_backoff"] is True
    assert dag.get_task("carregar_dw").retries == 2  # seguro porque a carga é atômica
    assert dag.get_task("qualidade").retries == 0  # dado inconsistente não melhora repetindo


def test_todas_as_tarefas_tem_timeout_e_alerta(dag):
    for tarefa in dag.tasks:
        assert tarefa.execution_timeout is not None, tarefa.task_id
        assert tarefa.on_failure_callback is not None, tarefa.task_id


def test_agendamento_e_concorrencia(dag):
    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert str(dag.timezone) == "America/Recife"
    assert dag.timetable.summary == "0 2 * * *"


def test_parametros_com_padrao_valido(dag):
    assert set(dag.params) == {"gerar_dados", "pedidos", "seed"}
    assert dag.params["pedidos"] >= 1000


@pytest.mark.parametrize("gerar,esperado", [(True, "gerar_dados"), (False, "usar_dados_existentes")])
def test_branch_escolhe_o_ramo_certo(dag, gerar, esperado):
    callable_ = dag.get_task("decidir_geracao").python_callable
    assert callable_(params={"gerar_dados": gerar}) == esperado
    # o ramo escolhido precisa ser realmente filho da tarefa de decisão
    assert esperado in dag.get_task("decidir_geracao").downstream_task_ids


def test_comandos_apontam_para_as_etapas_da_pipeline(dag):
    comandos = {t.task_id: t.bash_command for t in dag.tasks if hasattr(t, "bash_command")}
    assert "--stage silver" in comandos["silver"]
    assert "--stage gold" in comandos["gold"]
    assert "--stage quality" in comandos["qualidade"]
    assert "--stage load" in comandos["carregar_dw"]
    assert "pipeline.generate_data" in comandos["gerar_dados"]
