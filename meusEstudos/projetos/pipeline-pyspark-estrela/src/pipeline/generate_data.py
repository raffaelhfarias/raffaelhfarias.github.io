"""Gerador de dados sintéticos de e-commerce (determinístico por seed).

Produz:
  - ``orders.jsonl``  : pedidos semiestruturados (JSON aninhado, itens em array)
  - ``products.csv``  : catálogo de produtos

Os dados são sintéticos de propósito: nada de empresa real, e o volume é
ajustável (``--orders 5000000`` para exercitar o paralelismo do Spark).
São injetados problemas realistas para que a camada de qualidade tenha o que
tratar: duplicatas, JSON truncado, itens inválidos, SKU fora do catálogo,
status em caixa mista e cidades nulas.

Uso:
    python -m pipeline.generate_data --orders 200000 --out data/raw      # arquivo único
    python -m pipeline.generate_data --lotes 5 --out data/raw_inc        # lotes diários com atualizações
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

CATEGORIAS = {
    "Eletrônicos": ["Smartphones", "Notebooks", "Acessórios", "Áudio"],
    "Casa": ["Cozinha", "Decoração", "Móveis", "Limpeza"],
    "Moda": ["Camisetas", "Calçados", "Bolsas", "Relógios"],
    "Esporte": ["Fitness", "Ciclismo", "Camping"],
    "Livros": ["Técnicos", "Ficção", "Infantil"],
}
MARCAS = ["Aurora", "Nimbus", "Vértice", "Orbita", "Folha", "Prisma", "Atlas", "Cobalto"]
CIDADES = [
    ("Recife", "PE"), ("Olinda", "PE"), ("Caruaru", "PE"), ("Salvador", "BA"),
    ("Fortaleza", "CE"), ("São Paulo", "SP"), ("Campinas", "SP"), ("Rio de Janeiro", "RJ"),
    ("Belo Horizonte", "MG"), ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Brasília", "DF"),
]
SEGMENTOS = ["varejo", "premium", "corporativo"]
CANAIS = ["site", "app", "marketplace", "loja_fisica"]
PAGAMENTOS = [("cartao_credito", 0.55), ("pix", 0.25), ("boleto", 0.12), ("cartao_debito", 0.08)]
STATUS = [("ENTREGUE", 0.70), ("ENVIADO", 0.12), ("PAGO", 0.08), ("CANCELADO", 0.10)]
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Hugo", "Iara", "João",
         "Karina", "Lucas", "Marina", "Nelson", "Olívia", "Paulo", "Rafaela", "Sérgio", "Tânia", "Vitor"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Almeida", "Ribeiro", "Barros"]

DATA_INICIO = datetime(2024, 1, 1)
DATA_FIM = datetime(2025, 12, 31, 23, 59, 59)


def _escolha_ponderada(rng: random.Random, opcoes: list[tuple[str, float]]) -> str:
    return rng.choices([o for o, _ in opcoes], weights=[p for _, p in opcoes])[0]


def gerar_produtos(rng: random.Random, n: int = 500) -> list[dict]:
    produtos = []
    for i in range(1, n + 1):
        categoria = rng.choice(list(CATEGORIAS))
        custo = round(rng.uniform(8, 1800), 2)
        produtos.append(
            {
                "sku": f"SKU{i:05d}",
                "product_name": f"Produto {i:05d}",
                "category": categoria,
                "subcategory": rng.choice(CATEGORIAS[categoria]),
                "brand": rng.choice(MARCAS),
                "cost": custo,
            }
        )
    return produtos


def gerar_clientes(rng: random.Random, n: int) -> list[dict]:
    clientes = []
    for i in range(1, n + 1):
        cidade, uf = rng.choice(CIDADES)
        clientes.append(
            {
                "id": f"C{i:06d}",
                "name": f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}",
                "city": cidade,
                "state": uf,
                "segment": rng.choices(SEGMENTOS, weights=[0.8, 0.12, 0.08])[0],
            }
        )
    return clientes


def gerar_pedido(
    rng: random.Random,
    n_pedido: int,
    clientes: list[dict],
    produtos: list[dict],
    dia: datetime | None = None,
) -> dict:
    """``dia`` fixa a data do pedido (usado nos lotes diários); sem ele, sorteia em 2024-2025."""
    if dia is None:
        segundos = int((DATA_FIM - DATA_INICIO).total_seconds())
        ts = DATA_INICIO + timedelta(seconds=rng.randint(0, segundos))
    else:
        ts = dia + timedelta(seconds=rng.randint(0, 86399))
    cliente = dict(rng.choice(clientes))
    if rng.random() < 0.02:  # cidade ausente
        cliente["city"] = None

    itens = []
    for _ in range(rng.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]):
        produto = rng.choice(produtos)
        preco = round(produto["cost"] * rng.uniform(1.15, 1.9), 2)
        itens.append(
            {
                "sku": produto["sku"],
                "qty": rng.choices([1, 2, 3, 5], weights=[0.7, 0.18, 0.08, 0.04])[0],
                "unit_price": preco,
                "discount": rng.choice([0.0, 0.0, 0.0, 0.05, 0.1, 0.15, 0.2]),
            }
        )

    # Problemas de qualidade controlados
    if itens and rng.random() < 0.005:
        itens[0]["qty"] = rng.choice([0, -1])  # quantidade inválida
    if itens and rng.random() < 0.003:
        itens[-1]["sku"] = "SKU99999"  # fora do catálogo

    status = _escolha_ponderada(rng, STATUS)
    if rng.random() < 0.01:
        status = status.lower()  # caixa mista na origem

    metodo = _escolha_ponderada(rng, PAGAMENTOS)
    parcelas = rng.choice([1, 2, 3, 6, 10, 12]) if metodo == "cartao_credito" else 1

    return {
        "order_id": f"O{n_pedido:09d}",
        "order_ts": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": status,
        "channel": rng.choice(CANAIS),
        "customer": cliente,
        "payment": {"method": metodo, "installments": parcelas},
        "items": itens,
    }


def gerar(orders: int, out: Path, seed: int = 42) -> dict[str, int]:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    produtos = gerar_produtos(rng)
    clientes = gerar_clientes(rng, max(1000, orders // 10))

    with (out / "products.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(produtos[0]))
        writer.writeheader()
        writer.writerows(produtos)

    linhas = duplicadas = truncadas = 0
    with (out / "orders.jsonl").open("w", encoding="utf-8") as f:
        for n in range(1, orders + 1):
            linha = json.dumps(gerar_pedido(rng, n, clientes, produtos), ensure_ascii=False)
            roll = rng.random()
            if roll < 0.001:  # JSON truncado
                linha = linha[: len(linha) // 2]
                truncadas += 1
            f.write(linha + "\n")
            linhas += 1
            if roll > 0.99:  # reenvio duplicado do mesmo pedido
                f.write(linha + "\n")
                linhas += 1
                duplicadas += 1
    return {"linhas": linhas, "duplicadas": duplicadas, "truncadas": truncadas, "produtos": len(produtos)}


# --------------------------------------------------------------------------- #
# Lotes diários com atualizações (para a carga incremental)
# --------------------------------------------------------------------------- #
STATUS_ATUALIZAVEIS = ["PAGO", "ENVIADO", "ENTREGUE"]


def atualizar_pedido(rng: random.Random, pedido: dict) -> dict:
    """Versão atualizada de um pedido já enviado: o mesmo ``order_id`` e ``order_ts`` com algo alterado.

    Modela o que acontece de verdade em sistemas transacionais: o pedido avança de status,
    é cancelado depois de enviado, perde um item ou tem quantidade/desconto corrigido.
    """
    novo = json.loads(json.dumps(pedido))  # cópia profunda
    sorteio = rng.random()
    if sorteio < 0.15 and len(novo["items"]) > 1:
        novo["items"].pop()  # item removido do pedido
    elif sorteio < 0.30:
        novo["status"] = "CANCELADO"  # cancelamento tardio
    elif sorteio < 0.50 and novo["items"]:
        item = novo["items"][0]  # correção de valor: é o que muda a linha da fato (UPDATE no MERGE)
        if rng.random() < 0.5:
            item["qty"] = int(item["qty"]) + 1
        else:
            item["discount"] = 0.05 if float(item["discount"]) != 0.05 else 0.1
    else:
        atual = str(novo["status"]).upper()
        opcoes = [s for s in STATUS_ATUALIZAVEIS if s != atual] or STATUS_ATUALIZAVEIS
        novo["status"] = rng.choice(opcoes)
    return novo


def gerar_lotes(
    lotes: int, pedidos_por_lote: int, out: Path, seed: int = 42, inicio: datetime = datetime(2025, 1, 1)
) -> dict[str, int]:
    """Gera ``lotes`` arquivos diários em ``out/lotes``. Do segundo em diante, cada lote traz também
    ~5% de reenvios de pedidos de lotes anteriores, com atualizações."""
    rng = random.Random(seed)
    pasta = out / "lotes"
    pasta.mkdir(parents=True, exist_ok=True)
    produtos = gerar_produtos(rng)
    # O número de clientes NÃO pode depender de `lotes`: ele consome o gerador aleatório, e mudar o total de
    # lotes alteraria a sequência inteira. Assim, gerar N+1 lotes reproduz os N primeiros byte a byte
    # (propriedade em que a DAG incremental se apoia; há um teste para ela).
    clientes = gerar_clientes(rng, max(1000, pedidos_por_lote // 2))

    with (out / "products.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(produtos[0]))
        writer.writeheader()
        writer.writerows(produtos)

    historico: list[dict] = []
    numero = novos = atualizacoes = 0
    for lote in range(1, lotes + 1):
        dia = inicio + timedelta(days=lote - 1)
        do_lote = []
        for _ in range(pedidos_por_lote):
            numero += 1
            do_lote.append(gerar_pedido(rng, numero, clientes, produtos, dia=dia))
        reenvios = []
        if historico:
            amostra = rng.sample(range(len(historico)), min(len(historico), max(1, pedidos_por_lote // 20)))
            for posicao in amostra:
                nova_versao = atualizar_pedido(rng, historico[posicao])
                reenvios.append(nova_versao)
                historico[posicao] = nova_versao  # próximas atualizações partem desta versão
        historico.extend(do_lote)
        with (pasta / f"lote_{lote:04d}.jsonl").open("w", encoding="utf-8") as f:
            for pedido in do_lote + reenvios:
                f.write(json.dumps(pedido, ensure_ascii=False) + "\n")
        novos += len(do_lote)
        atualizacoes += len(reenvios)
    return {"lotes": lotes, "pedidos_novos": novos, "atualizacoes": atualizacoes, "produtos": len(produtos)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--orders", type=int, default=200_000, help="quantidade de pedidos (padrão: 200000)")
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lotes", type=int, default=0, help="se > 0, gera lotes diários em OUT/lotes (carga incremental)")
    parser.add_argument("--pedidos-por-lote", type=int, default=2000)
    args = parser.parse_args()
    if args.lotes > 0:
        resumo = gerar_lotes(args.lotes, args.pedidos_por_lote, args.out, args.seed)
        print(f"Lotes gerados em {args.out / 'lotes'}: {resumo}")
        return
    resumo = gerar(args.orders, args.out, args.seed)
    print(f"Dados gerados em {args.out}: {resumo}")


if __name__ == "__main__":
    main()
