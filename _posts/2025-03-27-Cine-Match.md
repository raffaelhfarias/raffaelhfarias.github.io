---
title: "Cine Match"
description: Sistema de recomendação de filmes com Python e Streamlit, baseado em similaridade textual com TF-IDF.
date: 2025-03-27 00:00:00 -0300
categories: [Machine Learning]
tags: [Python, Machine Learning, Streamlit]
comments: true
image: https://raw.githubusercontent.com/raffaelhfarias/recomenda-o/refs/heads/main/Others/Screenshot%202025-04-16%20183406.png
pin: true
---

> Aplicação online: [abrir dashboard](https://recomenda-o-j3mfxmgdwbdydzvjbhbqob.streamlit.app/)
{: .prompt-info }

# Cine Match

O Cine Match é um sistema de recomendação de filmes que sugere títulos semelhantes com base em características textuais como nome, gêneros e descrição.

## Objetivo

Criar uma experiência simples para descoberta de filmes, permitindo que o usuário escolha um título e receba recomendações relevantes de forma rápida e prática.

## Como funciona

O sistema utiliza dados de filmes para gerar representações textuais e calcular similaridade entre títulos. A lógica considera informações como:

- título;
- gêneros;
- descrição;
- metadados complementares da base.

A partir disso, o modelo identifica quais filmes têm maior proximidade com a escolha inicial do usuário.

## Etapas do projeto

1. **Coleta de dados** com a API do TMDB;
2. **pré-processamento** e organização das informações relevantes;
3. **vetorização textual** com TF-IDF;
4. **cálculo de similaridade** para geração das recomendações;
5. **interface interativa** com Streamlit para consulta em tempo real.

## Tecnologias utilizadas

- **Python**;
- **Streamlit** para a interface web;
- **scikit-learn** para TF-IDF e similaridade por cosseno;
- **Pandas** para manipulação dos dados;
- **Requests** para consumo da API do TMDB.

## Valor do projeto

- demonstra aplicação prática de sistema de recomendação;
- transforma um conceito de machine learning em produto utilizável;
- combina modelagem, tratamento de dados e interface de apresentação.

## Contato

Se quiser trocar ideias sobre o projeto ou sugerir melhorias, você pode me chamar no [LinkedIn](https://www.linkedin.com/in/raffael-henrique/).
