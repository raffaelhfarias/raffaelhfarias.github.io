-- Consultas analíticas em T-SQL (SQL Server 2022): as mesmas de sql/02_consultas_analiticas.sql.
-- Rodar:  docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P "$SA_PASSWORD" -d dw -i /sql/sqlserver/02_consultas_analiticas.sql
--
-- Diferenças em relação ao PostgreSQL, todas visíveis abaixo:
--   LIMIT n                    -> SELECT TOP (n)
--   expr::tipo                 -> CAST(expr AS tipo)
--   WINDOW w AS (...) nomeada  -> repetida em cada OVER (mais portátil entre versões)
--   JOIN ... USING (coluna)    -> JOIN ... ON a.coluna = b.coluna (não existe USING)
--   ROUND(100.0 * x / y, 1)    -> igual, mas a divisão de inteiros é inteira: força-se DECIMAL
SET NOCOUNT ON;

-- 1) Receita mensal com variação sobre o mês anterior (LAG) e sobre o mesmo mês do ano anterior.
WITH mensal AS (
    SELECT d.ano, d.mes, d.nome_mes, SUM(f.valor_liquido) AS receita
    FROM dw.fato_vendas f
    JOIN dw.dim_data d ON d.date_key = f.date_key
    GROUP BY d.ano, d.mes, d.nome_mes
)
SELECT ano, mes, nome_mes, receita,
       ROUND(100.0 * (receita - LAG(receita, 1)  OVER (ORDER BY ano, mes)) / NULLIF(LAG(receita, 1)  OVER (ORDER BY ano, mes), 0), 1) AS var_mom_pct,
       ROUND(100.0 * (receita - LAG(receita, 12) OVER (ORDER BY ano, mes)) / NULLIF(LAG(receita, 12) OVER (ORDER BY ano, mes), 0), 1) AS var_yoy_pct
FROM mensal
ORDER BY ano, mes;

-- 2) Top 3 produtos por categoria em margem (RANK por partição).
SELECT categoria, produto, margem_total, posicao
FROM (
    SELECT p.categoria, p.nome AS produto, SUM(f.margem) AS margem_total,
           RANK() OVER (PARTITION BY p.categoria ORDER BY SUM(f.margem) DESC) AS posicao
    FROM dw.fato_vendas f
    JOIN dw.dim_produto p ON p.produto_key = f.produto_key
    GROUP BY p.categoria, p.nome
) t
WHERE posicao <= 3
ORDER BY categoria, posicao;

-- 3) Curva ABC de produtos. A classe usa o acumulado ANTES do produto (o item que cruza 80% ainda é A).
WITH receita AS (
    SELECT p.sku, SUM(f.valor_liquido) AS receita
    FROM dw.fato_vendas f
    JOIN dw.dim_produto p ON p.produto_key = f.produto_key
    GROUP BY p.sku
),
acumulado AS (
    SELECT sku, receita,
           (SUM(receita) OVER (ORDER BY receita DESC, sku ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - receita)
               / SUM(receita) OVER () AS acum_anterior
    FROM receita
)
SELECT CASE WHEN acum_anterior < 0.80 THEN 'A' WHEN acum_anterior < 0.95 THEN 'B' ELSE 'C' END AS classe,
       COUNT(*) AS qtd_produtos,
       ROUND(SUM(receita), 2) AS receita
FROM acumulado
GROUP BY CASE WHEN acum_anterior < 0.80 THEN 'A' WHEN acum_anterior < 0.95 THEN 'B' ELSE 'C' END
ORDER BY classe;

-- 4) Margem % por estado e canal (as 10 maiores). HAVING como piso de volume.
SELECT TOP (10) c.estado, ca.canal,
       COUNT(DISTINCT f.pedido_id) AS pedidos,
       ROUND(100.0 * SUM(f.margem) / SUM(f.valor_liquido), 1) AS margem_pct
FROM dw.fato_vendas f
JOIN dw.dim_cliente c  ON c.cliente_key  = f.cliente_key
JOIN dw.dim_canal   ca ON ca.canal_key   = f.canal_key
GROUP BY c.estado, ca.canal
HAVING COUNT(DISTINCT f.pedido_id) >= 500
ORDER BY margem_pct DESC, c.estado, ca.canal;

-- 5) Fim de semana vs dia útil: ticket médio por pedido.
WITH pedidos AS (
    SELECT f.pedido_id, d.fim_de_semana, SUM(f.valor_liquido) AS valor
    FROM dw.fato_vendas f
    JOIN dw.dim_data d ON d.date_key = f.date_key
    GROUP BY f.pedido_id, d.fim_de_semana
)
SELECT CASE WHEN fim_de_semana = 1 THEN 'Fim de semana' ELSE 'Dia útil' END AS tipo_dia,
       COUNT(*) AS pedidos,
       ROUND(AVG(valor), 2) AS ticket_medio
FROM pedidos
GROUP BY fim_de_semana;

-- 6) Clientes que compraram em 3 ou mais canais (agregação + filtro pós-agregação com HAVING).
SELECT TOP (10) c.cliente_id, c.nome, COUNT(DISTINCT f.canal_key) AS canais, SUM(f.valor_liquido) AS gasto_total
FROM dw.fato_vendas f
JOIN dw.dim_cliente c ON c.cliente_key = f.cliente_key
GROUP BY c.cliente_id, c.nome
HAVING COUNT(DISTINCT f.canal_key) >= 3
ORDER BY gasto_total DESC, c.cliente_id;
