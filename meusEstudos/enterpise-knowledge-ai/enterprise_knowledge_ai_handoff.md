# Enterprise Knowledge AI — Demo RAG de portfólio

**Versão:** 2.0 — escopo realinhado em 19/10/2026

**Objetivo:** demonstrar um RAG funcional, simples de experimentar e tecnicamente consistente.

**Público:** recrutadores, visitantes do portfólio e testers.

**Status:** fundação da API existente; experiência pública e pipeline RAG ainda não implementados.

Este documento substitui o escopo anterior de plataforma empresarial multi-tenant. O nome e o diretório do projeto permanecem; não estamos construindo um SaaS B2B. Requisitos anteriores só continuam obrigatórios quando constam neste escopo.

## 1. Experiência esperada

O visitante abre uma página, envia um PDF textual ou DOCX, acompanha o processamento e faz perguntas sobre esse documento. As respostas exibem as evidências usadas. Quando não houver informação suficiente, o sistema informa isso claramente.

- Sem cadastro, login ou seleção de empresa na experiência pública.
- Uma sessão de visitante com um documento ativo por vez.
- Cinco perguntas disponíveis por sessão na primeira versão, com contador visível.
- Trocar o documento não renova a cota da sessão.
- Documento de exemplo disponível para quem quiser testar sem fazer upload.
- Documentos e trechos de uma sessão não ficam acessíveis a outra.

A interface de referência inspira a hierarquia pergunta → resposta → fontes, não os filtros, conectores e painéis empresariais.

## 2. Escopo obrigatório

### Interface

- Uma página responsiva com upload, nome do documento e status de processamento.
- Campo de pergunta e histórico das perguntas e respostas da sessão.
- Contador de perguntas restantes e indicação clara de cota esgotada.
- Fontes com trecho e identificação do documento; página no PDF quando disponível. Não inventar paginação de DOCX.
- Estados compreensíveis de carregamento, erro, ausência de evidência e sessão expirada.
- Aviso para não enviar dados sensíveis e explicação sobre processamento e retenção dos arquivos.

### RAG

- Validar formato e tamanho; aceitar PDF com texto e DOCX.
- Extrair texto, preservar referências de origem e gerar chunks com metadados.
- Gerar e persistir embeddings; buscar trechos relevantes apenas do documento autorizado à sessão.
- Enviar ao modelo a pergunta e os trechos recuperados, não o documento inteiro a cada pergunta.
- Retornar resposta fundamentada e referências verificáveis aos trechos usados.
- Tratar o conteúdo do arquivo como dados, não como instruções para o sistema.
- Exibir status de processamento e falha; não duplicar trechos em uma nova tentativa do mesmo processamento.

### Proteções da demo pública

- Validar no backend sessão, acesso ao documento e cota de perguntas; o contador da interface não é a proteção.
- Limitar tamanho/páginas de arquivos, frequência de requisições e concorrência de processamento.
- Aplicar teto global de consumo para que novas sessões não contornem toda a proteção de custos.
- Expirar sessões e remover arquivos, texto e embeddings associados conforme a retenção definida.
- Manter credenciais no servidor e evitar conteúdo de documentos e segredos nos logs.
- Informar antes do upload se conteúdo será enviado a um provedor externo de IA.

Os valores dos limites, retenção e orçamento serão acordados antes da publicação pública da demo. Cinco perguntas por sessão não equivalem a cinco por pessoa nem substituem o teto global.

## 3. Fora desta versão

- Cadastro público, gestão de organizações, convites e painéis administrativos.
- Permissões empresariais owner/editor/viewer como parte da interface.
- Coleções e consulta simultânea a vários documentos na experiência pública.
- Integrações com Drive, Slack, SharePoint ou outras fontes externas.
- OCR, PDFs escaneados, análise de imagens e tabelas complexas.
- Comparação obrigatória entre busca lexical, vetorial e híbrida, reranking e dashboards de observabilidade.
- Fine-tuning, GraphRAG, múltiplos agentes, cobrança, planos e SSO.
- Dataset de 50 perguntas ou infraestrutura de avaliação extensa como condição para a demo.

## 4. Implementação e infraestrutura

- Reaproveitar FastAPI e PostgreSQL/pgvector já presentes no projeto.
- Manter o projeto em `meusEstudos/enterpise-knowledge-ai` no repositório do portfólio.
- Deploy pelo Dockerfile no Coolify existente; o usuário conduz os deploys.
- Não exigir Docker local nem criar novos serviços sem necessidade confirmada.
- Escolher a forma mais simples de servir a interface; nenhum framework frontend é obrigatório neste escopo.
- Reavaliar a necessidade de Redis/Celery e MinIO/S3 antes de pedir novos recursos. Não são entregáveis por si só.
- Não reestruturar pastas nem introduzir camadas para acomodar possibilidades futuras.

O código atual de usuários, tenants e coleções não precisa ser removido nesta etapa. Pode ser reaproveitado internamente se simplificar o isolamento, mas o visitante não deve operar esses conceitos. A adaptação da sessão pública deve ser explícita e testada, nunca baseada em compartilhar a mesma credencial entre todos os visitantes.

## 5. Estado real após a integração da demo

Atualização local, ainda não publicada: a interface está ligada ao RAG por `/v1/demo`, com sessão anônima por cookie opaco, cinco tentativas, uma pergunta simultânea, expiração em 30 minutos e limpeza a cada minuto. Cotas por hora compartilhadas persistem no banco (10 envios e 50 perguntas por padrão). O documento fictício também usa a NVIDIA, sem respostas pré-definidas. PDF/DOCX seguem validação no servidor e limite de até 80 trechos. O histórico fica apenas na tela.

