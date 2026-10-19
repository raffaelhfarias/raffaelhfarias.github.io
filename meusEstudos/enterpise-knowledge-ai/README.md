# Enterprise Knowledge AI — Sprint 1

API FastAPI multi-tenant com PostgreSQL/pgvector, Redis/Celery preparado e MinIO privado. Esta sprint entrega autenticação, memberships, coleções e upload seguro. Documentos ficam `pending`; não há ingestão, OCR, chunks, embeddings, busca ou UI.

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

Cadastro público, busca, exclusão de documentos e ingestão não foram implementados nesta sprint; os usuários da demo vêm do seed. RLS e ACL por coleção não foram adicionados. Antes de publicação externa ainda são necessários TLS, proteção contra brute force/rate limiting, limites de corpo no proxy e revisão dos segredos de demonstração. Nenhum documento é enviado a provedores de IA nesta etapa.
