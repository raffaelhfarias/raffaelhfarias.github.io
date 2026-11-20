# Carga incremental

A carga completa (`run_pipeline`) lê tudo e substitui o conteúdo do DW. A carga incremental (`incremental.py`) processa **só os lotes novos** e mescla o resultado, o que obriga a tratar situações que a completa nunca vê.

## O problema

Em um sistema transacional o mesmo pedido chega mais de uma vez, mudando:

| O que chega | O que precisa acontecer no DW |
|---|---|
| Pedido novo | inserir as linhas |
| Pedido reenviado com **quantidade ou desconto corrigido** | **atualizar** a linha, sem duplicar |
| Pedido reenviado só com **status novo** (ex.: pago → enviado) | nada: status não está na fato |
| Pedido reenviado como **cancelado** | **remover** as linhas (pedido cancelado sai da fato por regra de negócio) |
| Pedido reenviado **sem um dos itens** | **remover** a linha do item que sumiu |
| O mesmo lote processado duas vezes | **nenhuma mudança** (idempotência) |

`MERGE` resolve inserir e atualizar. As remoções não: no PostgreSQL 16 não existe `WHEN NOT MATCHED BY SOURCE` (isso é do SQL Server e do PostgreSQL 17), então a remoção é um `DELETE` separado, **na mesma transação**.

## Como funciona

```
lote_NNNN.jsonl ─▶ silver (mesmas regras de qualidade) ─▶ gold do lote ─▶ stage_<schema>.* (JDBC)
                                                                              │
              ┌───────────────────────────────────────────────────────────────┘
              ▼   UMA transação:
      1. DELETE  linhas da fato de pedidos do lote que não existem mais na versão nova
      2. MERGE   dim_data, dim_pagamento, dim_canal      (só insere)
         MERGE   dim_cliente, dim_produto                (insere ou atualiza)
      3. MERGE   fato_vendas                             (insere ou atualiza se mudou)
      4. INSERT  controle_cargas (lote, checksum, contagens)
      5. verificação: as linhas do DW dos pedidos do lote == as da versão nova (contagem e valor total)
              ▼   COMMIT (ou ROLLBACK de tudo)
```

## Decisões

**Controle por checksum, no próprio banco.** `controle_cargas` guarda lote e SHA-256 do arquivo. Um lote é *pendente* se nunca foi processado **ou** se o arquivo mudou (mesmo nome, conteúdo novo). O registro é gravado na mesma transação do `MERGE`: "o lote consta no controle" e "os dados do lote estão no DW" nunca divergem. Uma tabela de controle fora do banco, ou gravada depois, poderia mentir após uma falha entre as duas escritas.

**`IS DISTINCT FROM` no `WHEN MATCHED`.** Só atualiza se algum valor realmente mudou. Reaplicar o mesmo lote vira um no-op de verdade (sem reescrever linhas) e o relatório mostra `~0 atualizadas`.

**Um escritor por vez, garantido pelo banco.** O staging é compartilhado entre lotes; dois processos ao mesmo tempo no mesmo schema misturariam os dados dos dois e o controle registraria um lote com dados do outro. Uma trava (`pg_try_advisory_lock`) numa conexão aberta durante toda a carga recusa a segunda. Ela protege também contra uma execução manual junto com a agendada, o que o `max_active_runs=1` da DAG não faz, e é liberada se o processo morrer (é de sessão).

**Atomicidade por staging + transação única.** O Spark grava o lote em `stage_<schema>.*` (tabelas sem PK/FK), cada escrita em sua própria transação; só então uma transação aplica tudo no schema final. Se o Spark ou o banco falharem antes da transação, o DW não foi tocado. Se falhar dentro dela, o `ROLLBACK` desfaz até o `DELETE` que já havia rodado. A verificação antes do `COMMIT` confere contagem **e** valor total das linhas dos pedidos do lote: pega o caso de o `MERGE` "funcionar" e deixar um estado errado, inclusive uma linha com o valor trocado.

**`dim_cliente` com SCD tipo 1 que não regride.** Um atributo "não informado" vindo de um lote novo não apaga um valor já conhecido (`CASE WHEN s.cidade = 'Não informada' THEN t.cidade ELSE s.cidade END`).

**Cada schema tem seu próprio controle.** A DAG incremental usa `dw_incremental`, separado de `dw`. A carga completa troca todo o conteúdo; se as duas escrevessem no mesmo schema, o controle diria que lotes antigos estão carregados quando o conteúdo já foi substituído.

## O que NÃO está resolvido

- **Ordem de chegada = ordem de verdade.** Sem `updated_at` ou número de versão na origem, "o último a chegar vence". Uma versão antiga que chegue depois de uma nova a sobrescreve. Em produção, o `MERGE` compararia a versão (`WHEN MATCHED AND s.versao > t.versao`). Vale também para `dim_cliente` (SCD1).
- **Reprocessar um lote antigo alterado regride o que veio depois.** Se o `lote_0002` for reescrito, ele é reaplicado e desfaz atualizações que o `lote_0003` já tinha feito nos mesmos pedidos. O checksum detecta a mudança, mas não sabe a ordem causal.
- **Pedido que sai de um arquivo reescrito não é removido do DW.** Só se removem linhas de pedidos que **aparecem** no lote.
- **Cabeçalho inválido deixa o pedido intocado.** Sem `order_id`, `customer.id` ou `order_ts` confiáveis, ou com status fora do domínio, o pedido vai para a quarentena e o DW fica como estava. Já um pedido de cabeçalho válido cujos itens foram **todos** rejeitados tem as linhas antigas removidas (a versão nova não tem nenhuma linha válida).
- **Empate dentro do lote.** Reenvios têm o mesmo `order_ts` do original; dentro de um mesmo arquivo, o desempate é pelo maior texto JSON, não pelo último da ordem do arquivo.
- **Exclusão física na origem** (o pedido some sem aviso) não é detectada: só se vê o que chega.
- **Dimensão que chega atrasada** (fato antes do cliente) não é tratada; aqui as dimensões nascem dos próprios lotes.
- **A trava é do PostgreSQL.** Não existe equivalente no SQL Server, onde esta carga não foi portada.
- **Não é equivalente a um rebuild em todos os casos.** A carga completa desempata reenvios por `order_ts` e conteúdo; o incremental, pela ordem dos lotes.
- **O checksum é calculado antes de o Spark ler o arquivo.** Se o arquivo mudar entre os dois momentos, o registro teria o checksum de um e os dados do outro. A janela é curta e a DAG gera o arquivo antes; um arquivo escrito de forma atômica (renomeado depois de pronto) a eliminaria.
- **Volume pequeno.** Cada lote tem alguns milhares de pedidos. Em volume alto, o `MERGE` precisaria de índices e particionamento na fato pensados para ele.
