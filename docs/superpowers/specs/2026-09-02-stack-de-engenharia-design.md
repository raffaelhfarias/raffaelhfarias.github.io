# Especificação — Stack de engenharia

## Objetivo

Substituir o bloco vazio “Impacto, com contexto” por uma apresentação visual, curta e bilíngue do ecossistema técnico utilizado por Raffael. A seção deve complementar os cases selecionados, sem repetir suas narrativas ou publicar métricas não verificadas.

## Conteúdo

A seção será organizada por camadas de competência:

- Dados e transformação: Python e SQL.
- Orquestração e automação: Kestra, Playwright e Browserless.
- Integrações e mensageria: Evolution API, REST e webhooks.
- Infraestrutura: Docker, Linux, Coolify e Git.
- Cloud: Azure, identificado explicitamente como “em aprofundamento”.

Cada item terá logo local, nome da ferramenta e uma descrição curta de sua função. A lista final deve conter apenas ferramentas que o proprietário confirme como experiência real ou em aprofundamento.

## Composição visual

- Uma faixa horizontal contínua de itens compactos.
- Movimento lento e automático, com pausa no hover/foco.
- Itens duplicados apenas para permitir um loop visual contínuo.
- Logos preferencialmente em SVG local, com tratamento monocromático e acento azul coerente com o site.
- Nenhum parágrafo longo ou imagem decorativa que prejudique a leitura.

## Acessibilidade e comportamento

- A faixa deve continuar navegável por teclado.
- O movimento deve ser desativado para `prefers-reduced-motion: reduce`.
- O nome e a função de cada ferramenta devem permanecer disponíveis como texto acessível.
- Não depender de imagens remotas ou de chamadas externas em tempo de execução.

## Relação com a página

A ordem da página será:

1. Hero.
2. Stack de engenharia.
3. Cases selecionados.

Os cases continuam responsáveis por contexto, arquitetura, decisões e evidências. A nova seção responde apenas “com quais camadas e ferramentas eu entrego”.

## Idiomas

O título, os rótulos de grupo, as descrições e o marcador de Azure terão versões em português e inglês.

## Limites editoriais

- Não incluir métricas de impacto nesta seção.
- Não apresentar Azure como experiência consolidada; usar “em aprofundamento”.
- Não usar o exemplo fictício “8h → 30min”.
- Não afirmar domínio de uma ferramenta sem confirmação do proprietário.
