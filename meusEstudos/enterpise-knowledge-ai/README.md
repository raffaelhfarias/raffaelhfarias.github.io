# Enterprise Knowledge AI — Demo RAG de portfólio

O objetivo atual é uma demo pública: enviar um PDF/DOCX e fazer cinco perguntas por sessão, com respostas fundamentadas e fontes. O escopo vigente está em [enterprise_knowledge_ai_handoff.md](enterprise_knowledge_ai_handoff.md). A interface está ligada ao motor RAG por sessões anônimas temporárias. Os endpoints autenticados da fundação anterior continuam separados; não estamos construindo uma plataforma B2B.

## Interface e demo

A rota `/` serve a página em português com HTML, CSS e JavaScript locais, sem framework, CDN ou processo de build separado. O mesmo Dockerfile já inclui os arquivos. Para visualizar sem banco, chave NVIDIA ou serviços externos:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Abra `http://127.0.0.1:8765`. Sem habilitação da demo, a página abre, mas o servidor recusa envios. Com `DEMO_ENABLED=true`, selecionar/arrastar um PDF ou DOCX envia o arquivo ao backend; extensão, conteúdo, tamanho e páginas são validados no servidor. O limite padrão é 20 MB/200 páginas, mas documentos também precisam caber em até 80 trechos de texto. PDF escaneado não tem OCR.

O botão de exemplo processa um manual fictício pelo mesmo RAG real; não apresenta respostas pré-definidas. O visitante faz perguntas livres e recebe fontes expansíveis. Todo texto é renderizado como texto, nunca HTML do documento/modelo. O histórico fica apenas na página; recarregar preserva o documento e a cota pelo cookie, mas não restaura as respostas anteriores.

### Habilitar depois do próximo deploy

1. Manter `NVIDIA_API_KEY` somente no runtime e confirmar os termos da conta para exposição pública.
2. No terminal da aplicação, executar `alembic upgrade head` (nova migration `0002_demo`).
3. Configurar `DEMO_ENABLED=true` no runtime e reiniciar/reimplantar pelo Coolify.
4. Abrir `/`, testar o documento fictício e perguntar pelo prazo de reembolso (15 dias) e pelo salário da gestora (abstenção). Depois testar um PDF textual e um DOCX próprios, sem dados sensíveis.

Nenhum serviço novo é necessário. A demo usa o PostgreSQL existente, sem MinIO/Redis/worker. Trechos e vetores ficam em colunas JSON, com busca de cosseno em memória sobre até 80 trechos; índice vetorial/pgvector não é necessário nessa escala. O arquivo original é descartado após extração. Conteúdo extraído e perguntas são enviados à NVIDIA, cujas políticas de retenção são independentes das nossas.

Sessões expiram em 30 minutos. A limpeza física roda a cada minuto enquanto a aplicação está ativa e também antes de novos uploads; após uma parada, roda novamente quando a aplicação volta. Remover o documento exclui imediatamente a sessão do banco. Isso não apaga backups/WAL do banco nem dados eventualmente retidos pelo provedor. Cookie opaco `HttpOnly`, `SameSite=Strict` e `Secure` em HTTPS; só o hash é armazenado no banco. Não há credencial da NVIDIA no navegador.

Cinco tentativas por sessão, inclusive falha do provedor; chamadas concorrentes da mesma sessão são rejeitadas. Cotas globais persistidas no banco: `DEMO_UPLOADS_PER_HOUR=10` e `DEMO_QUESTIONS_PER_HOUR=50`, por hora UTC de calendário, compartilhadas por visitantes/processos e preservadas em reinícios. Upload inválido após reserva também consome a cota de envio. Limite global atingido não consome uma tentativa da sessão. Limites conservadores não garantem disponibilidade: alguém pode esgotar a cota, apagar cookies ou iniciar sessões novas. Não há identificação por pessoa, CAPTCHA ou proteção antiabuso completa. Recomenda-se manter limite de corpo/conexões no proxy; as cotas da NVIDIA continuam valendo separadamente. Não há retries automáticos.

Rotas da demo: `POST /v1/demo/document?filename=arquivo.pdf` (corpo binário), `POST /v1/demo/example`, `GET /v1/demo/session`, `DELETE /v1/demo/session` e `POST /v1/demo/questions` (`{"question":"..."}`). Escritas exigem `X-Demo-Request: 1` e usam o cookie de sessão; não é permitido CORS. Nenhuma rota recebe ID de outro visitante. A habilitação é desligada por padrão para evitar consumo acidental antes da migration e da revisão dos termos.

## Avaliar o motor RAG com NVIDIA

O comando extrai PDF textual/DOCX/TXT, divide o texto em trechos, gera embeddings uma vez por execução e recupera até quatro trechos por pergunta usando similaridade de cosseno. A resposta inclui os trechos citados, com página para PDF; fontes inexistentes são rejeitadas. Isso valida a referência, não prova automaticamente que toda afirmação do modelo é verdadeira. Uma resposta sem fontes vira abstenção.

