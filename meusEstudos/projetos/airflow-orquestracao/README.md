# Orquestração com Apache Airflow

DAG de **Apache Airflow 2.10** que orquestra a [pipeline PySpark + modelo estrela](../pipeline-pyspark-estrela): gera um lote de pedidos, processa raw → silver → gold, aplica um **quality gate** e carrega o resultado no PostgreSQL. Tudo roda em Docker, com `LocalExecutor` e banco de metadados em PostgreSQL.

Este projeto não duplica código: o Airflow monta `../pipeline-pyspark-estrela/src` e executa as etapas da pipeline como tarefas.

```
decidir_geracao ─┬─▶ gerar_dados ──────────┐
 (branch)        └─▶ usar_dados_existentes ┴─▶ silver ─▶ gold ─▶ qualidade ─▶ carregar_dw ─▶ concluir
```

## O que a DAG demonstra

| Conceito | Onde está na DAG | Por quê |
|---|---|---|
| **Dependências** | `a >> b >> c` | A ordem entre etapas é explícita e visível no grafo da UI |
| **Agendamento** | `schedule="0 2 * * *"`, fuso `America/Recife`, `catchup=False` | Roda todo dia às 02h. Sem `catchup`, ligar a DAG não dispara execuções passadas, que seriam reprocessamentos iguais |
| **Retry com backoff** | `retries=2`, `retry_exponential_backoff` | Falha transitória (banco ocupado) passa sozinha, sem alertar ninguém |
| **Quality gate sem retry** | `qualidade` com `retries=0` | Dado inconsistente não melhora repetindo. Falhar aqui **impede** a carga de publicar dado ruim |
| **Retry seguro** | `carregar_dw` | A carga é atômica (staging + troca em uma transação): uma tentativa que falha deixa o DW como estava |
| **Branch** | `decidir_geracao` | Gera lote novo ou reprocessa o que já existe, conforme o parâmetro `gerar_dados` |
| **Trigger rule** | `silver` com `none_failed_min_one_success` | O ramo não escolhido da branch fica `skipped`; sem essa regra a silver também seria pulada |
| **Timeout e alerta** | `execution_timeout`, `on_failure_callback` | Etapa travada não prende o worker, e falha definitiva dispara o alerta (aqui só log) |
| **Concorrência** | `max_active_runs=1` | Duas execuções simultâneas disputariam os mesmos arquivos e o mesmo DW |
| **Parâmetros** | `params`: `gerar_dados`, `pedidos`, `seed` | Escolhidos no botão "Trigger DAG w/ config", com validação de tipo |

## Do Kestra para o Airflow

Quem já orquestra em produção com Kestra conhece a maior parte destes conceitos, só com outros nomes:

| Kestra | Airflow | Observação |
|---|---|---|
| Flow (YAML) | DAG (Python) | Kestra descreve em YAML; Airflow descreve em código Python |
| Task | Operator / Task | `BashOperator` ≈ `scripts.python.Commands` |
| `triggers: Schedule` (cron) | `schedule="0 2 * * *"` | Ambos aceitam cron e fuso horário |
| `triggers: Webhook` | `airflow dags trigger` / API REST | Em Airflow o gatilho por evento é mais indireto (sensors, API, datasets) |
| `concurrency: limit: 1` | `max_active_runs=1` | Mesma ideia: uma execução por vez |
| `retry:` | `retries`, `retry_delay` | Backoff exponencial nos dois |
| `errors:` (bloco de erro) | `on_failure_callback` | Ação ao falhar |
| `If` / `Switch` | `BranchPythonOperator` | Decisão em tempo de execução |
| `inputs:` | `params:` | Parâmetros da execução, com tipo |
| KV Store | Variables / XCom | Variables = config durável; XCom = dado entre tarefas |
| `kv('SEGREDO')` | Connections / secrets backend | Credenciais fora do código |
| `SyncNamespaceFiles` (Git) | volume de `dags/` (ou git-sync) | Como o código chega ao orquestrador |
| `Subflow` | `TriggerDagRunOperator` / TaskGroup | Composição de fluxos |

**Diferença de filosofia:** o Kestra descreve o fluxo de forma declarativa e roda cada tarefa em um container isolado por padrão. O Airflow descreve o fluxo em Python (mais flexível, mais verboso) e, aqui, executa as tarefas no próprio container do worker. Para isolar de verdade em produção usa-se `DockerOperator`, `KubernetesPodOperator` ou o `CeleryExecutor`/`KubernetesExecutor`.

## Como rodar

Pré-requisito: Docker Desktop. Dentro desta pasta:

