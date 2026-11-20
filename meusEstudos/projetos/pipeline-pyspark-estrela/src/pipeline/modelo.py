"""Definição do modelo estrela em um só lugar: tabelas, colunas e chaves.

Usado pelas cargas (PostgreSQL e SQL Server) e pela carga incremental. Um teste confere
estas listas contra os DDLs, para código e schema não divergirem em silêncio.
"""

from __future__ import annotations

# Dimensões antes da fato (a fato referencia as dimensões).
ORDEM_DE_CARGA = ["dim_data", "dim_cliente", "dim_produto", "dim_pagamento", "dim_canal", "fato_vendas"]

COLUNAS = {
    "dim_data": ["date_key", "data", "ano", "trimestre", "mes", "nome_mes", "dia", "dia_semana", "fim_de_semana"],
    "dim_cliente": ["cliente_key", "cliente_id", "nome", "cidade", "estado", "segmento"],
    "dim_produto": ["produto_key", "sku", "nome", "categoria", "subcategoria", "marca"],
    "dim_pagamento": ["pagamento_key", "metodo", "parcelas"],
    "dim_canal": ["canal_key", "canal"],
    "fato_vendas": [
        "pedido_id", "item_seq", "date_key", "cliente_key", "produto_key", "pagamento_key", "canal_key",
        "quantidade", "preco_unitario", "desconto_pct", "valor_bruto", "valor_desconto", "valor_liquido",
        "custo_total", "margem", "ano_mes",
    ],
}
CHAVES = {
    "dim_data": ["date_key"],
    "dim_cliente": ["cliente_key"],
    "dim_produto": ["produto_key"],
    "dim_pagamento": ["pagamento_key"],
    "dim_canal": ["canal_key"],
    "fato_vendas": ["pedido_id", "item_seq"],
}
