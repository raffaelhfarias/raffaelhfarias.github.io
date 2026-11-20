# PostgreSQL × SQL Server neste projeto

O mesmo modelo estrela existe nos dois bancos ([`sql/`](../sql) e [`sql/sqlserver/`](../sql/sqlserver)), carregado pelo mesmo Parquet. Esta tabela reúne as diferenças que **apareceram de fato** ao portar o DDL, as consultas e a carga. Os itens marcados com ✔ foram confirmados rodando no SQL Server 2022 (edição Developer, container Linux).

## DDL

| Assunto | PostgreSQL | SQL Server (T-SQL) |
|---|---|---|
| Booleano | `BOOLEAN` | `BIT` (0/1). `TRUE` é lido como nome de coluna (Msg 207 ✔) |
| Texto com acento | `VARCHAR` já é UTF-8 | `NVARCHAR` para não depender da *collation* |
| Timestamp com fuso | `TIMESTAMPTZ` | `DATETIMEOFFSET` (não usado aqui) |
| `CREATE SCHEMA` | comando comum | **precisa de lote próprio**: dentro de um script usa-se `EXEC('CREATE SCHEMA x')` |
| "Criar se não existir" | `CREATE TABLE IF NOT EXISTS` | `IF OBJECT_ID('s.t','U') IS NULL CREATE TABLE ...` |
| Separador de lotes | n/a | `GO` é do `sqlcmd`, não do T-SQL: o DDL aqui não usa `GO` para rodar igual pelo `sqlcmd` e por JDBC |
| Cópia estrutural | `CREATE TABLE s.t (LIKE d.t INCLUDING DEFAULTS)` | `SELECT TOP 0 * INTO s.t FROM d.t` |
| Nome de constraint | gerado se omitido | gerado também, mas aqui são nomeadas (`pk_`, `fk_`, `ck_`): erro de FK fica legível |

## Consultas

| Assunto | PostgreSQL | SQL Server |
|---|---|---|
| Limitar linhas | `LIMIT n` | `SELECT TOP (n)` ✔ (`LIMIT` dá erro de sintaxe, Msg 102) |
| Conversão | `valor::bigint` | `CAST(valor AS BIGINT)` |
| Junção por coluna comum | `JOIN t USING (coluna)` | só `JOIN t ON a.coluna = b.coluna` (`USING` é erro de sintaxe ✔) |
| Janela nomeada | `WINDOW w AS (...)` | funciona no 2022 ✔ (versão desta imagem); a cláusula é recente no SQL Server, então as consultas repetem o `OVER (...)` para não depender dela |
| `GROUP BY` | aceita posição (`GROUP BY 1`) | não aceita posição (Msg 164 ✔): é preciso repetir a expressão |
| Empates no `ORDER BY` + `LIMIT`/`TOP` | indefinido | indefinido nos dois: por isso as consultas 4 e 6 desempatam por colunas (`estado, canal` e `cliente_id`), e a curva ABC por `sku` |

As 6 consultas analíticas devolvem **os mesmos números** nos dois bancos com os mesmos 312.770 registros ✔ (receita total R$ 618.237.076,83; série mensal e variações; top 3 por categoria; curva ABC 282/113/105; ticket médio por tipo de dia). A única diferença visível é a apresentação (o `sqlcmd` mostra `-7.900000` onde o `psql` mostra `-7.9`: escala do `DECIMAL`).

## Carga

| Assunto | PostgreSQL | SQL Server |
|---|---|---|
| Esvaziar tabela referenciada por FK | `TRUNCATE a, b` (várias tabelas) | **recusa** `TRUNCATE` de tabela referenciada (Msg 4712 ✔) e **nem aceita** várias tabelas no mesmo `TRUNCATE` (erro de sintaxe ✔) |
| Como a troca atômica esvazia | `TRUNCATE` de todas, numa instrução | `DELETE` na ordem das FKs: fato primeiro, dimensões depois |
| Transação com DDL | `TRUNCATE`/DDL são transacionais | também transacionais, mas `CREATE SCHEMA` exige lote próprio |
| `MERGE` | PostgreSQL 15+; **sem** `WHEN NOT MATCHED BY SOURCE` até a versão 17 | existe há muito tempo e **tem** `WHEN NOT MATCHED BY SOURCE THEN DELETE` |
| Driver JDBC | `org.postgresql.Driver` | `com.microsoft.sqlserver.jdbc.SQLServerDriver` + `encrypt=false;trustServerCertificate=true` no container de estudo |

### O que isso muda para a carga incremental
No PostgreSQL 16 as remoções (cancelamento tardio, item que sumiu) exigiram um `DELETE` separado, na mesma transação. No SQL Server o mesmo trabalho caberia **dentro do `MERGE`** com `WHEN NOT MATCHED BY SOURCE THEN DELETE`, com uma condição extra para limitar a remoção aos pedidos do lote (sem ela, o `MERGE` apagaria tudo o que não veio no lote). Esta diferença **não foi implementada nem testada aqui**: a carga incremental existe só para PostgreSQL.

## O que não foi coberto

- **Índices columnstore**, particionamento por data e compressão, que são o que um DW em SQL Server usaria em volume de verdade. O volume aqui (300 mil linhas) não os justifica.
- **Plano de execução e estatísticas**: as consultas rodaram, mas não foram analisadas com o plano nem comparadas em desempenho entre os dois bancos.
- **SQL Server em Windows, Always On, SSIS/SSAS**: nada disso. É um SQL Server 2022 Developer em container Linux.
- **DB2**: não há equivalente aqui.
