"""Transformações puras (DataFrame in, DataFrame out) da pipeline.

Camadas (arquitetura medalhão):
  raw    -> JSON/CSV como chegou da origem
  silver -> itens de pedido limpos, tipados, sem duplicatas + quarentena de rejeitados
  gold   -> modelo dimensional em estrela (dimensões + fato)

Nenhuma função aqui escreve em disco: isso mantém tudo testável em memória.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from pipeline.schemas import ORDERS_SCHEMA, PRODUCTS_SCHEMA

STATUS_EXCLUIDO_DA_FATO = "CANCELADO"
# Domínio permitido. Fora disso o pedido vai para quarentena: um filtro como
# `status != 'CANCELADO'` descartaria NULL em silêncio (NULL != x é NULL, não verdadeiro).
STATUS_VALIDOS = ["ENTREGUE", "ENVIADO", "PAGO", "CANCELADO"]
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def surrogate_key(*cols: str | Column) -> Column:
    """Chave substituta determinística (hash de 64 bits da chave natural).

    Escolha deliberada: ``row_number()``/``monotonically_increasing_id()`` mudam
    a cada execução e exigiriam um lookup contra a dimensão existente para manter
    a fato consistente. Com hash, dimensão e fato derivam a mesma chave
    independentemente, em paralelo, e o reprocessamento é idempotente.
    """
    return F.xxhash64(*[F.col(c) if isinstance(c, str) else c for c in cols])


def _rejeitado(df: DataFrame, motivo: str, etapa: str) -> DataFrame:
    """Padroniza um DataFrame de registros rejeitados (quarentena)."""
    return df.select(
        F.lit(etapa).alias("etapa"),
        F.lit(motivo).alias("motivo"),
        F.to_json(F.struct(*df.columns)).alias("registro"),
    )


def _vazio_rejeitado(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame([], "etapa string, motivo string, registro string")


def _ultimo_nao_nulo(coluna: str) -> Column:
    """Valor mais recente não nulo da coluna (por order_ts) dentro de um groupBy."""
    return F.max(
        F.when(F.col(coluna).isNotNull(), F.struct(F.col("order_ts"), F.col(coluna)))
    ).getField(coluna)


# --------------------------------------------------------------------------- #
# Raw -> Silver
# --------------------------------------------------------------------------- #
def read_orders(spark: SparkSession, path: str | Path) -> DataFrame:
    return (
        spark.read.schema(ORDERS_SCHEMA)
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .json(str(path))
    )


def read_products(spark: SparkSession, path: str | Path) -> DataFrame:
    return (
        spark.read.schema(PRODUCTS_SCHEMA)
        .option("header", True)
        .csv(str(path))
        .withColumn("cost", F.round("cost", 2).cast("decimal(12,2)"))
    )


def clean_products(products: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Valida o catálogo. SKU duplicado é ambíguo (multiplicaria linhas da fato num
    join), então todas as linhas daquele SKU vão para quarentena em vez de se escolher uma."""
    colunas = ["sku", "product_name", "category", "subcategory", "brand", "cost"]
    incompleto = F.lit(False)
    for c in colunas:
        incompleto = incompleto | F.col(c).isNull()
    incompleto = incompleto | (F.col("cost") <= 0)

    marcados = products.withColumn("_n", F.count(F.lit(1)).over(Window.partitionBy("sku")))
    invalidos = _rejeitado(marcados.where(incompleto).drop("_n"), "produto_invalido", "catalogo")
    duplicados = _rejeitado(
        marcados.where(~incompleto & (F.col("_n") > 1)).drop("_n"), "sku_duplicado_no_catalogo", "catalogo"
    )
    validos = marcados.where(~incompleto & (F.col("_n") == 1)).drop("_n")
    return validos, invalidos.unionByName(duplicados)