A migration `0002_demo` adiciona duas tabelas ao banco existente: sessões temporárias (texto/vetores JSON) e orçamento global. Não usa MinIO, Redis ou Celery. Para esta escala, busca de cosseno sobre até 80 trechos substitui a necessidade de índice pgvector; o banco continua PostgreSQL, sem serviço novo. Arquivos originais não são armazenados. Retenção externa da NVIDIA e backups do banco são independentes da limpeza lógica da aplicação.

`DEMO_ENABLED=false` por padrão: antes de ativar, aplicar migration, confirmar termos da conta e validar a NVIDIA real no Coolify. Não é alegada validação autenticada da NVIDIA nem teste contra PostgreSQL neste ambiente. Cotas limitam consumo, mas não impedem esgotamento deliberado ou uma pessoa criar sessões novas. As seções abaixo registram o estado anterior ao desenvolvimento desta integração.

- Implementado: API de autenticação, memberships, coleções, upload e consulta de status; migrations e testes locais.
- Confirmado pelo usuário no Coolify: API publicada, PostgreSQL conectado, migrations, seed e login funcionando.
- Usuário confirmou deploy da interface anterior em prévia. A integração atual ainda está local.
- Ainda não confirmado no deploy: armazenamento de arquivos e fluxo completo de upload/isolamento.
- Implementado após o realinhamento: motor RAG por comando, com extração, chunks e vetores em memória, recuperação, resposta com fontes e cinco tentativas por execução. Testado localmente com provedor simulado; falta validação autenticada na NVIDIA.
- Interface ligada à demo anônima em `/`: upload, exemplo real, perguntas, histórico da tela e fontes; cota e isolamento verificados no backend com provedor simulado.
- Pendente: validação da conta NVIDIA real, migration e teste completo no PostgreSQL/Coolify. Uploads da API autenticada permanecem separados; índice pgvector e pipeline empresarial não são necessários para esta entrega.
- `/health/ready` verifica banco/schema; não comprova que o RAG ou o armazenamento estão operacionais.

A implementação da fundação anterior não equivale à conclusão da nova demo.

## 6. Sequência de entrega

### Etapa 1 — Fechar decisões mínimas

Definir provedor/modelos de embeddings e respostas, orçamento da demo, limites de arquivo e retenção. Confirmar quais recursos já existem no Coolify e decidir armazenamento/processamento sem ampliar a infraestrutura por padrão.

### Etapa 2 — Um documento até uma resposta

Adaptar isolamento por sessão; implementar upload, extração, chunking, embeddings, recuperação e resposta com fontes. Validar o fluxo completo com documento sintético antes de ampliar funcionalidades.

### Etapa 3 — Experiência do visitante

Entregar a página simples, documento de exemplo, status, histórico e contador. Integrar a cota no backend e testar sessões independentes.

### Etapa 4 — Publicação de portfólio

Concluir expiração/limpeza, proteção de consumo, testes e README de reprodução. O usuário realiza o deploy; validar a experiência publicada e apresentar no portfólio o que foi construído e suas limitações.

## 7. Critérios de conclusão

- Visitante consegue testar sem cadastro, com arquivo próprio ou exemplo.
- PDF textual e DOCX válidos percorrem o fluxo de upload até perguntas; arquivo inválido ou acima dos limites recebe erro claro.
- Uma sessão nova dispõe de cinco perguntas; backend impede exceder a cota, inclusive com requisições concorrentes.
- Respostas usam recuperação de trechos e exibem fontes correspondentes; pergunta sem evidência recebe abstenção.
- Testes comprovam isolamento entre sessões e bloqueio de acesso após expiração.
- Limpeza remove os dados expirados, e limites de uso são aplicados no servidor.
- Um pequeno conjunto de perguntas conhecidas verifica recuperação, fontes e ausência de evidência; resultados reais e limitações ficam documentados.
- Interface funciona em desktop e celular, e o fluxo completo é validado no Coolify.

## 8. Provedor e modelos iniciais

Usaremos a API hospedada da NVIDIA para desenvolvimento e avaliação, sem instalar modelos ou exigir GPU na VM.

- Respostas: `nvidia/nemotron-3.5-super-vl-120b-a12b`, somente texto e com `chat_template_kwargs.enable_thinking=false`.
- Embeddings: `nvidia/nemotron-3-embed-1b`, voltado a recuperação e RAG multilíngue.
- Escolha inicial, não benchmark concluído: testar recuperação e respostas em português com documento sintético antes de validar a integração.
- Em 20/10/2026, a página oficial do modelo de respostas selecionado apresenta endpoint gratuito disponível. Ele substitui o modelo anterior após erro HTTP 404 na geração. A disponibilidade efetiva e as quotas da conta dependem de teste autenticado; não assumir acesso ilimitado nem disponibilidade garantida.
- A chave fica somente no servidor, em `NVIDIA_API_KEY`; nunca no frontend, Git ou logs. O usuário confirmou sua configuração no Coolify; esta máquina não recebeu a chave e nenhuma chamada autenticada foi feita daqui.
- Manter cinco perguntas por sessão e controles globais de uso, independentemente das quotas do provedor.
- Antes da abertura pública, confirmar se os termos aplicáveis à conta permitem a demo de portfólio. Acesso gratuito de avaliação não será tratado como autorização automática para publicação.

Referências oficiais consultadas: https://build.nvidia.com/nvidia/nemotron-3.5-super-vl-120b-a12b e https://build.nvidia.com/nvidia/nemotron-3-embed-1b.

Próxima validação: publicar o código pelo fluxo do usuário e executar o exemplo sintético no terminal da aplicação, confirmando uma resposta com fonte e uma abstenção na NVIDIA. A integração por comando não cria novas rotas nem muda o fluxo da API. Antes da experiência pública, fechar limites, retenção e persistência sem adicionar serviços por antecipação.
