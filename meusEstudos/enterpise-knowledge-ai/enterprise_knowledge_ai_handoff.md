# Enterprise Knowledge AI — Handoff de implementação

**Versão:** 1.0  
**Perfil:** desenvolvedor experiente migrando para AI Engineer júnior  
**Prazo-alvo:** quatro semanas (semanas 3–6 da trilha), ajustável conforme disponibilidade  
**Status:** especificação inicial; decisões sujeitas a validação por benchmarks

## 1. Resultado esperado

Uma plataforma multi-tenant de conhecimento em que um usuário autenticado cria uma coleção, envia PDFs/DOCX/TXT, acompanha a ingestão, faz perguntas e recebe respostas com citações clicáveis (arquivo, página e trecho). A plataforma mede qualidade de retrieval, latência, custo aproximado de geração e falhas; não permite que um usuário acesse documentos de outro.

### Definition of Done

- `docker compose up --build` sobe API, PostgreSQL/pgvector, Redis, worker e MinIO; interface pode ser adicionada ao final.
- Migrações aplicadas de forma reproduzível e dados de teste gerados por script.
- Autenticação implementada e autorização em todos os endpoints de leitura/escrita.
- Upload de PDF com texto, DOCX e TXT; arquivos inválidos são recusados.
- Ingestão assíncrona idempotente, com estados e registro de falhas.
- Busca lexical, vetorial e híbrida comparáveis usando mesmo corpus.
- Resposta produzida apenas com trechos permitidos, retornando citações persistentes; ausência de evidência provoca abstenção.
- Teste automático de isolamento cross-tenant, revogação de acesso, prompt injection e deleção.
- Dataset com pelo menos 50 perguntas e avaliações automatizadas; resultados reais reportados sem prometer limiares arbitrários.
- CI executa lint, testes e migrations; README permite reproduzir a demo.

## 2. Escopo

### MVP (obrigatório)
1. Registro/login ou OIDC; tenants (organizações) e associação do usuário a um tenant.
2. Coleções pertencentes ao tenant; permissões iniciais de owner/editor/viewer.
3. Upload de PDF textual/DOCX/TXT (limite inicial 20 MB e 200 páginas por arquivo, configurável).
4. Processamento assíncrono: validação, extração, normalização, chunking, embeddings e persistência.
5. Busca por tenant/coleção usando pgvector e PostgreSQL full text, com RRF.
6. Perguntas e respostas com citações que incluem `document_id`, `chunk_id`, página e offsets quando disponíveis.
7. Endpoints de listagem/status/exclusão; deleção de chunks/embeddings e arquivo associado.
8. Logs/traces, métricas, testes e avaliação de retrieval.

### Fora do MVP
- OCR de PDFs escaneados; tabelas complexas e imagens; conectores externos (Drive, SharePoint).
- Fine-tuning, GraphRAG, múltiplos agentes, memory de longo prazo e tarefas automáticas de escrita.
- SSO empresarial, cobrança, limites de planos, produção certificada/compliance formal.

## 3. Arquitetura

```
Next.js Web UI ───> FastAPI ──────> PostgreSQL + pgvector
                         │                   │
                         ├──> Redis Queue --> Celery Worker
                         │                        │
                         ├──> MinIO/S3 <──────────┤
                         │                        └──> Embedding Provider
                         └──> Retrieval + RRF --> LLM Provider
                                      │
                                 Langfuse/OTel
```

**Fluxo de ingestão:** API valida identidade/tenant, MIME real, tamanho e quota; registra documento como `pending`, envia arquivo a storage privado e publica job. Worker extrai texto e paginação, normaliza, gera chunks com metadados, calcula embeddings em lotes, grava dados via transação e marca `ready`. Falha resulta em `failed` com motivo sanitizado, tentativas limitadas e retry exponencial. Reprocessar o mesmo arquivo deve ser idempotente por `(tenant_id, collection_id, sha256, parser_version, embedding_model)`.

**Fluxo de pergunta:** API autentica, autoriza coleção, incorpora query, busca candidatos lexicais e vetoriais **já filtrados por tenant e permissões**, funde rankings com RRF, opcionalmente reranqueia, envia trechos tratados como dados não confiáveis ao LLM, valida citações contra a lista de chunks entregues e devolve resposta ou abstenção. Registra métricas sem armazenar conteúdo sensível por padrão.

## 4. Estrutura do repositório

