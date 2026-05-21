# Guia visual das imagens do portfólio

Este guia define o padrão visual das capas e imagens do portfólio para manter consistência, qualidade profissional e melhor aproveitamento do tema Chirpy.

## Objetivo

As imagens do portfólio devem transmitir:

- organização;
- identidade visual;
- clareza;
- valor técnico e de negócio;
- acabamento profissional.

A ideia não é criar peças extravagantes, mas capas limpas, bonitas e consistentes entre si.

## Estrutura recomendada

### 1. Capas de posts
Usadas no campo `image:` do front matter.

**Pasta:** `assets/img/posts/covers/`

**Função:** aparecer na home, cards, listagens e previews.

### 2. Imagens de preview
Usadas dentro do conteúdo do post.

**Pasta:** `assets/img/posts/previews/`

**Função:** exibir dashboard, GIF, tela da aplicação ou resultado do projeto.

### 3. Imagens institucionais do site
Usadas para social preview, banners ou peças gerais.

**Pasta:** `assets/img/site/`

## Dimensões padrão

### Capa de post
- `1200 x 630 px`
- proporção `1.91:1`
- ideal para cards, Open Graph e compartilhamento

### Preview interno do post
- largura livre, mas preferencialmente exportado com boa nitidez
- screenshots devem ser cortadas para remover áreas desnecessárias

## Layout padrão da capa

Cada capa deve ter:

1. **categoria** em destaque discreto
2. **título do projeto** com boa legibilidade
3. **subtítulo curto** com o objetivo do projeto
4. **stack principal** em uma linha curta
5. **elemento visual de apoio** (gráfico, linhas, blocos, mapa, fluxo, etc.)

## Hierarquia textual

### Título
- curto e forte
- até 2 linhas
- maior destaque visual da peça

### Subtítulo
- 1 linha, no máximo 2
- explicar o tipo de solução ou o valor entregue

### Stack
- exemplo: `Python · Dash · Plotly`
- exemplo: `Python · Playwright · Kestra`
- exemplo: `Power BI · DAX · Power Query`

## Paleta recomendada por categoria

### Análise de Dados
- base: verde petróleo / teal
- apoio: cinza escuro / branco
- sensação: clareza analítica

### Machine Learning
- base: azul escuro / roxo
- apoio: azul claro / branco
- sensação: inteligência, modelagem, tecnologia

### Business Intelligence
- base: dourado queimado / grafite
- apoio: cinza claro / branco
- sensação: executivo, estratégico, corporativo

### Automação
- base: vermelho queimado / laranja escuro / azul acinzentado
- apoio: branco / grafite
- sensação: fluxo, processo, eficiência

## Estilo visual recomendado

- fundo limpo, sem excesso de informação;
- uso de formas geométricas sutis;
- evitar prints crus como capa principal;
- boa área de respiro;
- evitar mais de 3 níveis de informação;
- manter consistência de margens e tipografia.

## O que evitar

- screenshots poluídas como capa principal;
- excesso de logos;
- muito texto;
- muitas cores competindo entre si;
- imagens desfocadas ou esticadas;
- fundos com contraste ruim para leitura.

## Padrão de nomes

Usar sempre `kebab-case`:

- `churn-prediction-cover.png`
- `cine-match-cover.png`
- `airbnb-veneza-cover.png`
- `covid-dashboard-cover.png`
- `gasolina-brasil-cover.png`
- `estresse-comercial-cover.png`
- `whatsapp-report-cover.png`
- `banco-de-horas-cover.png`

## Estrutura sugerida por projeto

### Capa
Imagem criada para o portfólio, com identidade visual única.

### Preview interno
Imagem real do projeto: dashboard, notebook, automação, tela ou GIF.

## Processo recomendado para novos posts

1. criar a capa no padrão visual;
2. exportar em `1200x630`;
3. salvar em `assets/img/posts/covers/`;
4. salvar screenshot ou GIF em `assets/img/posts/previews/`;
5. atualizar o campo `image:` do post;
6. opcionalmente inserir preview dentro do conteúdo.

## Prioridade de execução

Começar pelos posts fixados (`pin: true`), pois eles têm mais impacto visual imediato na home do Chirpy.
