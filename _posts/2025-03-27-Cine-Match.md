---
title: "Cine Match"
description: Um sistema de recomendação de filmes baseado em inteligência artificial, que traz sugestões personalizadas para você, sem complicação e de forma prática.
date: 2025-03-27 00:00:00 -0300
categories: [IA]
tags: [Sistema de Recomendação]
comments: true
image: https://raw.githubusercontent.com/raffaelhfarias/recomenda-o/refs/heads/main/Others/Screenshot%202025-04-16%20183406.png
---

> Link para o Dashboard. 👉 [Clique Aqui](https://recomenda-o-j3mfxmgdwbdydzvjbhbqob.streamlit.app/)
{: .prompt-info }

## 🌟 O que é o CineMatch?
Um sistema de recomendação de filmes baseado em inteligência artificial, que traz sugestões personalizadas para você, sem complicação e de forma prática.
A ideia é simples: você escolhe um filme e, automaticamente, o CineMatch traz sugestões de filmes com base no que mais combina com o que você já gosta.

## 🔍 Como funciona o CineMatch?
Escolha de um filme. A partir disso, o sistema trabalha para analisar esse filme e comparar com outros no banco de dados, identificando quais filmes têm mais semelhanças em termos de título, gêneros e descrição.

## Etapas:

1. **Coleta de dados**:
   - Usei a API do TMDB para coletar dados de filmes populares, incluindo título, gênero, descrição, avaliação e data de lançamento.
   - Esse processo garante que o CineMatch tenha acesso às informações mais recentes e precisas sobre os filmes.

2. **Pré-processamento dos dados**:
   - Organizei as informações de maneira que o sistema pudesse entender de forma mais eficiente, criando um "mix" entre título, gênero e descrição de cada filme.
   - Assim, conseguimos gerar recomendações baseadas em múltiplas características.

3. **Inteligência Artificial**:
   - Utilizamos o algoritmo TF-IDF (Term Frequency-Inverse Document Frequency) para analisar os textos dos filmes e gerar um vetor de características de cada um.
   - Depois, comparamos esses vetores para calcular a similaridade entre os filmes, gerando recomendações baseadas na similaridade.

4. **Recomendações**:
   - O sistema sugere filmes que têm mais a ver com o filme escolhido inicialmente.
   - Ele garante também que não haja filmes repetidos nas sugestões, trazendo uma experiência única a cada recomendação.

## 🚀 Entendendo na prática!
1. Escolha o filme que você mais gosta.
2. Deixe o CineMatch fazer o trabalho pesado e, em segundos, ele traz as recomendações de filmes com base nesse filme.
3. Descubra novos filmes que você vai amar!
É como ter um indicador de filmes pessoal, disponível sempre que você precisar.

## 💡 Por que esse projeto foi criado?
Encontrar um sistema simples e eficaz para descobrir novos filmes sem perder tempo navegando por milhares de opções.
**E também para motivos de estudos, projetos, enfim!**

## 🛠️ Tecnologias utilizadas

* **Python**: A linguagem principal para o desenvolvimento do sistema.
* **Streamlit**: Para criar uma interface simples e interativa.
* **Sklearn**: Usado para implementar o modelo de recomendação baseado em **TF-IDF** e **cosine similarity**.
* **API do TMDB**: A fonte de dados de filmes populares.
* **Pandas**: Para manipulação e pré-processamento de dados.
* **Requests**: Para fazer as requisições à API.

## 🤝 Contribua!
Esse projeto é só o começo! Se você tem ideias para melhorar o CineMatch, fique à vontade para contribuir.
Sugestões, melhorias e pull requests são sempre bem-vindos.

## 💬 Vamos conversar!
Adoraria ouvir sua opinião sobre o projeto. Tem algum filme que você acha que deveria ser incluído nas recomendações?
Ou talvez algum recurso novo que você gostaria de ver no CineMatch?
Me envie uma mensagem no [LinkedIn](https://www.linkedin.com/in/raffael-henrique-59922520a/).
