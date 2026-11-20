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
| Carga JDBC no banco relacional, atômica (staging + troca em uma transação) | [`load_postgres.py`](src/pipeline/load_postgres.py) |
| **O mesmo modelo no SQL Server (T-SQL)**: DDL, consultas portadas e carga atômica com as diferenças de dialeto | [`sql/sqlserver/`](sql/sqlserver), [`load_sqlserver.py`](src/pipeline/load_sqlserver.py), [`docs/postgresql-vs-sqlserver.md`](docs/postgresql-vs-sqlserver.md) |
| **Carga incremental com `MERGE`**: upsert, remoção de linhas que sumiram, controle por checksum, idempotência | [`incremental.py`](src/pipeline/incremental.py), [`docs/carga-incremental.md`](docs/carga-incremental.md) |
| Testes automatizados: Spark local, PostgreSQL real e regressões de bugs | [`tests/`](tests) |
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

## Carga incremental

A carga completa reprocessa tudo a cada execução. A **carga incremental** processa só os lotes novos e mescla o resultado no modelo com `MERGE`, tratando o que a carga completa nunca enfrenta: pedidos reenviados com mudança, cancelamentos tardios e itens que somem de um pedido. O desenho e as decisões estão em [`docs/carga-incremental.md`](docs/carga-incremental.md).

```powershell
# 5 lotes diários, cada um com ~5% de reenvios de pedidos antigos (status, cancelamento, item removido, quantidade/desconto corrigidos)
docker compose run --rm pipeline python -m pipeline.generate_data --lotes 5 --pedidos-por-lote 2000 --out data/raw_inc

# processa os lotes pendentes (o schema dw_incremental é criado do mesmo DDL se não existir)
docker compose run --rm pipeline python -m pipeline.incremental --schema dw_incremental

# rodar de novo não faz nada: os lotes já constam em dw_incremental.controle_cargas
docker compose run --rm pipeline python -m pipeline.incremental --schema dw_incremental
```

Saída real com 5 lotes de 2.000 pedidos (cada linha é um lote):

```
lote_0001: +3162 inseridas, ~0 atualizadas, -0 removidas, 15 rejeitados
lote_0002: +3110 inseridas, ~18 atualizadas, -41 removidas, 15 rejeitados
lote_0003: +3131 inseridas, ~20 atualizadas, -33 removidas, 20 rejeitados
lote_0004: +3173 inseridas, ~20 atualizadas, -37 removidas, 14 rejeitados
lote_0005: +3158 inseridas, ~15 atualizadas, -40 removidas, 18 rejeitados
```

Uma conferência que dá para fazer à mão: inseridas − removidas = linhas na fato (15.734 − 151 = 15.583, igual ao `count(*)` do banco).

> **Por que Docker?** O Spark no Windows exige o `winutils.exe` (binário do Hadoop) para gravar Parquet em disco local. No container Linux isso não existe como problema, e o ambiente (Java 17 + PySpark 3.5.3) fica idêntico em qualquer máquina.

## Estado de verificação

Executado de ponta a ponta com Docker (Docker Desktop no Windows, containers Linux), com **200 mil pedidos sintéticos**:

