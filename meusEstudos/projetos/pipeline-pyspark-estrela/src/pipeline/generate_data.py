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
    python -m pipeline.generate_data --orders 200000 --out data/raw
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


def gerar_pedido(rng: random.Random, n_pedido: int, clientes: list[dict], produtos: list[dict]) -> dict:
    segundos = int((DATA_FIM - DATA_INICIO).total_seconds())
    ts = DATA_INICIO + timedelta(seconds=rng.randint(0, segundos))
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--orders", type=int, default=200_000, help="quantidade de pedidos (padrão: 200000)")
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    resumo = gerar(args.orders, args.out, args.seed)
    print(f"Dados gerados em {args.out}: {resumo}")


if __name__ == "__main__":
    main()
