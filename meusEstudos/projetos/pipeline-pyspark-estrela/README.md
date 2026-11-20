# Pipeline PySpark + modelo estrela

Pipeline de ETL em **PySpark** que ingere pedidos semiestruturados (JSON aninhado), aplica regras de qualidade com quarentena, constrói um **modelo dimensional em estrela** em Parquet e carrega o resultado em **PostgreSQL**, tudo reproduzível com Docker.

Os dados são **sintéticos** (gerador determinístico incluído), com volume ajustável e problemas injetados de propósito: duplicatas, JSON truncado, itens inválidos, SKU fora do catálogo.

```
 raw (JSON + CSV)        silver (Parquet)            gold (Parquet, estrela)         PostgreSQL
┌──────────────────┐   ┌─────────────────────┐    ┌───────────────────────────┐   ┌───────────────┐
│ orders.jsonl     │──▶│ itens_pedido        │───▶│ dim_data  dim_cliente     │──▶│ schema dw     │
│ products.csv     │   │ (limpo, tipado,     │    │ dim_produto dim_pagamento │   │ PK/FK/índices │
└──────────────────┘   │  sem duplicatas)    │    │ dim_canal                 │   │ + consultas   │
                       │ rejected/ (quarentena)│  │ fato_vendas (part. ano_mes)│   │   analíticas  │
                       └─────────────────────┘    └───────────────────────────┘   └───────────────┘
```

## O que o projeto demonstra

| Tema | Onde |
|---|---|
| PySpark: schema explícito, `posexplode`, window functions, joins `left_semi`/`left_anti`, partições | [`src/pipeline/transform.py`](src/pipeline/transform.py) |
| Dados semiestruturados: JSON aninhado com array de structs, modo `PERMISSIVE` e `_corrupt_record` | [`schemas.py`](src/pipeline/schemas.py), `read_orders` / `split_corrupt` |
| Modelagem dimensional: grão, dimensões, medidas aditivas, SCD1, chaves substitutas | [`docs/modelo-estrela.md`](docs/modelo-estrela.md) |
| Qualidade de dados: quarentena por motivo, integridade referencial, reconciliação | `validate_star`, [`run_pipeline.py`](src/pipeline/run_pipeline.py) |
| SQL: DDL com PK/FK/CHECK/índices; `LAG`, `RANK`, curva ABC, `HAVING` | [`sql/`](sql) |
| Carga JDBC no banco relacional | [`load_postgres.py`](src/pipeline/load_postgres.py) |
| Testes automatizados com Spark local | [`tests/test_pipeline.py`](tests/test_pipeline.py) |
| Infra reproduzível | [`Dockerfile`](Dockerfile), [`compose.yaml`](compose.yaml) |

## Como rodar (Docker)

Pré-requisito: Docker Desktop. Dentro desta pasta:

```powershell
# 1) Sobe o PostgreSQL (o DDL do modelo estrela é aplicado na primeira subida)
docker compose up -d postgres

# 2) Gera 200 mil pedidos sintéticos em ./data/raw
docker compose run --rm pipeline python -m pipeline.generate_data --orders 200000 --out data/raw

# 3) Roda a pipeline completa e carrega no PostgreSQL (Spark UI em http://localhost:4040 durante a execução)
docker compose run --rm --service-ports pipeline

# 4) Roda as consultas analíticas
docker compose exec postgres psql -U dw -d dw -f /sql/02_consultas_analiticas.sql

# Testes
docker compose run --rm pipeline python -m pytest -q
```

Para exercitar o paralelismo: `--orders 5000000` no passo 2.

### Rodar por etapas

A pipeline também roda etapa por etapa, cada uma em seu próprio processo Spark, trocando dados por Parquet em disco. É assim que o [Airflow a orquestra](../airflow-orquestracao):

```powershell
docker compose run --rm pipeline python -m pipeline.run_pipeline --stage silver
docker compose run --rm pipeline python -m pipeline.run_pipeline --stage gold
docker compose run --rm pipeline python -m pipeline.run_pipeline --stage quality   # falha se houver violação
docker compose run --rm pipeline python -m pipeline.run_pipeline --stage load      # carga atômica no PostgreSQL
```