Configure `NVIDIA_API_KEY` como segredo de runtime. Os modelos padrão são `nvidia/nemotron-3.5-super-vl-120b-a12b` para respostas e `nvidia/nemotron-3-embed-1b` para embeddings; podem ser alterados por `NVIDIA_CHAT_MODEL` e `NVIDIA_EMBEDDING_MODEL`. Não é necessário instalar modelos, GPU, Redis ou MinIO para esse comando.

Se `NVIDIA_CHAT_MODEL` já estiver definida no Coolify, atualize seu valor para `nvidia/nemotron-3.5-super-vl-120b-a12b`: a variável prevalece sobre o padrão do código. A geração usa somente texto, com `chat_template_kwargs.enable_thinking=false`. A troca não exige migração nem recriação dos embeddings.

Depois que o usuário publicar este código no Coolify, executar no terminal da aplicação:

```sh
cd /app
python -m scripts.rag_demo --example --question "Qual é o prazo para solicitar reembolso?" --question "Qual é o salário da gestora?"
```

O exemplo é um manual fictício em português. A primeira pergunta deve citar o prazo de 15 dias; a segunda deve se abster porque o manual não informa salários. Esses são critérios de validação, não resultados já confirmados no serviço real.

Para um documento local, com a chave configurada no `.env` ignorado pelo Git:

```powershell
uv run python -m scripts.rag_demo --file ./documento.pdf
```

Sem `--question`, o comando aceita perguntas interativamente; use `/sair` para encerrar. É necessário ter o arquivo no ambiente onde o comando roda. O conteúdo extraído e as perguntas são enviados à NVIDIA: use documentos sintéticos, não dados sensíveis.

O comando mantém trechos e vetores apenas na memória do processo, diferente das sessões temporárias da interface. O limite é de cinco tentativas por execução, inclusive falhas do provedor, com até 80 trechos e perguntas de até 1000 caracteres. Reiniciar o comando reinicia a contagem; suas chamadas privadas não entram no orçamento das rotas públicas.

As chamadas têm timeout e erros sanitizados de autenticação, indisponibilidade e rate limit. Sem chave, o comando falha antes de qualquer chamada. Testes locais usam respostas simuladas; disponibilidade da conta, latência, qualidade em português e termos para publicação precisam ser verificados no ambiente real.

### Diagnóstico nos logs do Coolify

Falhas geram avisos com `nvidia_failure` ou `rag_failure`, indicando `stage` e `code`. Rejeições HTTP incluem o status retornado pela NVIDIA; falhas de rede distinguem `timeout` de `network_error`. Respostas inválidas indicam JSON, estrutura ou término incompleto, com `finish_reason` limitado a valores conhecidos. Validação de fontes e incompatibilidade de embeddings também são identificadas. `demo_rag_failed operation=question` ou `operation=document` identifica a operação da interface que falhou.

Exemplos ilustrativos, não diagnóstico já confirmado em produção:

```text
nvidia_failure stage=generation code=nvidia_rate_limited http_status=429
nvidia_failure stage=answer_validation code=nvidia_invalid_answer reason=completion_not_finished finish_reason=length
demo_rag_failed operation=question
```

Os logs não incluem chave, token de sessão, pergunta, texto do documento, resposta do modelo ou corpo de erro do provedor. A mensagem pública e as regras de tentativas permanecem iguais. Após publicar a atualização, reproduza uma única falha e confira os avisos imediatamente anteriores ao `503`; o log HTTP sozinho não identifica a causa.

## Fundação existente (Sprint 1 original)

API FastAPI multi-tenant com PostgreSQL/pgvector, Redis/Celery preparado e suporte a MinIO privado. A fundação entrega autenticação, memberships, coleções e upload. Documentos dessa API continuam `pending`: não há integração com o motor RAG ou worker de ingestão. A demo anônima tem fluxo separado em `/v1/demo`, sem contas e coleções.

## Rodar com Docker (fluxo principal)

Requer Docker com Compose v2 recente. O Compose usa credenciais conhecidas de demonstração local; não exponha este ambiente à internet. `.env` é opcional. Para definir senhas próprias, copie o exemplo antes de subir:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Em outro terminal, o seed é executado explicitamente e é idempotente:

```powershell
docker compose run --rm migrate python scripts/seed_demo.py
```

A API fica em `http://localhost:8000`, com contratos interativos em `/docs`.

O Compose sobrescreve dentro dos containers as URLs de Postgres, Redis e MinIO para usar os nomes dos serviços. O `.env.example` usa `localhost` para o fluxo sem Docker e não é usado como `env_file` obrigatório pelo Compose.

Para o teste opt-in de integração de serviços, monte os testes e habilite explicitamente a variável:

```powershell
docker compose run --rm -e RUN_SERVICE_TESTS=1 -v "${PWD}/tests:/app/tests:ro" api uv run --frozen --group dev pytest tests/test_services.py
```

Esse comando instala o grupo dev no container via `uv`, usa os serviços do Compose e verifica PostgreSQL/pgvector, Redis e MinIO. Os testes de serviço não fazem parte do fluxo padrão.

## Fluxo local sem Docker

