# RAG do zero

[Ler o artigo passo a passo](rag-artigo.html)

Projeto pequeno para entender o fluxo básico de Retrieval-Augmented Generation:

```text
documento → chunks → embeddings → FAISS → contexto → resposta
```

O projeto usa um documento local, um modelo de embeddings local, busca vetorial em memória e um modelo local para gerar a resposta.

## Executar no Windows

No PowerShell, dentro desta pasta:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe rag.py --question "Quais são os dias de trabalho remoto?"
```

Na primeira execução, os modelos serão baixados. Depois, faça outras perguntas:

```powershell
.venv\Scripts\python.exe rag.py --question "Quantos dias de férias os funcionários recebem?"
.venv\Scripts\python.exe rag.py --question "Qual é o plano odontológico?"
```

A última pergunta não está no documento e deve resultar em uma recusa.

## O que observar

- `split_text` divide o documento em partes menores.
- `SentenceTransformer` transforma texto em vetores.
- `FAISS` recupera os chunks mais semelhantes à pergunta.
- O prompt obriga o modelo a usar somente o contexto recuperado.
- As fontes recuperadas aparecem antes da resposta para facilitar a inspeção.

## Prática sugerida

1. Faça três perguntas respondíveis.
2. Faça duas perguntas que não existem no documento.
3. Altere `chunk_size` e observe as fontes recuperadas.
4. Adicione uma nova política ao arquivo `knowledge.txt` e repita a consulta.
5. Leia o código inteiro e explique o caminho de uma pergunta até a resposta.