```
enterprise-knowledge-ai/
├── apps/
│   ├── api/app/
│   │   ├── main.py
│   │   ├── core/{config.py,security.py,observability.py}
│   │   ├── api/v1/{auth.py,collections.py,documents.py,search.py,chat.py}
│   │   ├── db/{models.py,session.py}
│   │   ├── schemas/
│   │   ├── services/{storage.py,ingestion.py,chunking.py,embeddings.py,retrieval.py,generation.py}
│   │   └── repositories/
│   ├── worker/{celery_app.py,tasks.py}
│   └── web/                       # fase final
├── migrations/
├── evals/{datasets/,run_retrieval.py,run_generation.py}
├── tests/{unit/,integration/,security/,e2e/}
├── infra/{docker-compose.yml,Dockerfile.api,Dockerfile.worker}
├── scripts/{seed_demo.py,generate_eval_set.py}
├── docs/{architecture.md,adr/,security.md,benchmarks.md,runbook.md}
├── .github/workflows/ci.yml
├── .env.example
├── pyproject.toml
└── README.md
```

## 5. Modelo de dados

| Tabela | Campos essenciais | Notas |
|---|---|---|
| `tenants` | `id`, `name`, `created_at` | organização isolada |
| `users` | `id`, `email`, `password_hash` ou `oidc_subject`, `created_at` | identidade |
| `memberships` | `tenant_id`, `user_id`, `role` | roles: owner/editor/viewer |
| `collections` | `id`, `tenant_id`, `name`, `created_by` | limite de acesso |
| `documents` | `id`, `tenant_id`, `collection_id`, `owner_id`, `filename`, `mime`, `sha256`, `storage_key`, `status`, `error_code`, `created_at` | `pending/processing/ready/failed/deleted` |
| `document_chunks` | `id`, `tenant_id`, `collection_id`, `document_id`, `ordinal`, `content`, `page_start`, `page_end`, `token_count`, `embedding`, `search_vector`, `metadata` | índice vetorial e GIN |
| `ingestion_jobs` | `id`, `tenant_id`, `document_id`, `status`, `attempts`, `started_at`, `finished_at` | idempotência e retry |
| `query_logs` | `id`, `tenant_id`, `user_id`, `collection_id`, `latency_ms`, `retrieved_count`, `model`, `estimated_cost`, `created_at` | não registrar conteúdo por padrão |
| `citation_events` | `query_log_id`, `document_id`, `chunk_id`, `page` | evidência e auditoria |

**Índices/constraints:** FK e índices compostos `(tenant_id, collection_id)` em todas as tabelas de conteúdo; HNSW `vector_cosine_ops` em `embedding` (dimensão fixada pelo modelo); GIN em `search_vector`; unique em chaves de idempotência. Escolher `to_tsvector('portuguese', content)` para corpus em português, configurável para corpus multilíngue. Dimensionar tipo `vector(N)` de acordo com o provedor escolhido, registrando `embedding_model` e versão: trocar de modelo exige reindexação.

**Segurança de dados:** o tenant deve ser derivado do token/sessão, nunca confiado ao payload. Filtro de autorização antes do `LIMIT` da busca vetorial/textual; se PostgreSQL RLS for adotado, ele complementa testes de autorização na aplicação. Filtros de documento/coleção precisam ser aplicados em ambos os ramos da busca. URLs para objetos devem ser assinadas e curtas. Evitar armazenamento de texto original em logs e traces.

## 6. Contratos REST v1

| Método | Endpoint | Body / resposta |
|---|---|---|
| `POST` | `/v1/auth/login` | credenciais → access token (ou OIDC) |
| `POST` | `/v1/collections` | `{name}` → `{id,name}` |
| `GET` | `/v1/collections` | coleções autorizadas |
| `POST` | `/v1/collections/{id}/documents` | `multipart/form-data: file` → `202 {document_id,status}` |
| `GET` | `/v1/collections/{id}/documents` | lista paginada |
| `GET` | `/v1/documents/{id}` | estado, páginas e erro sanitizado |
| `DELETE` | `/v1/documents/{id}` | `204`; remove dados derivados e objeto |
| `POST` | `/v1/collections/{id}/search` | `{query,mode,top_k}` → chunks autorizados com metadados |
| `POST` | `/v1/collections/{id}/ask` | `{question,top_k}` → resposta com citações |
| `GET` | `/health/live` e `/health/ready` | liveness/readiness |

**Resposta ilustrativa de `/ask`:**

```json
{
  "answer": "A política exige aprovação do gestor para valores acima do limite descrito [1].",
  "grounded": true,
  "citations": [
    {"ref": 1, "document_id": "uuid", "chunk_id": "uuid", "filename": "politica.pdf", "page_start": 3, "page_end": 3, "snippet": "..."}
  ],
  "retrieval": {"mode": "hybrid", "top_k": 6},
  "metrics": {"latency_ms": 1240, "estimated_cost_usd": 0.0012}
}
```