def split_corrupt(raw: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Separa linhas de JSON malformado (quarentena) das linhas parseáveis."""
    raw = raw.cache()  # exigido pelo Spark ao consultar _corrupt_record
    corrompidos = raw.where(F.col("_corrupt_record").isNotNull()).select(
        F.lit("raw").alias("etapa"),
        F.lit("json_malformado").alias("motivo"),
        F.col("_corrupt_record").alias("registro"),
    )
    validos = raw.where(F.col("_corrupt_record").isNull()).drop("_corrupt_record")
    return validos, corrompidos


def clean_orders(orders: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Tipa, normaliza, valida campos obrigatórios e remove pedidos duplicados."""
    tipados = (
        orders.withColumn("order_ts", F.to_timestamp("order_ts"))
        .withColumn("status", F.upper(F.trim("status")))
        .withColumn("channel", F.lower(F.trim("channel")))
    )

    obrigatorio_ausente = (
        F.col("order_id").isNull() | F.col("customer.id").isNull() | F.col("order_ts").isNull()
    )
    # isin() devolve NULL quando status é NULL; coalesce transforma isso em "inválido".
    status_invalido = ~F.coalesce(F.col("status").isin(*STATUS_VALIDOS), F.lit(False))

    invalidos = _rejeitado(tipados.where(obrigatorio_ausente), "campo_obrigatorio_ausente", "pedido")
    invalidos = invalidos.unionByName(
        _rejeitado(tipados.where(~obrigatorio_ausente & status_invalido), "status_invalido", "pedido")
    )
    validos = tipados.where(~obrigatorio_ausente & ~status_invalido)

    # Reenvios: mantém a ocorrência mais recente de cada order_id. O desempate pelo
    # conteúdo serializado torna a escolha determinística quando dois reenvios têm o
    # mesmo order_ts (sem isso o vencedor dependeria da ordem das partições).
    janela = Window.partitionBy("order_id").orderBy(
        F.col("order_ts").desc(), F.to_json(F.struct(*validos.columns)).desc()
    )
    ranqueados = validos.withColumn("_rn", F.row_number().over(janela))
    duplicados = _rejeitado(ranqueados.where("_rn > 1").drop("_rn"), "pedido_duplicado", "pedido")
    unicos = ranqueados.where("_rn = 1").drop("_rn")

    return unicos, invalidos.unionByName(duplicados)


def explode_items(orders: DataFrame) -> DataFrame:
    """Achata o JSON aninhado: uma linha por item de pedido (grão da fato)."""
    planos = orders.select(
        "order_id",
        "order_ts",
        F.to_date("order_ts").alias("order_date"),
        "status",
        "channel",
        F.col("customer.id").alias("customer_id"),
        F.col("customer.name").alias("customer_name"),
        F.col("customer.city").alias("customer_city"),
        F.col("customer.state").alias("customer_state"),
        F.col("customer.segment").alias("customer_segment"),
        F.col("payment.method").alias("payment_method"),
        F.col("payment.installments").alias("installments"),
        # posexplode_outer preserva pedidos sem itens (viram linha com item nulo)
        # e entrega a posição, que compõe a chave do grão: (pedido, item_seq).
        F.posexplode_outer("items").alias("item_seq", "item"),
    )
    return planos.select(
        "*",
        F.col("item.sku").alias("sku"),
        F.col("item.qty").alias("qty"),
        F.round("item.unit_price", 2).cast("decimal(12,2)").alias("unit_price"),
        # Sem cast aqui: decimal(5,4) transformaria valores fora da faixa em NULL em silêncio.
        F.coalesce(F.col("item.discount"), F.lit(0.0)).alias("discount_pct"),
    ).drop("item")


def validate_items(items: DataFrame) -> tuple[DataFrame, DataFrame]:
    invalido = (
        F.col("sku").isNull()
        | F.col("qty").isNull() | (F.col("qty") <= 0)
        | F.col("unit_price").isNull() | (F.col("unit_price") <= 0)
    )
    desconto_fora_da_faixa = ~invalido & ((F.col("discount_pct") < 0) | (F.col("discount_pct") > 1))
    rejeitados = _rejeitado(items.where(invalido), "item_invalido", "item").unionByName(
        _rejeitado(items.where(desconto_fora_da_faixa), "desconto_fora_da_faixa", "item")
    )
    return items.where(~invalido & ~desconto_fora_da_faixa), rejeitados


def check_catalog(items: DataFrame, products: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Garante integridade referencial: SKU precisa existir no catálogo."""
    skus = products.select("sku")
    return (
        items.join(skus, "sku", "left_semi"),
        _rejeitado(items.join(skus, "sku", "left_anti"), "sku_fora_do_catalogo", "item"),
    )


@dataclass
class Silver:
    items: DataFrame
    products: DataFrame
    rejected: DataFrame


def build_silver(spark: SparkSession, raw_dir: str | Path) -> Silver:
    raw_dir = Path(raw_dir)
    raw = read_orders(spark, raw_dir / "orders.jsonl")
    products, rejeitados_catalogo = clean_products(read_products(spark, raw_dir / "products.csv"))

    parseaveis, corrompidos = split_corrupt(raw)
    pedidos, rejeitados_pedido = clean_orders(parseaveis)
    itens, rejeitados_item = validate_items(explode_items(pedidos))
    itens, rejeitados_sku = check_catalog(itens, products)

    rejected = (
        corrompidos.unionByName(rejeitados_pedido)
        .unionByName(rejeitados_item)
        .unionByName(rejeitados_sku)
        .unionByName(rejeitados_catalogo)
    )
    return Silver(items=itens, products=products, rejected=rejected)


# --------------------------------------------------------------------------- #
# Silver -> Gold (modelo estrela)
# --------------------------------------------------------------------------- #
def build_dim_cliente(items: DataFrame) -> DataFrame:
    """SCD tipo 1: mantém o atributo mais recente não nulo de cada cliente."""
    return (
        items.groupBy("customer_id")
        .agg(
            _ultimo_nao_nulo("customer_name").alias("nome"),
            _ultimo_nao_nulo("customer_city").alias("cidade"),
            _ultimo_nao_nulo("customer_state").alias("estado"),
            _ultimo_nao_nulo("customer_segment").alias("segmento"),
        )
        .fillna({"cidade": "Não informada", "estado": "NI", "nome": "Não informado", "segmento": "Não informado"})
        .select(
            surrogate_key("customer_id").alias("cliente_key"),
            F.col("customer_id").alias("cliente_id"),
            "nome", "cidade", "estado", "segmento",
        )
    )


def build_dim_produto(products: DataFrame) -> DataFrame:
    return products.select(
        surrogate_key("sku").alias("produto_key"),
        "sku",
        F.col("product_name").alias("nome"),
        F.col("category").alias("categoria"),
        F.col("subcategory").alias("subcategoria"),
        F.col("brand").alias("marca"),
    )


def build_dim_pagamento(items: DataFrame) -> DataFrame:
    return (
        items.select("payment_method", "installments").distinct()
        .select(
            surrogate_key("payment_method", "installments").alias("pagamento_key"),
            F.col("payment_method").alias("metodo"),
            F.col("installments").alias("parcelas"),
        )
    )


def build_dim_canal(items: DataFrame) -> DataFrame:
    return items.select("channel").distinct().select(
        surrogate_key("channel").alias("canal_key"),
        F.col("channel").alias("canal"),
    )


def build_dim_data(spark: SparkSession, items: DataFrame) -> DataFrame:
    """Dimensão de calendário sem lacunas, do primeiro ao último dia observado."""
    limites = items.agg(F.min("order_date").alias("ini"), F.max("order_date").alias("fim"))
    dias = limites.select(
        F.explode(F.sequence("ini", "fim", F.expr("interval 1 day"))).alias("data")
    )
    nomes_meses = F.array(*[F.lit(m) for m in MESES])
    nomes_dias = F.array(*[F.lit(d) for d in DIAS])
    dow = F.dayofweek("data")  # 1 = domingo
    return dias.select(
        F.date_format("data", "yyyyMMdd").cast("int").alias("date_key"),
        "data",
        F.year("data").alias("ano"),
        F.quarter("data").alias("trimestre"),
        F.month("data").alias("mes"),
        F.element_at(nomes_meses, F.month("data")).alias("nome_mes"),
        F.dayofmonth("data").alias("dia"),
        F.element_at(nomes_dias, dow).alias("dia_semana"),
        dow.isin(1, 7).alias("fim_de_semana"),
    )


def build_fato_vendas(items: DataFrame, products: DataFrame) -> DataFrame:
    """Fato no grão de item de pedido. Cancelados ficam fora (regra de negócio)."""
    d2 = lambda c: F.round(c, 2).cast("decimal(14,2)")  # noqa: E731
    base = (
        items.where(F.col("status") != STATUS_EXCLUIDO_DA_FATO)
        .join(products.select("sku", "cost"), "sku")
        .withColumn("discount_pct", F.col("discount_pct").cast("decimal(5,4)"))
        .withColumn("valor_bruto", d2(F.col("qty") * F.col("unit_price")))
        .withColumn("valor_desconto", d2(F.col("valor_bruto") * F.col("discount_pct")))
        .withColumn("valor_liquido", d2(F.col("valor_bruto") - F.col("valor_desconto")))
        .withColumn("custo_total", d2(F.col("qty") * F.col("cost")))
    )
    return base.select(
        F.col("order_id").alias("pedido_id"),
        F.col("item_seq").cast("int"),
        F.date_format("order_date", "yyyyMMdd").cast("int").alias("date_key"),
        surrogate_key("customer_id").alias("cliente_key"),
        surrogate_key("sku").alias("produto_key"),
        surrogate_key("payment_method", "installments").alias("pagamento_key"),
        surrogate_key("channel").alias("canal_key"),
        F.col("qty").cast("int").alias("quantidade"),
        F.col("unit_price").alias("preco_unitario"),
        F.col("discount_pct").alias("desconto_pct"),
        "valor_bruto",
        "valor_desconto",
        "valor_liquido",
        "custo_total",
        d2(F.col("valor_liquido") - F.col("custo_total")).alias("margem"),
        F.date_format("order_date", "yyyy-MM").alias("ano_mes"),
    )


def build_gold(spark: SparkSession, silver: Silver) -> dict[str, DataFrame]:
    return {
        "dim_data": build_dim_data(spark, silver.items),
        "dim_cliente": build_dim_cliente(silver.items),
        "dim_produto": build_dim_produto(silver.products),
        "dim_pagamento": build_dim_pagamento(silver.items),
        "dim_canal": build_dim_canal(silver.items),
        "fato_vendas": build_fato_vendas(silver.items, silver.products),
    }


# --------------------------------------------------------------------------- #
# Qualidade do modelo
# --------------------------------------------------------------------------- #
FOREIGN_KEYS = {
    "date_key": "dim_data",
    "cliente_key": "dim_cliente",
    "produto_key": "dim_produto",
    "pagamento_key": "dim_pagamento",
    "canal_key": "dim_canal",
}


def validate_star(gold: dict[str, DataFrame]) -> dict[str, int]:
    """Verificações estruturais do modelo. Devolve contagens de violações (0 = ok).

    Atenção ao que cada uma prova: como as chaves da fato e das dimensões vêm do mesmo
    hash dos mesmos dados, ``orfaos_*`` é zero *por construção* enquanto o código de
    derivação for consistente. Ele detecta regressão no código (alguém mudar o hash de um
    lado só), não problema nos dados. As garantias que dependem dos dados são grão único,
    chave única nas dimensões e, em :func:`reconcile`, a conferência contra a silver.
    A integridade referencial "de verdade" é imposta pelas FKs do PostgreSQL na carga.
    """
    fato = gold["fato_vendas"]
    violacoes: dict[str, int] = {}
    for coluna, dimensao in FOREIGN_KEYS.items():
        violacoes[f"orfaos_{coluna}"] = fato.join(gold[dimensao], coluna, "left_anti").count()
    violacoes["grao_duplicado"] = (
        fato.groupBy("pedido_id", "item_seq").count().where("count > 1").count()
    )
    for nome, chave in [("dim_cliente", "cliente_key"), ("dim_produto", "produto_key"),
                        ("dim_pagamento", "pagamento_key"), ("dim_canal", "canal_key"),
                        ("dim_data", "date_key")]:
        violacoes[f"chave_duplicada_{nome}"] = (
            gold[nome].groupBy(chave).count().where("count > 1").count()
        )
    return violacoes


def reconcile(items: DataFrame, gold: dict[str, DataFrame]) -> dict[str, int]:
    """Confere a gold contra a silver com expressões independentes das usadas para construí-la.

    Devolve divergências (0 = ok). Esta é a verificação que pega perda silenciosa de linhas
    ou erro de cálculo: a receita esperada é recalculada em ``double`` a partir de
    ``qty * unit_price * (1 - desconto)``, enquanto a fato usa decimais arredondados por linha.
    """
    fato = gold["fato_vendas"]
    esperado = items.where(F.coalesce(F.col("status") != STATUS_EXCLUIDO_DA_FATO, F.lit(False)))
    esp = esperado.agg(
        F.count(F.lit(1)).alias("linhas"),
        F.sum(F.col("qty") * F.col("unit_price").cast("double") * (1 - F.col("discount_pct"))).alias("valor"),
    ).first()
    obt = fato.agg(F.count(F.lit(1)).alias("linhas"), F.sum("valor_liquido").cast("double").alias("valor")).first()

    # O arredondamento a 2 casas por linha pode deslocar no máximo meio centavo por linha.
    tolerancia = 0.005 * (esp["linhas"] or 0) + 1.0
    divergencia_valor = abs((esp["valor"] or 0.0) - (obt["valor"] or 0.0)) > tolerancia

    limites = items.agg(F.min("order_date").alias("ini"), F.max("order_date").alias("fim")).first()
    dias_esperados = (limites["fim"] - limites["ini"]).days + 1 if limites["ini"] else 0

    return {
        "divergencia_linhas": abs(esp["linhas"] - obt["linhas"]),
        "divergencia_valor": int(divergencia_valor),
        "divergencia_clientes": abs(items.select("customer_id").distinct().count() - gold["dim_cliente"].count()),
        "divergencia_dias": abs(dias_esperados - gold["dim_data"].count()),
    }