```powershell
# 1) Constrói a imagem e sobe o Airflow, o banco de metadados e o data warehouse
docker compose up -d --build

# 2) Abre a interface em http://localhost:8080  (usuário: admin / senha: admin)
#    Ative a DAG "pipeline_vendas" e use "Trigger DAG w/ config" para escolher os parâmetros.
#    Ou pela linha de comando (no PowerShell o JSON precisa passar por um bash dentro do container):
docker compose exec airflow-scheduler airflow dags unpause pipeline_vendas
$cmd = "airflow dags trigger pipeline_vendas --conf '{`"pedidos`": 20000}'"
docker compose exec airflow-scheduler bash -c $cmd

# 3) Confere o resultado no data warehouse (porta 5433 no host)
docker compose exec dw psql -U dw -d dw -c "SELECT count(*) FROM dw.fato_vendas"

# Testes da DAG (estrutura, retries, ordem das tarefas, branch)
docker compose run --rm --no-deps --entrypoint python airflow-scheduler -m pytest /opt/airflow/tests -q

# Desliga (os dados ficam nos volumes; use `down -v` para apagar tudo)
docker compose down
```

> Credenciais (`admin/admin`, `dw/dw`) e a ausência de Fernet key são só para estudo local: todas as portas ficam publicadas apenas em `127.0.0.1`.

> **Ao ativar a DAG pela primeira vez**, o Airflow dispara sozinho uma execução do último intervalo agendado (com os parâmetros padrão, 50 mil pedidos): é o efeito de `catchup=False`, que cria só a execução mais recente. Como `max_active_runs=1`, uma execução manual disparada logo em seguida espera na fila até a agendada terminar.

## Estado de verificação

Executado de ponta a ponta com Docker (Docker Desktop no Windows, containers Linux):

- **Execução completa:** `gerar_dados` → `silver` → `gold` → `qualidade` → `carregar_dw` com sucesso. Com 20 mil pedidos: ~3 min no total (gerar ~2 s, silver ~32 s, gold ~58 s, qualidade ~55 s, carga ~28 s). O DW recebeu 31.274 linhas na fato e 2.000 clientes.
- **Branch e trigger rule:** com `gerar_dados=false`, `usar_dados_existentes` foi executada, `gerar_dados` ficou `skipped` e a `silver` rodou normalmente.
- **Retry com recuperação:** derrubei o DW de propósito. `carregar_dw` falhou (`UnknownHostException: dw`), entrou em `up_for_retry`, e na segunda tentativa, com o banco de volta, concluiu a execução. O DW terminou com as mesmas 31.274 linhas, então a tentativa que falhou não deixou lixo.
- **`max_active_runs=1`:** observado na prática (ver o aviso acima): a execução manual esperou a agendada terminar.
- **Testes da DAG (11):** passam em ~5 s e não precisam de nenhum serviço no ar (estrutura, ordem, retries, timeout, branch, agendamento).
- **Testes da pipeline por etapas:** 14 passam no container, incluindo um que prova que rodar silver → gold → qualidade em etapas separadas dá o mesmo resultado que o fluxo em memória.

**Não verificado:**

- O **quality gate bloqueando a carga** dentro do Airflow não foi disparado de ponta a ponta. A etapa que falha é testada na pipeline (a `stage_quality` lança erro com a gold corrompida) e a DAG tem a ordem `qualidade >> carregar_dw` verificada por teste de estrutura, mas eu não forcei essa falha rodando a DAG.
- O **alerta de falha definitiva** (`on_failure_callback`) só registra em log e não foi exercitado até esgotar os retries.

## Limitações

- **`LocalExecutor`:** as tarefas rodam como subprocessos do mesmo container, sem isolamento. Em produção, `DockerOperator`/`KubernetesPodOperator` ou `CeleryExecutor`/`KubernetesExecutor`.
- **Spark em `local[*]`:** não há cluster. O Airflow orquestra a execução, mas o processamento continua numa máquina só.
- **Dados em disco local compartilhado:** as etapas trocam Parquet por um volume. Em produção seria armazenamento de objetos ou HDFS.
- **Airflow 2.10:** a versão 3.x mudou a arquitetura (API server separado, SDK de tarefas, novo conceito de assets). Os conceitos desta DAG se mantêm, mas a configuração e alguns imports mudam.
- **Credenciais fixas no `compose.yaml`** (estudo local). Em produção vão para um *secrets backend*, e a Fernet key precisa ser definida.
- **Sem sensores nem datasets:** a DAG é disparada por agenda ou manualmente, não por chegada de dados.
