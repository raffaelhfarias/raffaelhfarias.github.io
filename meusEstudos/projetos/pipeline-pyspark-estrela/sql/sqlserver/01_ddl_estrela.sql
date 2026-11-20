-- Modelo dimensional em estrela, em T-SQL (SQL Server 2022).
-- Mesmo modelo de sql/01_ddl_estrela.sql (PostgreSQL), com o dialeto do SQL Server.
-- Grão da fato: 1 linha por item de pedido (pedido_id, item_seq), sem pedidos cancelados.
--
-- Idempotente: cada objeto só é criado se não existir, então pode ser reexecutado.
-- Não usa "GO" (separador do sqlcmd, não do T-SQL): roda igual pelo sqlcmd e por JDBC.
-- Diferenças de dialeto em relação ao PostgreSQL: BIT no lugar de BOOLEAN, NVARCHAR para texto
-- com acento, CREATE SCHEMA precisa de lote próprio (por isso o EXEC), FKs com nome explícito.

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'dw') EXEC('CREATE SCHEMA dw');

IF OBJECT_ID('dw.dim_data', 'U') IS NULL
CREATE TABLE dw.dim_data (
    date_key       INT           NOT NULL CONSTRAINT pk_dim_data PRIMARY KEY,   -- yyyymmdd
    data           DATE          NOT NULL CONSTRAINT uq_dim_data_data UNIQUE,
    ano            SMALLINT      NOT NULL,
    trimestre      SMALLINT      NOT NULL CONSTRAINT ck_dim_data_trimestre CHECK (trimestre BETWEEN 1 AND 4),
    mes            SMALLINT      NOT NULL CONSTRAINT ck_dim_data_mes CHECK (mes BETWEEN 1 AND 12),
    nome_mes       NVARCHAR(10)  NOT NULL,
    dia            SMALLINT      NOT NULL,
    dia_semana     NVARCHAR(10)  NOT NULL,
    fim_de_semana  BIT           NOT NULL
);

IF OBJECT_ID('dw.dim_cliente', 'U') IS NULL
CREATE TABLE dw.dim_cliente (
    cliente_key  BIGINT         NOT NULL CONSTRAINT pk_dim_cliente PRIMARY KEY,   -- hash determinístico do cliente_id
    cliente_id   VARCHAR(20)    NOT NULL CONSTRAINT uq_dim_cliente_id UNIQUE,
    nome         NVARCHAR(120)  NOT NULL,
    cidade       NVARCHAR(80)   NOT NULL,
    estado       CHAR(2)        NOT NULL,
    segmento     NVARCHAR(20)   NOT NULL
);

IF OBJECT_ID('dw.dim_produto', 'U') IS NULL
CREATE TABLE dw.dim_produto (
    produto_key   BIGINT         NOT NULL CONSTRAINT pk_dim_produto PRIMARY KEY,
    sku           VARCHAR(20)    NOT NULL CONSTRAINT uq_dim_produto_sku UNIQUE,
    nome          NVARCHAR(120)  NOT NULL,
    categoria     NVARCHAR(40)   NOT NULL,
    subcategoria  NVARCHAR(40)   NOT NULL,
    marca         NVARCHAR(40)   NOT NULL
);

IF OBJECT_ID('dw.dim_pagamento', 'U') IS NULL
CREATE TABLE dw.dim_pagamento (
    pagamento_key  BIGINT        NOT NULL CONSTRAINT pk_dim_pagamento PRIMARY KEY,
    metodo         NVARCHAR(30)  NOT NULL,
    parcelas       SMALLINT      NOT NULL CONSTRAINT ck_dim_pagamento_parcelas CHECK (parcelas >= 1),
    CONSTRAINT uq_dim_pagamento UNIQUE (metodo, parcelas)
);

IF OBJECT_ID('dw.dim_canal', 'U') IS NULL
CREATE TABLE dw.dim_canal (
    canal_key  BIGINT        NOT NULL CONSTRAINT pk_dim_canal PRIMARY KEY,
    canal      NVARCHAR(30)  NOT NULL CONSTRAINT uq_dim_canal UNIQUE
);

IF OBJECT_ID('dw.fato_vendas', 'U') IS NULL
CREATE TABLE dw.fato_vendas (
    pedido_id       VARCHAR(20)    NOT NULL,
    item_seq        INT            NOT NULL,
    date_key        INT            NOT NULL CONSTRAINT fk_fato_data      FOREIGN KEY REFERENCES dw.dim_data (date_key),
    cliente_key     BIGINT         NOT NULL CONSTRAINT fk_fato_cliente   FOREIGN KEY REFERENCES dw.dim_cliente (cliente_key),
    produto_key     BIGINT         NOT NULL CONSTRAINT fk_fato_produto   FOREIGN KEY REFERENCES dw.dim_produto (produto_key),
    pagamento_key   BIGINT         NOT NULL CONSTRAINT fk_fato_pagamento FOREIGN KEY REFERENCES dw.dim_pagamento (pagamento_key),
    canal_key       BIGINT         NOT NULL CONSTRAINT fk_fato_canal     FOREIGN KEY REFERENCES dw.dim_canal (canal_key),
    quantidade      INT            NOT NULL CONSTRAINT ck_fato_quantidade CHECK (quantidade > 0),
    preco_unitario  DECIMAL(12,2)  NOT NULL,
    desconto_pct    DECIMAL(5,4)   NOT NULL,
    valor_bruto     DECIMAL(14,2)  NOT NULL,
    valor_desconto  DECIMAL(14,2)  NOT NULL,
    valor_liquido   DECIMAL(14,2)  NOT NULL,
    custo_total     DECIMAL(14,2)  NOT NULL,
    margem          DECIMAL(14,2)  NOT NULL,
    ano_mes         CHAR(7)        NOT NULL,
    CONSTRAINT pk_fato_vendas PRIMARY KEY (pedido_id, item_seq)
);

-- O SQL Server, como o PostgreSQL, não cria índice automaticamente nas colunas de FK.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_fato_date' AND object_id = OBJECT_ID('dw.fato_vendas'))
    CREATE NONCLUSTERED INDEX ix_fato_date    ON dw.fato_vendas (date_key);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_fato_cliente' AND object_id = OBJECT_ID('dw.fato_vendas'))
    CREATE NONCLUSTERED INDEX ix_fato_cliente ON dw.fato_vendas (cliente_key);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_fato_produto' AND object_id = OBJECT_ID('dw.fato_vendas'))
    CREATE NONCLUSTERED INDEX ix_fato_produto ON dw.fato_vendas (produto_key);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_fato_ano_mes' AND object_id = OBJECT_ID('dw.fato_vendas'))
    CREATE NONCLUSTERED INDEX ix_fato_ano_mes ON dw.fato_vendas (ano_mes);
