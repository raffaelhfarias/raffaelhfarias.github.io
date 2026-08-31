# Design do portfólio de Engenharia de Dados e Automação

## Resumo

O portfólio será reconstruído como uma experiência bilíngue orientada à contratação de um Engenheiro de Dados e Automação de nível pleno. A home deixará de ser uma listagem cronológica de posts e passará a comunicar posicionamento, impacto e evidências profissionais em menos de um minuto. Os três projetos principais serão apresentados como estudos de caso aprofundados; os demais permanecerão disponíveis em um catálogo secundário.

O novo site usará Astro, TypeScript e conteúdo em Markdown/MDX, será gerado estaticamente e continuará hospedado no GitHub Pages. A linguagem visual aprovada é “Editorial Engineering”: composição clara, tipografia editorial, azul intenso como cor de ação e elementos técnicos discretos.

## Contexto e diagnóstico

O site atual tem uma base operacional estável: Jekyll com o tema Chirpy, geração estática, deploy no GitHub Pages, funcionamento responsivo e ausência de erros visíveis no console durante a auditoria. O conteúdo também demonstra experiência prática relevante com Kestra, Python, Playwright, Browserless, autenticação 2FA, persistência de estado, APIs e automação de processos financeiros e operacionais.

Os principais problemas identificados foram:

- apresentação profissional centrada em “Data Scientist & Analyst”, desalinhada com os projetos mais fortes;
- home organizada como blog cronológico, sem hero, proposta de valor ou chamadas para ação;
- ausência de projetos fixados, o que faz a data determinar a prioridade;
- cases curtos e repetitivos, sem métricas quantificadas, diagramas, evidências ou decisões técnicas aprofundadas;
- oito projetos sem demonstração, repositório ou outro link externo;
- navegação priorizando categorias, tags e arquivos em vez de projetos, trajetória e contato;
- identidade visual genérica, com selfie, ilustração reutilizada e badges decorativos;
- capas com texto pequeno, redundante com o título do card e difícil de ler no mobile;
- título da home limitado ao nome, Open Graph baseado no avatar e textos alternativos genéricos;
- múltiplos títulos de nível 1 na home;
- ausência de layouts, componentes e estilos autorais no repositório.

## Objetivos

1. Posicionar Raffael Henrique como Engenheiro de Dados e Automação de nível pleno.
2. Converter visitas de recrutadores e líderes técnicos em leitura de cases, acesso ao currículo ou contato.
3. Comunicar especialidade, impacto e domínio técnico em até 30 segundos.
4. Demonstrar autonomia por meio de problemas reais, decisões de arquitetura e resultados mensuráveis.
5. Atender aos mercados brasileiro e internacional com conteúdo adaptado em português e inglês.
6. Preservar o valor histórico dos projetos existentes sem permitir que trabalhos antigos dominem a apresentação.
7. Manter desempenho, acessibilidade, SEO e manutenção simples em um site estático.

## Não objetivos da primeira versão

- CMS ou painel administrativo;
- banco de dados ou backend próprio;
- autenticação;
- formulário de contato com processamento no servidor;
- animações complexas;
- demos dependentes de infraestrutura ativa;
- reprodução de sistemas ou dados confidenciais;
- área de comentários;
- migração para uma plataforma de hospedagem paga.

## Público e posicionamento

### Público principal

Recrutadores e líderes técnicos contratando profissionais de nível pleno para Engenharia de Dados, Automação, Integrações ou funções adjacentes.

### Mercado

Brasil e oportunidades internacionais/remotas. A experiência será bilíngue desde a arquitetura, não uma tradução adicionada posteriormente.

### Posicionamento principal

**Engenheiro de Dados e Automação**

O texto deve enfatizar a capacidade de transformar processos operacionais complexos em fluxos confiáveis, integrando sistemas, processando dados e reduzindo intervenção manual.

IA será apresentada como competência complementar e direção de evolução. O site não usará “Engenheiro de IA” como identidade principal até que existam cases fortes de sistemas com LLMs, RAG, agentes, MLOps ou aplicações equivalentes.

### Tom de voz

- objetivo e seguro;
- técnico sem excesso de jargão;
- orientado a decisões e resultados;
- honesto sobre limitações e confidencialidade;
- sem superlativos vazios ou alegações não comprovadas.