*Valores acima são exemplos de formato, não resultados medidos.* Se evidência não for suficiente: `grounded=false`, `answer="Não encontrei evidência suficiente nos documentos disponíveis."`, `citations=[]`.

## 7. Algoritmo de retrieval

1. Normalizar consulta e validar tamanho.
2. Extrair embedding com mesmo modelo/dimensão dos chunks.
3. Selecionar candidatos lexicais (`websearch_to_tsquery`/`plainto_tsquery`, GIN, `ts_rank_cd`) e vetoriais (`embedding <=> query_embedding`, HNSW), ambos com filtro de tenant, coleção e ACL.
4. Buscar inicialmente 30–50 candidatos por ramo, variar em benchmark.
5. Aplicar RRF: `score(d) = Σ 1/(k + rank_i(d))`, com `k=60` inicial; unir por `chunk_id`.
6. Remover duplicatas quase idênticas; opcional reranker top 20 → top 6.
7. Construir prompt com fontes identificadas; não obedecer comandos presentes nos documentos.
8. Exigir citações com identificadores pré-aprovados e verificar referências retornadas.
9. Abster-se quando não houver evidência; não tratar similaridade como probabilidade de verdade.

Medir separadamente `vector`, `lexical` e `hybrid`. HNSW pode sofrer com filtros seletivos; validar recall após aplicação de tenant/coleção e ajustar índices/consultas conforme o corpus.

## 8. Chunking e extração

- PDF textual: extrair por página, preservar número da página e hash da fonte.
- DOCX: preservar ordem dos parágrafos/títulos; registrar localização por seção quando não houver página.
- TXT: normalizar codificação e quebras.
- Segmentação inicial: 500–800 tokens, overlap de 80–120, respeitando parágrafos; comparar contra baseline simples.
- Guardar versão do parser, chunker e modelo; permitir reprocessar e comparar resultados.
- PDF escaneado: retornar status `unsupported_scanned_pdf` no MVP; OCR é backlog.
- Impor limites de arquivo, tokenização e uso por tenant para evitar abuso e contas inesperadas.

## 9. Métricas e evals

**Dataset:** pelo menos 50 perguntas com `question`, `tenant_id`, `collection_id`, `relevant_document_ids`, `relevant_chunk_ids` (se possível), `reference_answer`, `answerable`. Incluir perguntas factuais, paráfrases, perguntas sem resposta, ambiguidades, termos exatos e tentativas cross-tenant. Revisar manualmente rótulos.

**Retrieval:** recall@5, recall@10, MRR@10, precision@k (se relevância rotulada); comparação lexical/vetorial/híbrido. **Geração:** taxa de respostas com citações válidas, groundedness amostrada/avaliada, taxa de abstenção correta, respostas infundadas. **Operação:** latência p50/p95 por etapa, erros por 100 requisições, tokens e custo estimado por pergunta, throughput de ingestão.

**Metas iniciais de experimento, não garantias:** atingir 100% de bloqueio nos testes conhecidos de acesso cross-tenant; 100% de citações com IDs válidos quando presentes; aumento de recall@5 do híbrido em relação ao melhor baseline sempre que demonstrável no corpus. Publicar resultados mesmo quando híbrido não vencer.

## 10. Segurança mínima

- Validar autorização a cada consulta, inclusive URL de arquivo e download de citações.
- Aplicar least privilege, segredos via variáveis/secret manager, limites de consumo e rate limit.
- Tratar documento recuperado como **dado não confiável**, nunca como comando de sistema; testar prompt injection em documentos.
- Não enviar documentos a provedor externo sem deixar claro no README; para demo usar dados sintéticos ou licenciados.
- Sanitizar nomes de arquivos e MIME, impedir path traversal, bloquear arquivos perigosos; AV/scan é melhoria planejada.
- Apagar documento implica apagar chunks, embeddings, versões derivadas, objetos e invalidar cache; registrar evento de exclusão sem reter conteúdo.
- Autenticação e autorização devem ser validadas na aplicação, não delegadas ao LLM.
- Nunca expor stack traces nem prompts internos para o usuário final.

Referência: OWASP RAG Security Cheat Sheet e OWASP LLM01:2025 Prompt Injection.

## 11. Plano de quatro sprints

### Sprint 1 — Fundamentos (semana 3)
- [ ] Criar monorepo, Docker Compose, API, PostgreSQL/pgvector, Redis e MinIO.
- [ ] Criar migrations e testes de conexão.
- [ ] Implementar auth, membership, collections e autorização; começar com dois tenants no seed.
- [ ] Implementar upload e estados dos documentos.
- [ ] **Demo:** dois usuários isolados conseguem criar coleções e enviar arquivos.

