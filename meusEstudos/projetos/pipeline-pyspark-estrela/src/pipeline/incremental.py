"""Carga incremental: processa só os lotes novos e aplica as mudanças no DW com MERGE.

A carga completa (``run_pipeline``) reprocessa tudo a cada execução. Aqui cada lote diário é
tratado uma única vez e **mescla** o resultado no modelo estrela, o que exige resolver o que
a carga completa nunca enfrenta:

* **Pedido reenviado com mudança** (status novo, item corrigido): ``MERGE ... WHEN MATCHED``
  atualiza a linha em vez de duplicar.
* **Cancelamento tardio**: o pedido cancelado não está mais na fato (regra de negócio), então
  as linhas que ele tinha são **removidas** (DELETE) na mesma transação.
* **Item removido de um pedido**: idem, a linha que sumiu do pedido é removida.
* **Idempotência**: rodar o mesmo lote duas vezes deixa o DW exatamente igual.
* **Um escritor por vez**: uma trava (advisory lock) no banco impede duas cargas simultâneas no mesmo schema.
* **Atomicidade**: staging + uma transação (remoções, MERGEs, tabela de controle e uma
  verificação final antes do commit). Se algo falhar, o DW fica como estava e o lote
  continua pendente.

O controle do que já foi processado fica na tabela ``controle_cargas`` (lote + checksum do
arquivo), no próprio banco e na mesma transação do MERGE: o registro e os dados nunca divergem.

Uso:
    python -m pipeline.incremental --lotes data/raw_inc/lotes --produtos data/raw_inc/products.csv
    python -m pipeline.incremental ... --schema dw_inc      # schema próprio, criado do DDL se preciso
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from pipeline.load_postgres import POSTGRES_DRIVER, _conexao, _executar_em_transacao, consultar_inteiro
from pipeline.modelo import CHAVES, COLUNAS, ORDEM_DE_CARGA
from pipeline.spark_session import get_spark
from pipeline.transform import (
    build_dim_canal,
    build_dim_cliente,
    build_dim_data,
    build_dim_pagamento,
    build_dim_produto,
    build_fato_vendas,
    build_silver_from_orders,
    clean_products,
    read_products,
)

log = logging.getLogger("incremental")

ID_VALIDO = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")  # nome de lote (arquivo)
NOME_SQL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,40}$")  # schema e staging, interpolados em SQL

# Um valor "não informado" vindo de um lote novo não pode apagar um atributo já conhecido.
ATUALIZACAO_CLIENTE = {
    "nome": "CASE WHEN s.nome = 'Não informado' THEN t.nome ELSE s.nome END",
    "cidade": "CASE WHEN s.cidade = 'Não informada' THEN t.cidade ELSE s.cidade END",
    "estado": "CASE WHEN s.estado = 'NI' THEN t.estado ELSE s.estado END",
    "segmento": "CASE WHEN s.segmento = 'Não informado' THEN t.segmento ELSE s.segmento END",
}
ATUALIZACAO_PRODUTO = {c: f"s.{c}" for c in ("nome", "categoria", "subcategoria", "marca")}
ATUALIZACAO_FATO = {c: f"s.{c}" for c in COLUNAS["fato_vendas"] if c not in CHAVES["fato_vendas"]}


def _validar_nome(nome: str, o_que: str = "identificador") -> str:
    if not NOME_SQL.match(nome):
        raise ValueError(f"{o_que.capitalize()} inválido: {nome!r}")
    return nome


# --------------------------------------------------------------------------- #
# SQL (funções puras: testáveis sem banco)
# --------------------------------------------------------------------------- #
def _juncao(tabela: str) -> str:
    return " AND ".join(f"t.{c} = s.{c}" for c in CHAVES[tabela])


def sql_merge_inserir(schema: str, stage: str, tabela: str) -> str:
    """Dimensões imutáveis (data, pagamento, canal): só insere o que ainda não existe."""
    colunas = COLUNAS[tabela]
    return (
        f"MERGE INTO {schema}.{tabela} AS t USING {stage}.{tabela} AS s ON {_juncao(tabela)} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(colunas)}) VALUES ({', '.join('s.' + c for c in colunas)})"
    )


def sql_merge_atualizar(schema: str, stage: str, tabela: str, atribuicoes: dict[str, str]) -> str:
    """Insere o que é novo e atualiza o que mudou. ``IS DISTINCT FROM`` evita reescrever linhas
    idênticas, o que torna o reprocessamento um no-op de verdade."""
    colunas = COLUNAS[tabela]
    atuais = ", ".join(f"t.{c}" for c in atribuicoes)
    novos = ", ".join(atribuicoes.values())
    sets = ", ".join(f"{c} = {expr}" for c, expr in atribuicoes.items())
    return (
        f"MERGE INTO {schema}.{tabela} AS t USING {stage}.{tabela} AS s ON {_juncao(tabela)} "
        f"WHEN MATCHED AND ({atuais}) IS DISTINCT FROM ({novos}) THEN UPDATE SET {sets} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(colunas)}) VALUES ({', '.join('s.' + c for c in colunas)})"
    )


def _condicao_remocao(schema: str, stage: str) -> str:
    return (
        f"f.pedido_id IN (SELECT pedido_id FROM {stage}.pedidos_lote) "
        f"AND NOT EXISTS (SELECT 1 FROM {stage}.fato_vendas s "
        f"WHERE s.pedido_id = f.pedido_id AND s.item_seq = f.item_seq)"
    )


def sql_remocoes(schema: str, stage: str) -> str:
    """Remove da fato as linhas de pedidos do lote que não existem mais na versão nova: pedido
    cancelado (sai da fato por regra de negócio) ou item retirado do pedido."""
    return f"DELETE FROM {schema}.fato_vendas f WHERE {_condicao_remocao(schema, stage)}"


def sql_contar_remocoes(schema: str, stage: str) -> str:
    return f"SELECT count(*) FROM {schema}.fato_vendas f WHERE {_condicao_remocao(schema, stage)}"


def sql_contar_inseridas(schema: str, stage: str) -> str:
    return (
        f"SELECT count(*) FROM {stage}.fato_vendas s WHERE NOT EXISTS "
        f"(SELECT 1 FROM {schema}.fato_vendas t WHERE {_juncao('fato_vendas')})"
    )


def sql_contar_atualizadas(schema: str, stage: str) -> str:
    atuais = ", ".join(f"t.{c}" for c in ATUALIZACAO_FATO)
    novos = ", ".join(ATUALIZACAO_FATO.values())
    return (
        f"SELECT count(*) FROM {stage}.fato_vendas s JOIN {schema}.fato_vendas t ON {_juncao('fato_vendas')} "
        f"WHERE ({atuais}) IS DISTINCT FROM ({novos})"
    )


def sql_registrar_lote(schema: str, lote: str, checksum: str, relatorio: dict[str, int]) -> str:
    # lote e checksum são validados antes (regex / hexadecimal), então a interpolação é segura.
    return (
        f"INSERT INTO {schema}.controle_cargas "
        f"(lote, checksum, itens_validos, fato_inseridas, fato_atualizadas, fato_removidas, rejeitados, processado_em) "
        f"VALUES ('{lote}', '{checksum}', {relatorio['itens_validos']}, {relatorio['fato_inseridas']}, "
        f"{relatorio['fato_atualizadas']}, {relatorio['fato_removidas']}, {relatorio['rejeitados']}, now()) "
        f"ON CONFLICT (lote) DO UPDATE SET checksum = EXCLUDED.checksum, itens_validos = EXCLUDED.itens_validos, "
        f"fato_inseridas = EXCLUDED.fato_inseridas, fato_atualizadas = EXCLUDED.fato_atualizadas, "
        f"fato_removidas = EXCLUDED.fato_removidas, rejeitados = EXCLUDED.rejeitados, processado_em = now()"
    )


def sql_criar_controle(schema: str) -> str:
    return (
        f"CREATE TABLE IF NOT EXISTS {schema}.controle_cargas ("
        "lote VARCHAR(80) PRIMARY KEY, checksum CHAR(64) NOT NULL, itens_validos INTEGER NOT NULL, "
        "fato_inseridas INTEGER NOT NULL, fato_atualizadas INTEGER NOT NULL, fato_removidas INTEGER NOT NULL, "
        "rejeitados INTEGER NOT NULL, processado_em TIMESTAMPTZ NOT NULL DEFAULT now())"
    )


def comandos_de_mescla(schema: str, stage: str) -> list[str]:
    """Ordem importa: remoções e dimensões antes da fato (a fato referencia as dimensões)."""
    return [
        sql_remocoes(schema, stage),
        sql_merge_inserir(schema, stage, "dim_data"),
        sql_merge_atualizar(schema, stage, "dim_cliente", ATUALIZACAO_CLIENTE),
        sql_merge_atualizar(schema, stage, "dim_produto", ATUALIZACAO_PRODUTO),
        sql_merge_inserir(schema, stage, "dim_pagamento"),
        sql_merge_inserir(schema, stage, "dim_canal"),
        sql_merge_atualizar(schema, stage, "fato_vendas", ATUALIZACAO_FATO),
    ]


# --------------------------------------------------------------------------- #
# Orquestração de lotes
# --------------------------------------------------------------------------- #
def sha256_arquivo(arquivo: Path) -> str:
    h = hashlib.sha256()
    with arquivo.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def listar_lotes(pasta: str | Path) -> list[Path]:
    """Lotes em ordem de nome. A ordem é a ordem de chegada: em reenvios, o último vence."""
    return sorted(Path(pasta).glob("*.jsonl"))


def criar_modelo(spark: SparkSession, schema: str, ddl: str | Path) -> None:
    """Cria o modelo estrela em ``schema`` a partir do DDL do projeto (que usa o schema ``dw``).

    Uma única definição do modelo serve a todos os schemas: o nome é trocado no texto do DDL.
    """
    _validar_nome(schema, "schema")
    texto = re.sub(r"\bdw\b", schema, Path(ddl).read_text(encoding="utf-8"))
    _executar_em_transacao(spark, [texto])


def _schema_existe(spark: SparkSession, schema: str) -> bool:
    return consultar_inteiro(
        spark, f"SELECT count(*) FROM information_schema.schemata WHERE schema_name = '{schema}'"
    ) > 0


@contextmanager
def trava_do_schema(spark: SparkSession, schema: str):
    """Impede duas cargas incrementais simultâneas no mesmo schema (advisory lock do PostgreSQL).

    O staging é compartilhado: dois escritores ao mesmo tempo misturariam os dados dos dois lotes, e o
    controle registraria um lote com dados do outro. O ``max_active_runs=1`` da DAG não protege contra uma
    execução manual junto com a agendada; esta trava, que vive no banco, protege. É de sessão: fechar a
    conexão (inclusive se o processo morrer) libera a trava.
    """
    _validar_nome(schema, "schema")
    url, usuario, senha = _conexao()
    jvm = spark._jvm  # noqa: SLF001
    jvm.java.lang.Class.forName(POSTGRES_DRIVER)
    conexao = jvm.java.sql.DriverManager.getConnection(url, usuario, senha)
    try:
        resultado = conexao.createStatement().executeQuery(f"SELECT pg_try_advisory_lock(hashtext('incremental:{schema}'))")
        resultado.next()
        if not resultado.getBoolean(1):
            raise RuntimeError(f"Outra carga incremental já está em execução no schema {schema!r}.")
        yield
    finally:
        conexao.close()


def preparar_banco(spark: SparkSession, schema: str, stage: str, ddl: str | Path | None = None) -> None:
    """Garante o modelo, a tabela de controle e as tabelas de staging. Idempotente."""
    _validar_nome(schema, "schema"), _validar_nome(stage, "schema de staging")
    if not _schema_existe(spark, schema):
        if ddl is None:
            raise RuntimeError(f"O schema {schema!r} não existe e nenhum DDL foi informado para criá-lo.")
        log.info("Criando o modelo estrela no schema %s", schema)
        criar_modelo(spark, schema, ddl)
    comandos = [f"CREATE SCHEMA IF NOT EXISTS {stage}", sql_criar_controle(schema)]
    comandos += [f"CREATE TABLE IF NOT EXISTS {stage}.{t} (LIKE {schema}.{t} INCLUDING DEFAULTS)" for t in ORDEM_DE_CARGA]
    comandos.append(f"CREATE TABLE IF NOT EXISTS {stage}.pedidos_lote (pedido_id VARCHAR(20) NOT NULL)")
    _executar_em_transacao(spark, comandos)


def _ler_controle(spark: SparkSession, schema: str) -> dict[str, str]:
    url, usuario, senha = _conexao()
    linhas = (
        spark.read.format("jdbc")
        .option("url", url)
        .option("query", f"SELECT lote, checksum FROM {schema}.controle_cargas")
        .option("user", usuario)
        .option("password", senha)
        .option("driver", "org.postgresql.Driver")
        .load()
        .collect()
    )
    return {r["lote"]: r["checksum"].strip() for r in linhas}


def lotes_pendentes(spark: SparkSession, arquivos: list[Path], schema: str = "dw") -> list[Path]:
    """Lote é pendente se nunca foi processado ou se o arquivo mudou desde então (checksum diferente)."""
    processados = _ler_controle(spark, schema)
    return [a for a in arquivos if processados.get(a.stem) != sha256_arquivo(a)]


def _gravar_stage(spark: SparkSession, df: DataFrame, tabela: str, stage: str) -> None:
    url, usuario, senha = _conexao()
    (
        df.write.format("jdbc")
        .option("url", url)
        .option("dbtable", f"{stage}.{tabela}")
        .option("user", usuario)
        .option("password", senha)
        .option("driver", "org.postgresql.Driver")
        .option("truncate", "true")  # staging não tem PK/FK: truncar é seguro
        .option("batchsize", 10_000)
        .mode("overwrite")
        .save()
    )


def processar_lote(
    spark: SparkSession,
    arquivo: Path,
    produtos: DataFrame,
    schema: str = "dw",
    stage: str = "stage_inc",
    rejeitados_dir: Path | None = None,
) -> dict:
    """Processa um lote: silver → gold do lote → staging → transação com MERGE. Devolve o relatório."""
    lote = arquivo.stem
    if not ID_VALIDO.match(lote):
        raise ValueError(f"Nome de lote inválido: {lote!r}")
    _validar_nome(schema, "schema"), _validar_nome(stage, "schema de staging")
    checksum = sha256_arquivo(arquivo)
    inicio = time.perf_counter()

    # O cache do Spark (df.cache() em split_corrupt) é indexado pelo PLANO lógico: reler o mesmo caminho
    # com o mesmo schema devolveria o cache anterior mesmo que o arquivo tenha sido reescrito (lote
    # reenviado com conteúdo novo), e o checksum registrado seria o do arquivo novo com dados velhos.
    spark.catalog.refreshByPath(str(arquivo))
    try:
        return _processar(spark, arquivo, lote, checksum, inicio, produtos, schema, stage, rejeitados_dir)
    finally:
        spark.catalog.clearCache()  # libera os caches do lote: sem isso a memória cresce a cada lote


def _processar(
    spark: SparkSession, arquivo: Path, lote: str, checksum: str, inicio: float,
    produtos: DataFrame, schema: str, stage: str, rejeitados_dir: Path | None,
) -> dict:
    silver = build_silver_from_orders(spark, arquivo, produtos)
    itens = silver.items.cache()
    itens_validos = itens.count()
    rejeitados = silver.rejected.count()
    if rejeitados_dir is not None and rejeitados:
        silver.rejected.write.mode("overwrite").parquet(str(Path(rejeitados_dir) / f"lote={lote}"))

    tabelas = {
        "dim_data": build_dim_data(spark, itens),
        "dim_cliente": build_dim_cliente(itens),
        "dim_produto": build_dim_produto(produtos),
        "dim_pagamento": build_dim_pagamento(itens),
        "dim_canal": build_dim_canal(itens),
        "fato_vendas": build_fato_vendas(itens, produtos),
    }
    # TODOS os pedidos válidos do arquivo, inclusive os sem nenhum item válido: um pedido reenviado cujos
    # itens foram todos rejeitados precisa ter suas linhas antigas removidas da fato (a versão nova não tem
    # nenhuma linha válida). Pedido com cabeçalho inválido continua intocado: não dá para confiar no id.
    pedidos = silver.pedidos.select(F.col("order_id").alias("pedido_id")).distinct()

    for nome, df in tabelas.items():
        _gravar_stage(spark, df, nome, stage)
    _gravar_stage(spark, pedidos, "pedidos_lote", stage)
    itens.unpersist()

    # Medidas do que o MERGE vai fazer, calculadas antes (informativas; a garantia é a verificação abaixo).
    na_fato_do_lote = consultar_inteiro(spark, f"SELECT count(*) FROM {stage}.fato_vendas")
    valor_do_lote = consultar_inteiro(spark, f"SELECT COALESCE(CAST(ROUND(SUM(valor_liquido) * 100) AS BIGINT), 0) FROM {stage}.fato_vendas")
    relatorio = {
        "lote": lote,
        "itens_validos": itens_validos,
        "rejeitados": rejeitados,
        "fato_inseridas": consultar_inteiro(spark, sql_contar_inseridas(schema, stage)),
        "fato_atualizadas": consultar_inteiro(spark, sql_contar_atualizadas(schema, stage)),
        "fato_removidas": consultar_inteiro(spark, sql_contar_remocoes(schema, stage)),
    }

    # Tudo ou nada. A verificação roda antes do commit: depois do MERGE, as linhas dos pedidos do
    # lote que estão no DW têm de ser exatamente as da versão nova (mesma contagem e mesmo valor total).
    _executar_em_transacao(
        spark,
        comandos_de_mescla(schema, stage) + [sql_registrar_lote(schema, lote, checksum, relatorio)],
        verificacoes=[
            # contagem E valor: só a contagem não pegaria uma linha com o valor errado
            (
                f"SELECT count(*) FROM {schema}.fato_vendas f WHERE f.pedido_id IN (SELECT pedido_id FROM {stage}.pedidos_lote)",
                na_fato_do_lote,
            ),
            (
                f"SELECT COALESCE(CAST(ROUND(SUM(f.valor_liquido) * 100) AS BIGINT), 0) FROM {schema}.fato_vendas f "
                f"WHERE f.pedido_id IN (SELECT pedido_id FROM {stage}.pedidos_lote)",
                valor_do_lote,
            ),
        ],
    )
    relatorio["segundos"] = round(time.perf_counter() - inicio, 1)
    return relatorio


def run_incremental(
    spark: SparkSession,
    lotes_dir: str | Path,
    produtos_csv: str | Path,
    schema: str = "dw",
    stage: str | None = None,
    rejeitados_dir: Path | None = None,
    max_lotes: int | None = None,
    reprocessar: bool = False,
    ddl: str | Path | None = None,
) -> list[dict]:
    """Processa os lotes pendentes em ordem. Para no primeiro erro: lotes seguintes dependem do anterior."""
    stage = stage or f"stage_{schema}"
    with trava_do_schema(spark, schema):
        preparar_banco(spark, schema, stage, ddl)
        produtos, _ = clean_products(read_products(spark, produtos_csv))  # catálogo pequeno: relido a cada lote

        arquivos = listar_lotes(lotes_dir)
        pendentes = arquivos if reprocessar else lotes_pendentes(spark, arquivos, schema)
        if max_lotes is not None:
            pendentes = pendentes[:max_lotes]
        log.info("%d lote(s) encontrado(s), %d pendente(s)", len(arquivos), len(pendentes))

        relatorios = []
        for arquivo in pendentes:
            relatorio = processar_lote(spark, arquivo, produtos, schema, stage, rejeitados_dir)
            log.info(
                "lote %s: +%d inseridas, ~%d atualizadas, -%d removidas, %d rejeitados (%.1fs)",
                relatorio["lote"], relatorio["fato_inseridas"], relatorio["fato_atualizadas"],
                relatorio["fato_removidas"], relatorio["rejeitados"], relatorio["segundos"],
            )
            relatorios.append(relatorio)
    return relatorios


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lotes", type=Path, default=Path("data/raw_inc/lotes"))
    parser.add_argument("--produtos", type=Path, default=Path("data/raw_inc/products.csv"))
    parser.add_argument("--rejeitados", type=Path, default=Path("data/incremental/rejeitados"))
    parser.add_argument("--schema", default="dw", help="schema do DW (criado a partir do DDL se não existir)")
    parser.add_argument("--ddl", type=Path, default=Path(os.getenv("PIPELINE_DDL", "sql/01_ddl_estrela.sql")))
    parser.add_argument("--max-lotes", type=int, default=None, help="processa no máximo N lotes pendentes")
    parser.add_argument("--reprocessar", action="store_true", help="ignora o controle e reaplica todos os lotes (idempotente)")
    args = parser.parse_args()

    spark = get_spark("incremental")
    try:
        relatorios = run_incremental(
            spark, args.lotes, args.produtos, schema=args.schema, rejeitados_dir=args.rejeitados,
            max_lotes=args.max_lotes, reprocessar=args.reprocessar, ddl=args.ddl,
        )
    finally:
        spark.stop()
    if not relatorios:
        log.info("Nada a processar: todos os lotes já foram carregados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