## Arquitetura da informação

### Páginas principais

1. **Home:** posicionamento, prova rápida, cases selecionados, método, competências e contato.
2. **Projetos:** catálogo filtrável de cases profissionais e projetos pessoais.
3. **Case:** estudo aprofundado de uma solução.
4. **Sobre:** trajetória, formação, competências, currículo e contatos.
5. **Artigos:** arquivo editorial secundário para conteúdo existente e publicações futuras.

O menu principal terá Projetos, Sobre e Artigos, seguido pelo alternador de idioma e pela chamada para currículo ou contato. Categorias, tags e arquivos não ocuparão a navegação primária.

### Rotas bilíngues

- português em `/pt/`;
- inglês em `/en/`;
- páginas equivalentes compartilharão um identificador estável;
- o alternador de idioma levará à versão equivalente da página atual;
- cada versão terá metadados, texto e currículo próprios;
- tags `hreflang` e canonical serão geradas de acordo com a rota.

A raiz `/` redirecionará para `/pt/`, mantendo o português como idioma padrão. Não haverá detecção automática de idioma baseada no navegador na primeira versão, evitando navegação imprevisível e problemas de indexação.

## Estrutura da home

### 1. Cabeçalho

- nome como assinatura textual;
- links para Projetos, Sobre e Artigos;
- alternador PT/EN;
- chamada discreta para currículo ou contato;
- cabeçalho compacto e fixo somente quando não reduzir a área útil em telas pequenas.

### 2. Hero

- rótulo “Engenheiro de Dados e Automação”;
- proposta de valor curta;
- descrição de até duas linhas;
- CTA primário para os cases;
- CTA secundário para o currículo;
- sinal de disponibilidade profissional, localização e idiomas.

Mensagem-base aprovada para refinamento editorial:

> Sistemas que transformam complexidade operacional em fluxo.

### 3. Prova rápida

Três indicadores agregados e verificáveis, escolhidos entre tempo economizado, registros processados, redução de intervenção manual, frequência de execução ou processos atendidos. Os valores serão publicados como números exatos ou faixas identificadas, conforme a confidencialidade.

### 4. Cases em destaque

Três cards com problema, resumo da solução, stack essencial e resultado principal. A seleção inicial é:

1. Venda direta com autenticação resiliente;
2. Pipeline para conciliação contábil;
3. Documentos financeiros para dados estruturados.

### 5. Como trabalho

Fluxo em quatro etapas:

1. entender o problema, as restrições e o resultado;
2. projetar contratos, estados e integrações;
3. operar com retries, idempotência e observabilidade;
4. medir tempo, volume, precisão e adoção.

### 6. Competências comprovadas

Competências serão ligadas a evidências concretas, não apresentadas como uma nuvem de tecnologias. Os grupos iniciais são:

- orquestração;
- integração;
- processamento de dados;
- confiabilidade operacional.

Cada grupo apontará para pelo menos um case que demonstre seu uso.

### 7. Apresentação e contato

Resumo humano da trajetória, fotografia profissional e CTA para LinkedIn, GitHub, e-mail e currículos em português e inglês.

## Modelo dos estudos de caso

Cada case principal conterá:

1. resumo executivo com problema, solução e resultado;
2. contexto de negócio e restrições;
3. responsabilidade pessoal;
4. diagrama de arquitetura sanitizado;
5. decisões técnicas e alternativas consideradas;
6. confiabilidade: estados, retries, idempotência, autenticação, monitoramento e falhas;
7. resultados mensuráveis;
8. stack associada às funções que cada tecnologia cumpriu;
9. aprendizados, limitações e melhorias futuras;
10. evidências sanitizadas: telas, trechos de configuração, demonstração ou repositório quando permitido.

Os cases profissionais usarão nomes neutros para empresas, sistemas e dados. Nenhum segredo, credencial, endpoint privado, dado pessoal ou informação comercial sensível será publicado.

### Campos estruturados

Cada entrada de projeto terá, no mínimo:

- identificador estável;
- idioma;
- título;
- resumo;
- tipo de projeto;
- função exercida;
- período;
- problema;
- solução;
- impacto;
- métricas;
- stack;
- competências demonstradas;
- nível de confidencialidade;
- imagem social;
- imagem de capa;
- destaque na home;
- disponibilidade de repositório ou demonstração.

