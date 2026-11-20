# RAG do zero

[Ler o artigo passo a passo](rag-artigo.html)

Estudo com duas versões para entender recuperação e geração de respostas:

```text
rag.py: documento → parágrafos → embeddings → FAISS → trecho mais semelhante
rag_colab.ipynb: documento → chunks → embeddings → FAISS → contexto → Qwen → resposta
```

O script local `rag.py` faz busca semântica e devolve o primeiro trecho recuperado, sem modelo de geração ou prompt. O [notebook no Colab](rag_colab.ipynb) e o [artigo](rag-artigo.html) mostram a versão RAG com geração pelo Qwen.

## Executar no Windows

No PowerShell, dentro desta pasta:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe rag.py --question "Quais são os dias de trabalho remoto?"
```

Na primeira execução, o modelo de embeddings será baixado. Depois, faça outras perguntas:

```powershell
.venv\Scripts\python.exe rag.py --question "Quantos dias de férias os funcionários recebem?"
.venv\Scripts\python.exe rag.py --question "Qual é o plano odontológico?"
```

A última pergunta não está no documento. O script só retorna uma recusa quando nenhum trecho atinge o limiar de similaridade `min_score=0.5`; esse corte não garante que o trecho recuperado contenha a resposta.

## O que observar

- `split_text` usa cada parágrafo como um trecho, sem configuração de tamanho ou sobreposição.
- `SentenceTransformer` transforma texto em vetores.
- `FAISS` recupera os chunks mais semelhantes à pergunta.
- `generate_answer` devolve o primeiro trecho recuperado; no script local não há geração de texto.
- As fontes recuperadas aparecem antes da resposta para facilitar a inspeção.

## Prática sugerida

1. Faça três perguntas respondíveis.
2. Faça duas perguntas que não existem no documento.
3. Altere os parágrafos do documento ou `--top-k` e observe as fontes recuperadas. O script continua devolvendo somente o primeiro trecho como resposta.
4. Adicione uma nova política ao arquivo `knowledge.txt` e repita a consulta.
5. Leia o código inteiro e explique o caminho de uma pergunta até a resposta.
