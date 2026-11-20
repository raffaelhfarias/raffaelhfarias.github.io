-- Consultas analíticas sobre o modelo em estrela.
-- Rodar:  docker compose exec postgres psql -U dw -d dw -f /sql/02_consultas_analiticas.sql
SET search_path TO dw;

-- 1) Receita mensal com variação sobre o mês anterior (LAG) e sobre o mesmo mês do ano anterior.
WITH mensal AS (
    SELECT d.ano, d.mes, d.nome_mes, SUM(f.valor_liquido) AS receita
    FROM fato_vendas f
    JOIN dim_data d USING (date_key)
    GROUP BY d.ano, d.mes, d.nome_mes
)
SELECT ano, mes, nome_mes, receita,
       ROUND(100.0 * (receita - LAG(receita, 1)  OVER w) / NULLIF(LAG(receita, 1)  OVER w, 0), 1) AS var_mom_pct,
       ROUND(100.0 * (receita - LAG(receita, 12) OVER w) / NULLIF(LAG(receita, 12) OVER w, 0), 1) AS var_yoy_pct
FROM mensal
WINDOW w AS (ORDER BY ano, mes)
ORDER BY ano, mes;

-- 2) Top 3 produtos por categoria em margem (RANK por partição).
SELECT *
FROM (
    SELECT p.categoria, p.nome AS produto, SUM(f.margem) AS margem_total,
           RANK() OVER (PARTITION BY p.categoria ORDER BY SUM(f.margem) DESC) AS posicao
    FROM fato_vendas f
    JOIN dim_produto p USING (produto_key)
    GROUP BY p.categoria, p.nome
) t
WHERE posicao <= 3
ORDER BY categoria, posicao;

-- 3) Curva ABC de produtos. A classe usa o acumulado ANTES do produto: o item que
--    cruza 80% ainda pertence à classe A (A = primeiros 80% da receita, B = até 95%).
--    Com os dados sintéticos (uniformes) quase todos os SKUs pesam parecido, então a
--    curva sai achatada; em dados reais a classe A costuma ser uma fração pequena dos SKUs.
WITH receita AS (
    SELECT p.sku, SUM(f.valor_liquido) AS receita
    FROM fato_vendas f
    JOIN dim_produto p USING (produto_key)
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
GROUP BY 1
ORDER BY 1;

-- 4) Margem % por estado e canal. O HAVING é um piso de volume: com 200 mil pedidos ele não
--    exclui nada; serve para amostras menores, onde a margem de poucos pedidos engana.
SELECT c.estado, ca.canal,
       COUNT(DISTINCT f.pedido_id) AS pedidos,
       ROUND(100.0 * SUM(f.margem) / SUM(f.valor_liquido), 1) AS margem_pct
FROM fato_vendas f
JOIN dim_cliente c  USING (cliente_key)
JOIN dim_canal  ca  USING (canal_key)
GROUP BY c.estado, ca.canal
HAVING COUNT(DISTINCT f.pedido_id) >= 500
ORDER BY margem_pct DESC, c.estado, ca.canal
LIMIT 10;

-- 5) Fim de semana vs dia útil: ticket médio por pedido.
WITH pedidos AS (
    SELECT f.pedido_id, d.fim_de_semana, SUM(f.valor_liquido) AS valor
    FROM fato_vendas f
    JOIN dim_data d USING (date_key)
    GROUP BY f.pedido_id, d.fim_de_semana
)
SELECT CASE WHEN fim_de_semana THEN 'Fim de semana' ELSE 'Dia útil' END AS tipo_dia,
       COUNT(*) AS pedidos,
       ROUND(AVG(valor), 2) AS ticket_medio
FROM pedidos
GROUP BY fim_de_semana;

-- 6) Clientes que compraram em 3 ou mais canais (agregação + filtro pós-agregação com HAVING).
SELECT c.cliente_id, c.nome, COUNT(DISTINCT f.canal_key) AS canais, SUM(f.valor_liquido) AS gasto_total
FROM fato_vendas f
JOIN dim_cliente c USING (cliente_key)
GROUP BY c.cliente_id, c.nome
HAVING COUNT(DISTINCT f.canal_key) >= 3
ORDER BY gasto_total DESC, c.cliente_id
LIMIT 10;