> **Por que Docker?** O Spark no Windows exige o `winutils.exe` (binário do Hadoop) para gravar Parquet em disco local. No container Linux isso não existe como problema, e o ambiente (Java 17 + PySpark 3.5.3) fica idêntico em qualquer máquina.

## Estado de verificação

Executado de ponta a ponta com Docker (Docker Desktop no Windows, containers Linux), com **200 mil pedidos sintéticos**:

- **Pipeline completa:** raw → silver → gold → PostgreSQL em ~5 min. 347.447 itens na silver e 312.770 linhas na fato. As contagens e a receita total (R$ 618,2 mi) conferem entre Parquet e banco; as contagens do log da carga são lidas **do PostgreSQL**, não do Parquet.
- **Quarentena:** os rejeitados batem com o que o gerador injetou — 207 JSON truncados e 1.914 duplicatas, além de 965 itens inválidos e 622 SKUs fora do catálogo.
- **Testes (14):** passam no container (Spark 3.5.3, Java 17). Cada bug encontrado em revisão tem um teste de regressão, inclusive um que prova que `validate_star` e `reconcile` **detectam** erro (fato sem linha, valor errado, grão duplicado, dimensão ausente).
- **SQL:** o DDL é aplicado na criação do banco e as 6 consultas analíticas rodam sem erro.
- **Carga atômica comprovada:** forcei uma falha na troca (constraint que os dados novos violam) e o `dw` permaneceu com a carga anterior.

### O que cada verificação de qualidade prova (e o que não prova)

| Verificação | Detecta | Observação |
|---|---|---|
| Grão único `(pedido_id, item_seq)` e chaves únicas nas dimensões | duplicação nos dados | depende dos dados |
| `reconcile`: linhas, **receita recalculada de forma independente**, clientes e dias | perda silenciosa de linhas, erro de cálculo, calendário com lacuna | depende dos dados |
| FKs órfãs (`orfaos_*`) | regressão no código (hash derivado de um lado só) | **zero por construção**: fato e dimensões usam o mesmo hash dos mesmos dados |
| FKs reais do PostgreSQL | dado inconsistente na carga | é a garantia de integridade referencial de fato |

> Os dados sintéticos são uniformes por construção (margem ~29,6% em todo canto, ticket igual em dia útil e fim de semana). As consultas provam que o modelo e o SQL funcionam; **não** revelam padrões de negócio.

### Bugs encontrados e corrigidos

1. **Primeira execução:** o `TRUNCATE` do Postgres recusa esvaziar dimensões referenciadas por FK. Resolvido pela carga em staging com troca atômica.
2. **Revisão independente:** status nulo sumia da fato sem quarentena (`NULL != 'CANCELADO'` não é verdadeiro) e a reconciliação, usando o mesmo filtro, não via; desconto fora de `[0, 1]` virava NULL ou receita negativa; catálogo com SKU duplicado multiplicaria linhas; o desempate do dedupe não era determinístico; a carga não era atômica; partições antigas sobravam no Parquet.

## Limitações e próximos passos

- **Desempenho:** ~5 min para 200 mil pedidos é lento e **não foi perfilado no Spark UI**. As verificações disparam muitos `count()`, cada um reexecutando parte do plano, e as camadas são relidas do disco. Persistir a silver e consolidar as contagens em uma única ação são os primeiros ganhos. 200 mil linhas não justificam Spark: o volume serve para exercitar a API e a estrutura, não para mostrar ganho de escala.
- **Execução local:** `local[*]`, uma máquina, Parquet em disco. **Não há HDFS, YARN nem cluster.** Rodar em YARN exigiria também `HADOOP_CONF_DIR`, caminhos HDFS e distribuição do JAR JDBC; isso não foi feito nem testado.
- **Reprocessamento completo, sem incremental.** A evolução seria `MERGE` por `(pedido_id, item_seq)` com marca d'água de ingestão. O desempate do dedupe usa `order_ts` (data de criação do pedido), pois os dados não têm timestamp de ingestão.
- **Chaves por hash:** colisão em 64 bits é desprezível neste volume, mas a chave serve para SCD1; um SCD2 exigiria incluir a vigência na chave (ou usar sequences).
- `dim_cliente` é SCD tipo 1; histórico de endereços exigiria SCD tipo 2. Cliente sem segmento vira "Não informado".
- Orquestração com Airflow (agendamento, retries, dependências entre as etapas) é o próximo projeto deste laboratório.