O schema rejeitará builds quando faltar um campo obrigatório. Métricas podem ser omitidas apenas em projetos não destacados, com uma explicação editorial da restrição; os três cases principais exigem ao menos uma evidência quantificável.

## Estratégia para o conteúdo existente

- os três cases principais serão reescritos integralmente;
- os demais projetos profissionais serão migrados para o catálogo com resumos normalizados;
- Airbnb, COVID-19, churn e outros projetos de formação permanecerão como arquivo de trajetória;
- artigos úteis continuarão disponíveis em uma área editorial secundária;
- URLs antigas serão preservadas ou redirecionadas permanentemente para a rota nova equivalente;
- datas originais serão mantidas como metadado histórico, mas não determinarão a ordem da home.

## Direção visual

### Conceito aprovado: Editorial Engineering

A identidade combina autoridade editorial com sinais discretos de engenharia.

- base clara em marfim ou cinza quente;
- texto em grafite de alto contraste;
- azul intenso como cor de ação e navegação;
- tipografia editorial nos títulos;
- tipografia sans-serif nas interfaces e no corpo;
- fonte monoespaçada apenas em rótulos técnicos, estados e pequenos trechos;
- espaço em branco generoso;
- bordas finas, grids precisos e poucos efeitos;
- diagramas inspirados em documentação técnica;
- fotografia profissional natural;
- animações discretas, respeitando `prefers-reduced-motion`;
- modo escuro opcional, sem ser a experiência dominante.

Não serão usados como elementos principais:

- estética integral de terminal;
- ilustrações genéricas de programador;
- badges decorativos;
- excesso de logos;
- fundos com partículas ou animações contínuas;
- glassmorphism;
- carrosséis;
- barras de proficiência arbitrárias.

## Arquitetura técnica

### Stack

- Astro;
- TypeScript em modo estrito;
- Markdown/MDX para conteúdo;
- Astro Content Collections com schemas validados;
- CSS autoral organizado por tokens e componentes;
- geração estática;
- GitHub Actions;
- GitHub Pages.

Dependências de interface serão adicionadas apenas quando resolverem uma necessidade que HTML, CSS e os componentes do Astro não atendam com clareza. A home não dependerá de um framework cliente.

### Módulos principais

- **conteúdo:** schemas, loaders e relacionamentos entre traduções;
- **i18n:** rotas, textos de interface, alternância e metadados;
- **SEO:** títulos, descriptions, canonical, hreflang, Open Graph e JSON-LD;
- **design system:** tokens, tipografia, botões, cards, grids e estados de foco;
- **projetos:** listagem, filtros progressivamente aprimorados e cards;
- **cases:** template, métricas, diagramas, evidências e navegação relacionada;
- **shell:** cabeçalho, rodapé, navegação e layout responsivo.

Cada módulo terá uma responsabilidade clara e dependerá apenas de contratos públicos, como props tipadas ou schemas de conteúdo.

### Fluxo de dados

1. arquivos Markdown/MDX fornecem conteúdo localizado e metadados;
2. Content Collections validam os dados durante o build;
3. loaders agrupam versões traduzidas pelo identificador estável;
4. páginas geradas estaticamente recebem conteúdo e metadados tipados;
5. componentes renderizam HTML sem dependência de JavaScript quando a interação não o exige;
6. o build gera o site estático para o GitHub Pages.

## Tratamento de erros e degradação

- conteúdo obrigatório ausente interrompe o build com mensagem identificando o arquivo e o campo;
- tradução ausente em página principal interrompe o build;
- tradução ausente em artigo histórico remove apenas o link de alternância para aquele idioma;
- imagem ausente usa uma capa editorial gerada a partir de tokens do projeto, nunca um ícone quebrado;
- links internos quebrados falham na verificação de CI;
- links externos indisponíveis geram relatório de CI, sem bloquear o deploy por falhas transitórias;
- filtros de projeto funcionam como links e conteúdo legível sem JavaScript; JavaScript apenas melhora a experiência;
- animações são removidas quando o usuário prefere movimento reduzido;
- a página 404 será bilíngue e oferecerá caminhos para Home e Projetos.

## SEO, acessibilidade e desempenho

