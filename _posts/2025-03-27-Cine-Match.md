---
title: "Cine Match"
description: Sistema de recomendação de filmes com Python e Streamlit, baseado em similaridade textual com TF-IDF.
date: 2025-03-27 00:00:00 -0300
categories: [Machine Learning]
tags: [Python, Machine Learning, Streamlit]
comments: true
image: /assets/img/posts/covers/cine-match-cover.svg
pin: true
---

# Cine Match

Aplicação de recomendação de filmes desenvolvida para sugerir títulos semelhantes com base em características textuais, transformando um modelo de machine learning em uma experiência simples e interativa para o usuário.

> Acessos do projeto: [aplicação online](https://recomenda-o-j3mfxmgdwbdydzvjbhbqob.streamlit.app/)
{: .prompt-info }

## Contexto

Sistemas de recomendação fazem parte de muitos produtos digitais modernos. Neste projeto, a proposta foi construir uma solução capaz de recomendar filmes de forma prática, mostrando como técnicas de similaridade podem ser aplicadas em uma interface acessível.

## O que foi desenvolvido

- coleta de dados de filmes com apoio da API do TMDB;
- preparação das informações textuais mais relevantes;
- vetorização com TF-IDF para representar os filmes;
- cálculo de similaridade para gerar recomendações;
- interface web em Streamlit para consulta em tempo real.

## Tecnologias utilizadas

- **Python** para a lógica da aplicação;
- **scikit-learn** para TF-IDF e similaridade por cosseno;
- **Pandas** para manipulação dos dados;
- **Streamlit** para a interface interativa;
- **Requests** para integração com API externa.

## Valor do projeto

- demonstra aplicação prática de sistema de recomendação;
- combina modelagem, tratamento de dados e interface de produto;
- mostra capacidade de transformar conceito técnico em solução utilizável;
- fortalece o portfólio em machine learning aplicado.

## Observações

O foco deste case está em unir experiência do usuário com recomendação baseada em dados, de forma direta e fácil de explorar.
