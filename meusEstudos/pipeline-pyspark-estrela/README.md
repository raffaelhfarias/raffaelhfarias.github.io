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

> **Por que Docker?** O Spark no Windows exige o `winutils.exe` (binário do Hadoop) para gravar Parquet em disco local. No container Linux isso não existe como problema, e o ambiente (Java 17 + PySpark 3.5.3) fica idêntico em qualquer máquina.

## Estado de verificação

Executado de ponta a ponta com Docker (Docker Desktop no Windows, containers Linux), com 200 mil pedidos:

- **Pipeline completa:** raw → silver → gold → PostgreSQL em ~4 min. 347.447 itens na silver, 312.770 linhas na fato, **0 violações de integridade**, fato reconciliada com a silver. A contagem no banco (312.770) e a receita total (R$ 618,2 mi) conferem com o Parquet.
- **Quarentena:** os rejeitados batem com o que o gerador injetou — 207 JSON truncados e 1.914 duplicatas, além de 965 itens inválidos e 622 SKUs fora do catálogo.
- **Testes (6):** passam no container (Spark 3.5.3, Java 17).
- **SQL:** o DDL é aplicado na criação do banco e as 6 consultas analíticas rodam sem erro.
- **Bug encontrado na primeira execução:** o `TRUNCATE` do Postgres recusa esvaziar dimensões referenciadas por FK. Corrigido com `cascadeTruncate=true` (ver [`load_postgres.py`](src/pipeline/load_postgres.py)).

> Os dados sintéticos são uniformes por construção (margem ~29,6% em todo canto, ticket igual em dia útil e fim de semana). As consultas provam que o modelo e o SQL funcionam; **não** revelam padrões de negócio.

## Limitações e próximos passos

- **Desempenho:** ~4 min para 200 mil pedidos é lento. O run relê o Parquet várias vezes e dispara muitos `count()` nas verificações, cada um reexecutando parte do plano. Há ganho fácil com `cache()`/`persist()` da silver e consolidando as contagens em uma única ação. Não otimizei de propósito, para não complicar o código antes de você entendê-lo.
- Execução em `local[*]` (uma máquina). A mesma aplicação roda em um cluster Spark/YARN trocando o `master`, mas isso não foi testado aqui.
- `dim_cliente` é SCD tipo 1; histórico de endereços exigiria SCD tipo 2.
- Reprocessamento é por sobrescrita das partições afetadas; carga incremental (apenas novos pedidos) é uma evolução natural.
- Orquestração com Airflow (agendamento, retries, dependências entre as etapas) é o próximo projeto deste laboratório.