- **Pipeline completa:** raw → silver → gold → PostgreSQL em ~5 min. 347.447 itens na silver e 312.770 linhas na fato. As contagens e a receita total (R$ 618,2 mi) conferem entre Parquet e banco; as contagens do log da carga são lidas **do PostgreSQL**, não do Parquet.
- **Quarentena:** os rejeitados batem com o que o gerador injetou — 207 JSON truncados e 1.914 duplicatas, além de 965 itens inválidos e 622 SKUs fora do catálogo.
- **Testes (55):** passam no container (Spark 3.5.3, Java 17, PostgreSQL 16 e SQL Server 2022); 12 deles tocam um banco real e os outros 43 são unitários ou usam só o Spark local. Sem o SQL Server no ar, os 3 testes de integração dele são ignorados e passam 52. Cada bug encontrado em revisão tem um teste de regressão, inclusive um que prova que `validate_star` e `reconcile` **detectam** erro (fato sem linha, valor errado, grão duplicado, dimensão ausente).
- **SQL Server:** 312.770 linhas carregadas em ~65 s, com as contagens lidas do próprio banco. As 6 consultas em T-SQL devolvem **os mesmos números do PostgreSQL** (receita total, série mensal, top 3 por categoria, curva ABC, ticket médio). 13 testes (10 unitários e 3 de integração: carga confere com o Spark e o banco impõe as FKs; uma falha no meio da troca preserva a carga anterior; as consultas executam).
- **Carga incremental:** 26 testes, 8 de integração contra um PostgreSQL real (schema isolado): cenário com insert, update, cancelamento tardio e item removido; reaplicar um lote não muda nada (estado idêntico, bit a bit); uma falha no meio do `MERGE` desfaz até o `DELETE` que já tinha rodado; pedido reenviado com **todos** os itens rejeitados sai da fato; cancelado que volta a ficar ativo entra; lote sem nenhum pedido válido é registrado sem efeito; duas cargas simultâneas no mesmo schema são recusadas; e a verificação antes do commit (contagem **e** valor) desfaz a transação. O teste do pedido sem itens válidos foi conferido por mutação: com o comportamento antigo ele falha. Um teste confere as colunas do `MERGE` contra o DDL e contra os DataFrames, e outro garante que gerar mais lotes não altera os anteriores.
- **SQL:** o DDL é aplicado na criação do banco e as 6 consultas analíticas rodam sem erro.
- **Carga atômica (PostgreSQL e SQL Server) com teste automatizado:** uma constraint que os dados novos violam faz a troca falhar no `INSERT` (depois do `TRUNCATE`/`DELETE`) e o banco permanece com a carga anterior; a carga seguinte, sem a sabotagem, passa. Um teste também confere que reprocessar não deixa partições antigas no Parquet.

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
3. **Ao construir o incremental:** o `df.cache()` do Spark é indexado pelo plano lógico, então reler o **mesmo caminho** de um arquivo reescrito devolvia os dados antigos, enquanto o checksum registrado já era o do arquivo novo. Descoberto por um teste de integração (o relatório dizia 6 itens para um arquivo de 1). O que de fato protege é liberar o cache ao fim de cada lote (`clearCache()`); invalidar o caminho antes de ler (`refreshByPath`) é uma defesa adicional que os testes não distinguem. Uma primeira hipótese (cache de listagem de arquivos) estava errada e foi descartada.
4. **Segunda revisão independente (sobre o incremental):** a afirmação "gerar N+1 lotes reproduz os N primeiros byte a byte" era **falsa a partir do 3º lote**, porque o número de clientes dependia do total de lotes e mudava a sequência do gerador (a DAG reaplicaria todos os lotes na 3ª execução); um pedido reenviado cujos itens foram todos rejeitados nunca saía da fato; a verificação antes do commit só conferia contagem; duas cargas simultâneas misturariam o staging; o nome do schema de staging não era validado. Tudo corrigido e coberto por teste, e a 3ª execução da DAG foi refeita de verdade.

## Limitações e próximos passos

- **Desempenho:** ~5 min para 200 mil pedidos é lento e **não foi perfilado no Spark UI**. As verificações disparam muitos `count()`, cada um reexecutando parte do plano, e as camadas são relidas do disco. Persistir a silver e consolidar as contagens em uma única ação são os primeiros ganhos. 200 mil linhas não justificam Spark: o volume serve para exercitar a API e a estrutura, não para mostrar ganho de escala.
- **Execução local:** `local[*]`, uma máquina, Parquet em disco. **Não há HDFS, YARN nem cluster.** Rodar em YARN exigiria também `HADOOP_CONF_DIR`, caminhos HDFS e distribuição do JAR JDBC; isso não foi feito nem testado.
- **Carga completa × incremental:** a completa continua reprocessando tudo (é um *rebuild*). O incremental resolve o reenvio com "o último a chegar vence", sem versão nem `updated_at` na origem: uma versão antiga que chegue depois de uma nova a sobrescreve, e isso vale também para `dim_cliente`. Reaplicar um lote **antigo** alterado regride pedidos que lotes posteriores já atualizaram, e pedido que sumiu de um arquivo reescrito continua no DW. Pedido com cabeçalho inválido (sem `customer.id`, status fora do domínio) fica intocado. A trava de concorrência é do PostgreSQL (advisory lock); no SQL Server não há carga incremental. Detalhes em [`docs/carga-incremental.md`](docs/carga-incremental.md).
- **SQL Server:** é um container Linux de estudo, sem columnstore, particionamento, análise de plano nem comparação de desempenho com o PostgreSQL. A carga incremental (`MERGE`) existe só para PostgreSQL; no SQL Server as remoções caberiam no próprio `MERGE` com `WHEN NOT MATCHED BY SOURCE`, o que não foi implementado. **Não há DB2.**
- **Chaves por hash:** colisão em 64 bits é desprezível neste volume, mas a chave serve para SCD1; um SCD2 exigiria incluir a vigência na chave (ou usar sequences).
- `dim_cliente` é SCD tipo 1; histórico de endereços exigiria SCD tipo 2. Cliente sem segmento vira "Não informado".
- A orquestração com Airflow está em [`airflow-orquestracao`](../airflow-orquestracao), com uma DAG para a carga completa e outra para a incremental.
