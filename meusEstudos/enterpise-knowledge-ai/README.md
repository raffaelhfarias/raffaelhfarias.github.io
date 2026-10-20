# Knowledge AI — perguntas sobre documentos

Demo de portfólio que permite enviar um PDF ou DOCX e fazer até **cinco tentativas de pergunta**. O sistema recupera trechos do documento, gera uma resposta com fontes e se abstém quando o modelo não indica evidência suficiente.

**Objetivo:** demonstrar um fluxo RAG de ponta a ponta, com uma interface acessível a recrutadores e visitantes, sem cadastro. Não é uma plataforma empresarial pronta para comercialização.

- **[Experimentar a demo](https://7cgxisdn5j0nlskxuxjewivm.coolify.cogni.qzz.io/)** · **[Documentação da API](https://7cgxisdn5j0nlskxuxjewivm.coolify.cogni.qzz.io/docs)**
- **Entrada:** um documento textual e uma pergunta em português.
- **Saída:** resposta com trechos consultáveis ou uma mensagem de abstenção.
- **Stack:** Python, FastAPI, SQLAlchemy, PostgreSQL em produção, APIs NVIDIA e HTML/CSS/JavaScript sem framework de frontend.

## Experimente em um minuto

1. Abra a demo e escolha o exemplo fictício **Manual da equipe Aurora**, ou envie um PDF textual/DOCX sem dados sensíveis.
2. Aguarde o processamento e faça uma pergunta sobre o conteúdo.
3. Confira os trechos apresentados como fontes, não apenas a resposta.
4. Teste uma pergunta cuja resposta não está no documento.

A interface inclui histórico visual das perguntas, cópia de respostas e alternância claro/escuro. As perguntas são independentes: o histórico não é enviado como contexto de conversa ao modelo.

### Exemplo reproduzível, sem depender do site

O manual fictício informa que o prazo para solicitar reembolso é de **15 dias corridos após a despesa**, exige nota fiscal e identifica Marina como gestora responsável. Não informa salários.

| Pergunta | Comportamento esperado |
| --- | --- |
| Qual é o prazo para solicitar reembolso? | Informar 15 dias corridos e citar o trecho correspondente. |
| Qual é o salário da gestora? | Responder “Não encontrei informações suficientes no documento para responder.”, sem fontes. |

Esses são critérios esperados para o exemplo incluído no [script de demonstração](scripts/rag_demo.py), não uma medição de acurácia do modelo.

## Executar localmente

Requisitos: Python 3.12 ou superior e `uv`. Para experimentar a interface completa, é necessária uma chave NVIDIA com acesso aos modelos configurados. Não é necessário ter GPU local, Redis ou MinIO para a demo.

Na pasta deste projeto, em PowerShell:

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

No `.env` local, configure `NVIDIA_API_KEY` e `DEMO_ENABLED=true`. Preserve `DATABASE_URL=sqlite:///./local.db` para o teste local. O `.env` é ignorado pelo Git: não publique sua chave.

```powershell
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Abra `http://127.0.0.1:8765/`; a API fica em `/docs`. Sem habilitar a demo e configurar a chave, a página pode ser visualizada, mas o processamento RAG não estará disponível. O seed de usuários da API autenticada não é necessário para este fluxo.

### Executar apenas o RAG pelo terminal

Com a chave configurada, sem precisar de banco:

```powershell
uv run python -m scripts.rag_demo --example --question "Qual é o prazo para solicitar reembolso?" --question "Qual é o salário da gestora?"
uv run python -m scripts.rag_demo --file ./documento.pdf
```

Sem `--question`, o script abre uma sessão interativa; use `/sair` para encerrar. O CLI também aceita TXT e mantém os dados somente na memória do processo. São cinco tentativas por execução; os orçamentos da API pública não se aplicam ao CLI.

## Como funciona

```text
PDF / DOCX ou exemplo fictício
  → validação e extração de texto
  → divisão em trechos com sobreposição
  → embeddings NVIDIA
  → trechos e vetores na sessão temporária

Pergunta
  → embedding NVIDIA
  → busca dos quatro trechos mais similares
  → geração NVIDIA com esses trechos
  → validação da resposta e dos IDs das fontes
  → resposta com fontes ou abstenção
```

- **Extração:** `pypdf` para PDFs e leitura do XML de DOCX. Não há OCR.
- **Chunking:** janelas de até 1.000 caracteres, com avanço de 850; no PDF, a divisão respeita cada página.
- **Recuperação:** produto escalar de vetores normalizados, equivalente à similaridade de cosseno, sobre até 80 trechos. Retorna os quatro melhores, sem reranker ou limiar de relevância calibrado.
- **Geração:** recebe pergunta e trechos como contexto e deve retornar JSON com resposta e IDs das fontes. Não utiliza ferramentas externas nem agentes.
- **Validação:** rejeita estrutura inválida e IDs fora dos trechos recuperados. Sem IDs de fontes, retorna a abstenção padrão.

**Validar um ID de fonte não comprova que o texto citado sustenta cada afirmação.** O usuário ainda precisa conferir as evidências.

### Decisões e trade-offs

| Escolha | Motivo e limite aceito |
| --- | --- |
| Frontend estático servido pelo FastAPI | Um único deploy para uma interface pequena. Não exige SPA ou serviço separado. |
| Embeddings e geração hospedados na NVIDIA | Dispensa GPU própria; aceita dependência de rede, disponibilidade, cotas e latência do provedor. |
| Busca exata em Python e vetores em JSON no banco | Suficiente para até 80 trechos por sessão. Não usa índice vetorial; reavaliar se o volume ou a concorrência crescerem. |
| Chunking por caracteres | Implementação simples e inspecionável; pode cortar contexto semântico. Uma alternativa deve ser comparada em avaliação antes de substituir. |
| Sessão anônima e temporária | Reduz atrito para quem visita o portfólio; não oferece contas, histórico permanente ou gestão de documentos. |

A demo não utiliza pgvector para recuperar trechos, embora a fundação original do repositório tenha suporte à extensão.

## Testes e avaliação: coisas diferentes

### Verificações automatizadas

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Se houver erro de permissão no temporário padrão do Windows, use `uv run pytest --basetemp=.pytest_cache/tmp`. Esse diretório é descartável.

A suíte cobre extração e limites, recuperação, validação de fontes, abstenção, erros do provedor, timeouts, isolamento e expiração das sessões, tentativas concorrentes, orçamentos compartilhados, frontend e migrações em SQLite. Também há testes da fundação autenticada.

Os testes do RAG usam **respostas simuladas do provedor**: verificam o comportamento do código, não a qualidade real do modelo. Três testes de integração com serviços externos são opcionais, habilitados por `RUN_SERVICE_TESTS=1`, e exigem os serviços da fundação disponíveis.

### Evidência manual e lacunas

Em testes manuais relatados pelo autor com um DOCX de política de reembolso, a aplicação respondeu **15 dias corridos** à pergunta sobre cancelamento e se absteve sobre um suposto cupom `PROMO100`. Outra consulta retornou **30 dias corridos** para o caso Enterprise com mais de 50 licenças, com referência ao trecho.

Essas observações demonstram exemplos de uso, **não comprovam qualidade geral**. Ainda não há conjunto rotulado de avaliação, comparação com busca por palavras-chave, métricas de recuperação/fidelidade ou medições consolidadas de latência e custo.

O próximo passo de qualidade é montar um conjunto pequeno de perguntas com respostas e evidências esperadas, incluindo casos respondíveis, fora do documento e de abstenção. Só então comparar recuperação, suporte das citações e respostas com uma baseline simples. Isso é trabalho pendente, não uma funcionalidade já entregue.

## Falhas reais e diagnóstico

Durante os testes de deploy, a geração retornou `404` porque a variável do modelo estava sem o prefixo `nvidia/`. Conferir a configuração efetivamente carregada permitiu corrigir o identificador no Coolify.

Também houve timeout de geração: uma pergunta falhou e uma posterior funcionou. O timeout de socket foi separado por etapa: **120 segundos para geração e 60 para embeddings**, sem retentativas automáticas. Essa mudança não garante disponibilidade nem representa um tempo máximo total da requisição.

Para distinguir falha de processamento, recuperação e geração, os logs registram etapa, código sanitizado e status HTTP quando disponível. Exemplo de timeout observado:

```text
nvidia_failure stage=generation code=nvidia_unavailable reason=timeout error_type=TimeoutError
demo_rag_failed operation=question
```

Os logs de diagnóstico não registram chave, token de sessão, perguntas, conteúdo do documento, respostas ou corpo de erro do provedor. Ainda não há monitoramento consolidado de tokens, custos ou latências. Um `503` sozinho não identifica a causa; consulte os avisos imediatamente anteriores.

## Limites e privacidade

- **Um documento por sessão**, até 20 MB, 200 páginas de PDF e 80 trechos extraídos; perguntas de até 1.000 caracteres. Os limites de bytes/páginas são configuráveis.
- **Cinco tentativas por sessão**, incluindo falhas do provedor. Não são cinco respostas bem-sucedidas garantidas.
- Orçamentos públicos padrão de **10 uploads e 50 perguntas por hora UTC**, compartilhados entre visitantes e persistidos no banco. Não são cotas individuais; uma reserva de upload pode ser consumida mesmo se o arquivo for inválido.
- Sessões expiram em **30 minutos**. A limpeza roda periodicamente enquanto a aplicação está ativa e antes de novos uploads. O cookie é HttpOnly, SameSite Strict e seguro em HTTPS; o banco guarda o hash do token.
- O arquivo original é descartado após a extração; os trechos e vetores ficam temporariamente no banco. Excluir a sessão remove seus registros ativos, não backups ou dados eventualmente retidos pelo provedor.
- **Texto extraído e perguntas são enviados à NVIDIA.** Use documentos sintéticos ou públicos, nunca dados pessoais, confidenciais ou de clientes.
- PDFs escaneados não são suportados; tabelas e layouts complexos podem perder estrutura. DOCX não oferece numeração confiável de páginas.
- O modelo pode errar mesmo com fontes. Instruções no documento são tratadas como conteúdo não confiável, mas não há promessa de imunidade a prompt injection.
- Não há streaming, fallback de modelo, proteção completa contra abuso ou garantia de serviço. Cotas e condições de uso da NVIDIA dependem da conta e do provedor.

## Configuração e deploy no Coolify

O projeto é uma subpasta do repositório do portfólio. O deploy usa o [Dockerfile](Dockerfile) existente e um recurso PostgreSQL na rede privada do Coolify.

| Configuração | Valor |
| --- | --- |
| Base directory | `/meusEstudos/enterpise-knowledge-ai` |
| Dockerfile location | `/Dockerfile` |
| Porta interna | `8000` |
| `DATABASE_URL` | URL privada do PostgreSQL, com driver `postgresql+psycopg` |
| `DEMO_ENABLED` | `true` |
| `NVIDIA_API_KEY` | Segredo de runtime, nunca no frontend ou Git |
| `NVIDIA_CHAT_MODEL` | `nvidia/nemotron-3.5-super-vl-120b-a12b` |
| `NVIDIA_EMBEDDING_MODEL` | `nvidia/nemotron-3-embed-1b` |

As variáveis prevalecem sobre os padrões do código. Os modelos são usados somente para texto. Ao trocar o modelo de embeddings, descarte sessões antigas e reprocesse os documentos; trocar somente o modelo de geração não exige refazer embeddings.

Na instalação ou quando houver novas migrações, execute **no terminal da aplicação**, não no PostgreSQL:

```sh
cd /app
alembic upgrade head
```

`/health/live` verifica o processo; `/health/ready` verifica acesso ao schema do banco, não a disponibilidade da NVIDIA. Use HTTPS e configure limites de corpo e conexões no proxy. A demo não precisa de Redis, Celery, MinIO nem seed de usuários para funcionar.

## Onde olhar no código

| Arquivo | Responsabilidade |
| --- | --- |
| [app/rag.py](app/rag.py) | Extração, chunking, recuperação e validação de fontes |
| [app/nvidia.py](app/nvidia.py) | Chamadas de embeddings/geração e erros sanitizados |
| [app/demo.py](app/demo.py) | API anônima, sessões, tentativas e orçamentos |
| [app/static/index.html](app/static/index.html) | Interface; CSS e JavaScript ficam na mesma pasta |
| [app/config.py](app/config.py) e [.env.example](.env.example) | Configuração e variáveis disponíveis |
| [migrations/versions/0002_demo.py](migrations/versions/0002_demo.py) | Schema das sessões e orçamentos da demo |
| [tests/test_rag.py](tests/test_rag.py) e [tests/test_demo.py](tests/test_demo.py) | Comportamento do RAG e da API pública |
| [tests/test_frontend.py](tests/test_frontend.py) e [tests/test_migrations.py](tests/test_migrations.py) | Interface e evolução do schema |

### Fundação anterior: fora do caminho da demo

A Sprint 1 original deixou autenticação, tenants, papéis, coleções e uploads privados em [app/main.py](app/main.py), com suporte a MinIO e configuração Redis/Celery. Essa API é separada das rotas `/v1/demo`: seus uploads permanecem `pending`, sem ingestão integrada ao RAG. Não é um sistema empresarial concluído.

O [compose.yaml](compose.yaml) atende essa fundação para desenvolvimento, não é requisito para a demo. Contém credenciais locais conhecidas e não deve ser exposto à internet. O [seed](scripts/seed_demo.py) cria usuários de teste, mas não rotaciona senhas existentes. O [handoff original](enterprise_knowledge_ai_handoff.md) registra o planejamento inicial; não deve ser interpretado como lista de funcionalidades implementadas.

## Autoria e foco do portfólio

Projeto conduzido por Raffael Farias, com assistência de IA no desenvolvimento. As decisões de reduzir o escopo a uma demo, utilizar a infraestrutura existente, configurar o ambiente, realizar o deploy e testar documentos foram conduzidas pelo autor. O objetivo é discutir o fluxo, suas decisões e falhas com transparência, não apresentar código assistido por IA como trabalho inteiramente manual.

Este README segue as diretrizes aplicáveis do [AI Engineering Field Guide — Portfolio](https://github.com/alexeygrigorev/ai-engineering-field-guide/tree/main/portfolio), especialmente [apresentação do projeto](https://github.com/alexeygrigorev/ai-engineering-field-guide/blob/main/portfolio/05-present-the-project.md): problema, demonstração, arquitetura, decisões, evidências, limitações e autoria. Avaliações quantitativas ficam explicitamente como próximas etapas.
