-- Modelo dimensional em estrela (PostgreSQL).
-- Executado automaticamente na primeira subida do container (docker-entrypoint-initdb.d).
-- Grão da fato: 1 linha por item de pedido (pedido_id, item_seq), sem pedidos cancelados.

CREATE SCHEMA IF NOT EXISTS dw;
SET search_path TO dw;

CREATE TABLE dim_data (
    date_key       INTEGER      PRIMARY KEY,          -- yyyymmdd
    data           DATE         NOT NULL UNIQUE,
    ano            SMALLINT     NOT NULL,
    trimestre      SMALLINT     NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    mes            SMALLINT     NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nome_mes       VARCHAR(10)  NOT NULL,
    dia            SMALLINT     NOT NULL,
    dia_semana     VARCHAR(10)  NOT NULL,
    fim_de_semana  BOOLEAN      NOT NULL
);

CREATE TABLE dim_cliente (
    cliente_key  BIGINT        PRIMARY KEY,           -- hash determinístico do cliente_id
    cliente_id   VARCHAR(20)   NOT NULL UNIQUE,
    nome         VARCHAR(120)  NOT NULL,
    cidade       VARCHAR(80)   NOT NULL,
    estado       CHAR(2)       NOT NULL,
    segmento     VARCHAR(20)   NOT NULL
);

CREATE TABLE dim_produto (
    produto_key   BIGINT        PRIMARY KEY,
    sku           VARCHAR(20)   NOT NULL UNIQUE,
    nome          VARCHAR(120)  NOT NULL,
    categoria     VARCHAR(40)   NOT NULL,
    subcategoria  VARCHAR(40)   NOT NULL,
    marca         VARCHAR(40)   NOT NULL
);

CREATE TABLE dim_pagamento (
    pagamento_key  BIGINT       PRIMARY KEY,
    metodo         VARCHAR(30)  NOT NULL,
    parcelas       SMALLINT     NOT NULL CHECK (parcelas >= 1),
    UNIQUE (metodo, parcelas)
);

CREATE TABLE dim_canal (
    canal_key  BIGINT       PRIMARY KEY,
    canal      VARCHAR(30)  NOT NULL UNIQUE
);

CREATE TABLE fato_vendas (
    pedido_id       VARCHAR(20)    NOT NULL,
    item_seq        INTEGER        NOT NULL,
    date_key        INTEGER        NOT NULL REFERENCES dim_data (date_key),
    cliente_key     BIGINT         NOT NULL REFERENCES dim_cliente (cliente_key),
    produto_key     BIGINT         NOT NULL REFERENCES dim_produto (produto_key),
    pagamento_key   BIGINT         NOT NULL REFERENCES dim_pagamento (pagamento_key),
    canal_key       BIGINT         NOT NULL REFERENCES dim_canal (canal_key),
    quantidade      INTEGER        NOT NULL CHECK (quantidade > 0),
    preco_unitario  NUMERIC(12,2)  NOT NULL,
    desconto_pct    NUMERIC(5,4)   NOT NULL,
    valor_bruto     NUMERIC(14,2)  NOT NULL,
    valor_desconto  NUMERIC(14,2)  NOT NULL,
    valor_liquido   NUMERIC(14,2)  NOT NULL,
    custo_total     NUMERIC(14,2)  NOT NULL,
    margem          NUMERIC(14,2)  NOT NULL,
    ano_mes         CHAR(7)        NOT NULL,
    PRIMARY KEY (pedido_id, item_seq)
);

-- Índices nas chaves estrangeiras: o PostgreSQL não os cria automaticamente
-- e são eles que sustentam os joins estrela -> dimensão.
CREATE INDEX ix_fato_date     ON fato_vendas (date_key);
CREATE INDEX ix_fato_cliente  ON fato_vendas (cliente_key);
CREATE INDEX ix_fato_produto  ON fato_vendas (produto_key);
CREATE INDEX ix_fato_ano_mes  ON fato_vendas (ano_mes);