### Sprint 2 — Ingestão e busca (semana 4)
- [ ] Worker idempotente para PDF/DOCX/TXT.
- [ ] Extração, chunking, embeddings, armazenamento e índices.
- [ ] Endpoints `/search` nos modos lexical/vetorial/híbrido.
- [ ] Dataset inicial com 20 perguntas e testes cross-tenant.
- [ ] **Demo:** documentos prontos aparecem em buscas filtradas; resultados mostram fonte e página.

### Sprint 3 — Respostas e qualidade (semana 5)
- [ ] Endpoint `/ask`, prompt com trechos e retorno estruturado.
- [ ] Validador de citações e abstenção.
- [ ] Dataset ampliado a 50+ questões e métricas de retrieval.
- [ ] Testes de prompt injection, deleção e revogação.
- [ ] **Demo:** resposta fundamentada e pergunta sem evidência que se abstém.

### Sprint 4 — Produção e portfólio (semana 6)
- [ ] Tracing/metricas e relatório comparativo.
- [ ] GitHub Actions, smoke test, README, ADRs e threat model.
- [ ] Deploy de API/demo com credenciais de demonstração e documentos sintéticos.
- [ ] UI básica de upload/status/pergunta/citações, se houver tempo.
- [ ] **Demo final:** onboarding → upload → indexação → pergunta → citação → métricas → exclusão.

## 12. Testes obrigatórios de aceite

1. Usuário A faz upload e consulta documento do tenant A: `200`, fonte correta.
2. Usuário B consulta documento, coleção ou ID do tenant A: `403` ou `404`; zero chunks de A chegam ao LLM.
3. Remoção de membro da coleção/tenant bloqueia consultas posteriores, mesmo com sessão válida.
4. PDF inválido e arquivo acima do limite são rejeitados.
5. Repetição do job não duplica chunks; falha de embedding é recuperável.
6. Documento apagado não aparece mais em busca, citações ou download.
7. Resposta com fonte inexistente é rejeitada por validação.
8. Pergunta sem evidência gera abstenção.
9. Documento contendo "ignore todas as instruções" não muda política nem acessos.
10. CI executa e reporta métricas comparativas no corpus fixado.

## 13. Backlog pós-MVP

- LangGraph com planejamento controlado de buscas (somente após benchmark evidenciar necessidade).
- Reranker cross-encoder; reescrita de consultas; busca multilíngue.
- Permissões por documento e compartilhamento entre coleções.
- OCR e extração de tabelas; ingestão incremental/versionamento.
- Observabilidade avançada, quotas por tenant, cache seguro, custo por cliente.
- Deploy com infraestrutura como código e teste de carga.

## 14. Issues iniciais para abrir no GitHub

1. `chore: bootstrap FastAPI monorepo and Compose`
2. `feat(auth): tenant membership and authorization`
3. `feat(collections): CRUD scoped to current tenant`
4. `feat(documents): signed upload and state machine`
5. `feat(ingestion): Celery extraction and idempotent indexing`
6. `feat(embeddings): provider abstraction and pgvector schema`
7. `feat(retrieval): lexical, vector and hybrid RRF`
8. `feat(qa): grounded answers and validated citations`
9. `test(security): tenant isolation and injection cases`
10. `feat(evals): reproducible retrieval benchmarks`
11. `chore(observability): traces, latency and cost`
12. `ci: lint, tests, migrations and deploy workflow`
13. `docs: architecture, benchmarks, runbook and demo`

## 15. Prompt de handoff para assistente de programação

> Você é meu tech lead para construir o **Enterprise Knowledge AI**, conforme este handoff. Use Python/FastAPI, PostgreSQL+pgvector, SQLAlchemy/Alembic, Celery/Redis, MinIO, Docker Compose e pytest. Comece somente pela Sprint 1. Antes de codificar, mostre a árvore de arquivos, entidades e contratos dos endpoints. Em seguida implemente verticalmente, com migrations, testes e comandos para rodar localmente. Não implemente agentes, OCR nem bibliotecas adicionais sem justificativa. Toda consulta deve ser tenant-safe e a identidade deve vir da sessão autenticada. Ao finalizar cada issue, forneça arquivos alterados, passos de verificação, testes executados e pendências. Nunca afirme que testes passaram sem executá-los. Priorize arquitetura compreensível, observabilidade e reprodutibilidade.

## 16. Fontes e referências

- Artigo motivador: https://amanxai.com/2026/10/09/40-ai-projects-that-show-real-ai-engineering-skills/
- pgvector hybrid search: https://github.com/pgvector/pgvector/blob/master/README.md
- OWASP RAG Security: https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
- OWASP Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/

**Princípio de arquitetura:** construir um RAG determinístico, auditável e seguro antes de adicionar agentic RAG.