### SEO

- títulos incluem nome, especialidade e contexto da página;
- descriptions específicas por rota;
- uma única hierarquia principal de `h1` por página;
- canonical e `hreflang` corretos;
- Open Graph próprio para site e cases;
- JSON-LD de `Person`, `WebSite`, `BreadcrumbList` e `CreativeWork` quando aplicável;
- sitemap e robots gerados;
- redirects preservam autoridade das URLs antigas.

### Acessibilidade

- conformidade mínima com WCAG 2.2 AA;
- navegação completa por teclado;
- foco visível;
- contraste validado;
- landmarks e headings semânticos;
- texto alternativo específico;
- links com propósito compreensível;
- diagramas acompanhados de descrição textual;
- idioma declarado por página;
- suporte a zoom e reflow em telas estreitas.

### Desempenho

- JavaScript cliente mínimo;
- imagens responsivas e otimizadas;
- dimensões de mídia declaradas;
- fontes auto-hospedadas e reduzidas aos pesos usados;
- carregamento tardio de mídia fora da primeira dobra;
- ausência de bibliotecas de animação na primeira versão;
- metas Lighthouse mínimas de 90 para desempenho, acessibilidade, boas práticas e SEO em páginas principais.

## Estratégia de testes

### Build e conteúdo

- build de produção;
- checagem de tipos;
- validação dos schemas;
- verificação de traduções obrigatórias;
- verificação de links internos;
- auditoria de redirects.

### Interface

- smoke tests para Home, Projetos, Case e Sobre nos dois idiomas;
- teste do alternador de idioma preservando a página equivalente;
- teste de navegação principal e CTAs;
- teste dos filtros com e sem JavaScript;
- teste da página 404;
- snapshots visuais nos breakpoints principais;
- testes de teclado e auditoria automatizada de acessibilidade.

### Qualidade operacional

- Lighthouse em páginas representativas;
- validação de metadados e dados estruturados;
- verificação de ausência de overflow horizontal;
- verificação de console sem erros nas rotas principais;
- deploy de preview ou build local revisado antes da publicação.

## Migração e publicação

1. estabelecer a base Astro e o design system;
2. implementar shell, i18n e SEO;
3. criar schemas e templates de conteúdo;
4. implementar e validar a home;
5. produzir os três cases principais;
6. migrar catálogo, artigos e rotas antigas;
7. adicionar currículos, fotografia e imagens finais;
8. executar testes de regressão, acessibilidade, desempenho e links;
9. substituir o build Jekyll no workflow de GitHub Pages;
10. publicar somente quando os redirects e os dois idiomas estiverem completos.

A mudança do gerador ocorrerá em uma única publicação, mas o desenvolvimento poderá ser feito incrementalmente no repositório. O site Jekyll permanecerá como versão publicada até a nova versão satisfazer os critérios de aceitação.

## Materiais necessários para publicação

- fotografia profissional autorizada para uso público;
- currículo final em português;
- currículo adaptado para inglês;
- métricas aproximadas e verificáveis dos três cases;
- imagens e telas anonimizadas;
- diagramas sanitizados;
- descrição precisa da participação individual em cada solução.

Durante o desenvolvimento, os componentes podem usar conteúdo de demonstração claramente marcado apenas no ambiente local. Conteúdo de demonstração não poderá chegar ao build de produção.

## Critérios de aceitação

A primeira versão estará pronta quando:

1. o posicionamento principal for compreensível na primeira dobra;
2. os três cases principais apresentarem responsabilidade, arquitetura, decisões, confiabilidade e impacto;
3. Home, Projetos, Case e Sobre estiverem completas em português e inglês;
4. currículos, GitHub, LinkedIn e e-mail estiverem acessíveis por CTAs claros;
5. todas as URLs antigas relevantes funcionarem ou redirecionarem corretamente;
6. não houver links internos quebrados ou erros no console;
7. navegação por teclado, foco e contraste atenderem ao padrão definido;
8. não houver overflow horizontal nos breakpoints testados;
9. as páginas principais alcançarem pelo menos 90 nas quatro categorias Lighthouse definidas;
10. schemas, testes, build e deploy passarem no CI;
11. nenhum dado confidencial ou conteúdo de demonstração estiver presente no build de produção.