Requer Python 3.12+ e `uv`. O exemplo usa SQLite para desenvolvimento e testes de regras; o banco de referência é PostgreSQL no Compose. Migrações, seed e login funcionam sem os outros serviços. Para upload funcionar, é necessário um MinIO acessível em `S3_ENDPOINT`, com bucket privado `S3_BUCKET` já criado; o worker também requer Redis.

```powershell
Copy-Item .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/seed_demo.py
uv run uvicorn app.main:app --reload
```

## Endpoints e isolamento

`POST /v1/auth/login` recebe `{email,password}` e retorna somente Bearer: `access_token`, `token_type`, `expires_in`, `user_id` e `tenants` (`id`, `name`, `role`). O tenant selecionado vem de `X-Tenant-ID`, validado contra a membership do usuário; não vem do payload. Envie o token em `Authorization: Bearer <access_token>`.

No Swagger (`/docs`), autorize com o token e preencha o campo obrigatório `X-Tenant-ID` em `POST /v1/collections` com um ID retornado no login. Sem esse header, a API retorna `422` de validação; enviar `tenant_id` no JSON não o substitui.

Exemplo PowerShell 7 usando as senhas padrão locais (substitua a senha se alterou o `.env`):

```powershell
$login = Invoke-RestMethod http://localhost:8000/v1/auth/login -Method Post -ContentType 'application/json' -Body (@{email='owner.a@example.test';password='change-me-owner'} | ConvertTo-Json)
$tenantId = $login.tenants[0].id
$headers = @{ Authorization = "Bearer $($login.access_token)"; 'X-Tenant-ID' = $tenantId }
Invoke-RestMethod http://localhost:8000/v1/collections -Method Get -Headers $headers
$collection = Invoke-RestMethod http://localhost:8000/v1/collections -Method Post -Headers $headers -ContentType 'application/json' -Body '{"name":"Documentos de teste"}'
```

Com um arquivo sintético `documento.txt` no diretório atual, envie e consulte o status:

```powershell
$upload = Invoke-RestMethod "http://localhost:8000/v1/collections/$($collection.id)/documents" -Method Post -Headers $headers -Form @{file=Get-Item ./documento.txt}
Invoke-RestMethod "http://localhost:8000/v1/documents/$($upload.document_id)" -Headers $headers
```

`POST /v1/auth/logout` revoga a sessão. A sessão é opaca, armazenada por hash e vinculada ao usuário; `X-Tenant-ID` apenas seleciona um tenant entre suas memberships. Cada operação revalida o acesso no banco. `POST /v1/collections` cria com esse seletor; `GET /v1/collections` lista todas as coleções autorizadas do usuário. IDs de outro tenant retornam `404` para não confirmar existência. Owner/editor criam e enviam; viewer apenas lê.

`GET /v1/collections/{id}/documents?page=1&page_size=50` lista documentos (página até 1.000.000, tamanho de 1 a 100). `GET /v1/documents/{id}` retorna status, páginas e erro sanitizado. `/health/live` verifica o processo; `/health/ready` verifica acesso ao schema no banco, não a disponibilidade de Redis/MinIO.

O seed cria três usuários e dois tenants: `owner.a@example.test` é owner de Demo Alpha, `owner.b@example.test` é owner de Demo Beta e `viewer.a@example.test` é viewer somente de Demo Alpha. As senhas vêm de `settings()` carregando `.env`; o script imprime apenas `id`, `email` e `role`, nunca senhas.

O seed não altera senhas de usuários existentes. Alterar as variáveis de senha e executá-lo novamente não rotaciona essas credenciais.

Uploads aceitos: PDF com assinatura e contagem de páginas, DOCX com estrutura XML validada e TXT UTF-8. Não se confia no Content-Type informado pelo cliente. O limite padrão é 20 MB/200 páginas de PDF; configure `MAX_UPLOAD_BYTES` e `MAX_PDF_PAGES` no `.env`. A detecção de PDF escaneado depende da extração, na Sprint 2. Se MinIO falhar, o registro permanece rastreável como `failed` com `storage_upload_failed`.

## Verificações

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Se o pytest encontrar erro de permissão no diretório temporário padrão do Windows, execute `uv run pytest --basetemp=.pytest_cache/tmp`. Esse diretório é descartável. A suíte cobre isolamento, papéis, revogação, arquivos inválidos/limites, falha de storage, migrações de ida e volta e seed idempotente; três testes de serviços ficam ignorados sem `RUN_SERVICE_TESTS=1`.

As verificações locais cobrem SQLite; Postgres/pgvector, Redis, Celery e MinIO exigem Docker/serviços disponíveis. Não há alegação de validação Postgres sem executar o Compose.

Cadastro público, busca, exclusão e ingestão dos uploads da API autenticada não foram implementados; os usuários dessa API vêm do seed. RLS e ACL por coleção não foram adicionados. Para essa fundação ainda são necessários proteção contra brute force/rate limiting e revisão dos segredos de demonstração. Diferentemente do upload autenticado, as rotas anônimas `/v1/demo` enviam texto e perguntas à NVIDIA quando habilitadas. Use TLS e limites de corpo/conexões no proxy.
