"""Schemas explícitos da camada raw.

Ler JSON sem schema obriga o Spark a varrer os arquivos para inferir tipos,
e deixa a pipeline à mercê de qualquer mudança na origem. Com schema explícito
o contrato fica documentado no código e registros malformados caem em
``_corrupt_record`` em vez de derrubar o job.
"""

from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

ORDERS_SCHEMA = StructType(
    [
        StructField("order_id", StringType()),
        StructField("order_ts", StringType()),
        StructField("status", StringType()),
        StructField("channel", StringType()),
        StructField(
            "customer",
            StructType(
                [
                    StructField("id", StringType()),
                    StructField("name", StringType()),
                    StructField("city", StringType()),
                    StructField("state", StringType()),
                    StructField("segment", StringType()),
                ]
            ),
        ),
        StructField(
            "payment",
            StructType(
                [
                    StructField("method", StringType()),
                    StructField("installments", LongType()),
                ]
            ),
        ),
        StructField(
            "items",
            ArrayType(
                StructType(
                    [
                        StructField("sku", StringType()),
                        StructField("qty", LongType()),
                        StructField("unit_price", DoubleType()),
                        StructField("discount", DoubleType()),
                    ]
                )
            ),
        ),
        # Recebe a linha original quando o JSON está quebrado (modo PERMISSIVE).
        StructField("_corrupt_record", StringType()),
    ]
)

PRODUCTS_SCHEMA = StructType(
    [
        StructField("sku", StringType()),
        StructField("product_name", StringType()),
        StructField("category", StringType()),
        StructField("subcategory", StringType()),
        StructField("brand", StringType()),
        StructField("cost", DoubleType()),
    ]
)
