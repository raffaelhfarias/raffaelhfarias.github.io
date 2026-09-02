# Pacote de fontes dos cases do portfólio

Status: **APROVADO COM RESTRIÇÕES** (resposta do proprietário registrada em 2026-09-01).

Este é o pacote-fonte exclusivo dos seis MDX da Tarefa 8. Os três cases foram desenvolvidos ao longo de meses em 2026 e continuam ativos na data da aprovação. A responsabilidade pessoal foi ponta a ponta: entendimento do problema, desenho, implementação, testes, deploy, operação e manutenção. Clientes, sistemas, origens, identificadores, endpoints, credenciais e dados pessoais permanecem fora do material publicável.

As arquiteturas descritas abaixo foram confirmadas pelo proprietário. É autorizado citar Kestra, Python, Playwright, Browserless, TOTP/2FA, integração de mensageria, PDF e XLSX, além de usar diagramas editoriais sanitizados. Os diagramas não representam telas nem dados operacionais.

## Case 1 — Venda direta com autenticação resiliente

### Contexto de negócio

Uma rotina coleta resultados de venda direta em ambiente protegido por login externo e segundo fator, preservando o contexto de sessão entre execuções e entregando os dados por integração de mensageria.

### Responsabilidade pessoal

Responsabilidade ponta a ponta pela solução, da definição do problema ao deploy, à operação e à manutenção.

### Nós e arestas de arquitetura

Kestra orquestra a renovação e a execução; Python coordena a extração, consolidação e entrega; Playwright conecta-se ao Browserless; o login externo usa TOTP/2FA; o estado de sessão é reaproveitado; os resultados seguem para a integração de mensageria.

### Decisões de confiabilidade

Renovação de autenticação separada da execução completa, reutilização de estado de sessão e navegação remota com Browserless foram decisões confirmadas. Limite: este pacote não quantifica disponibilidade, taxa de sucesso, retries, backoff, timeout, idempotência ou alertas; essas alegações não devem ser publicadas.

### Métrica verificada com qualificador

**1 hora** de cadência de renovação de cookies. É uma cadência operacional de autenticação, não uma medida de impacto, disponibilidade ou economia de tempo.

### Evidência publicável

Texto sanitizado e diagrama editorial que mostram fronteiras e fluxo, sem dados do portal, estado de sessão ou entrega.

## Case 2 — Pipeline para conciliação contábil

### Contexto de negócio

O pipeline reúne dados financeiros de fontes anonimizadas para apoiar a conciliação, reduzindo a necessidade de navegar, limpar e reorganizar manualmente informações antes da análise.

### Responsabilidade pessoal

Responsabilidade ponta a ponta pela solução, da definição do problema ao deploy, à operação e à manutenção.

### Nós e arestas de arquitetura

Kestra orquestra as etapas; Playwright e Browserless coletam dados; Python aplica parsing, limpeza e regras de negócio; a saída consolidada apoia a conciliação. A organização separa componentes, páginas e regras de negócio e usa Page Object Model.

### Decisões de confiabilidade

Browserless, logging estruturado, componentes reutilizáveis, separação modular e Page Object Model foram decisões confirmadas. Limite: o pacote não registra valores históricos para retries, backoff, timeout, idempotência, deduplicação, completude, alertas ou falhas parciais; não publicar essas medidas.

### Métrica verificada com qualificador

**3 etapas:** coleta, normalização e consolidação. É a estrutura confirmada do pipeline. O ganho de tempo foi confirmado apenas qualitativamente, sem medição histórica publicável.

### Evidência publicável

Descrição sanitizada e diagrama editorial da coleta à consolidação, sem nomes de fontes, saldos, títulos ou destinos internos.

## Case 3 — Documentos financeiros para dados estruturados

### Contexto de negócio

O fluxo recebe um documento financeiro em PDF por um canal de mensagens, extrai dados estruturados e devolve uma planilha XLSX pelo mesmo canal para apoiar uma rotina administrativa.

### Responsabilidade pessoal

Responsabilidade ponta a ponta pela solução, da definição do problema ao deploy, à operação e à manutenção.

### Nós e arestas de arquitetura

O solicitante envia o PDF pelo canal; a integração encaminha o documento a um subfluxo orquestrado no Kestra; Python extrai os dados e gera o XLSX; a integração devolve o arquivo pelo canal.

### Decisões de confiabilidade

O retorno de uma mensagem clara ao usuário em caso de erro e o uso do mesmo canal para entrada e devolução foram decisões confirmadas. Limite: o pacote não registra valores históricos para retries, timeout, idempotência, validação, retenção, controle de acesso, alertas ou falhas parciais; não publicar essas medidas.

### Métrica verificada com qualificador

**2 formatos:** PDF para XLSX. É uma evidência do escopo de transformação. O ganho de tempo foi confirmado apenas qualitativamente, sem medição histórica publicável.

### Evidência publicável

Descrição sanitizada e diagrama editorial PDF → extração → XLSX → devolução, sem documentos, remetentes, mensagens, dados financeiros ou identificadores.

## Retrato e currículos

- O avatar `commons/avatar.jpg` está aprovado como fonte de retrato para uma tarefa futura de ativos.
- Currículos em português e inglês foram **postergados**: serão produzidos e adaptados por vaga. Nenhum PDF é criado, publicado ou vinculado nesta tarefa.

## Registro de restrição editorial

- A resposta `8h → 30min` foi fornecida exclusivamente como **exemplo fictício de validação**. Ela não é uma métrica real, não é publicável e não pode aparecer em frontmatter, MDX, páginas ou saída de produção.
- Para ganhos de tempo de conciliação e documentos financeiros, só é permitido declarar confirmação qualitativa, sem medição histórica.

## Status final de lançamento

- Retrato aprovado pelo proprietário, convertido para `src/assets/profile/raffael-henrique.webp` e publicado nas páginas Sobre e About.
- Currículos continuam sob demanda e adaptados por vaga; nenhum PDF genérico deve ser publicado ou vinculado.
- Os três cases bilíngues foram publicados somente com as evidências e os qualificadores aprovados neste documento.
- O exemplo fictício `8h → 30min` permanece restrito a este pacote de fontes e proibido na saída pública.
- A publicação do novo workflow depende da revisão do preview e da aprovação explícita do proprietário.
