---
title: "Extração de banco de horas dos colaboradores ativos"
description: Automação para extração e consolidação de banco de horas com Python, Playwright, Evolution API e Kestra.
date: 2026-03-19 00:00:00 -0300
categories: [Automação]
tags: [Python, Automação]
comments: true
image: /assets/img/posts/covers/banco-de-horas-cover.svg

---

# Extração de banco de horas dos colaboradores ativos

Projeto de automação criado para eliminar o processo manual de extração de banco de horas no portal Sólides, consolidando dados de múltiplas filiais e apoiando o time de RH com mais agilidade e previsibilidade.

> Acessos do projeto: case de portfólio com foco em solução, stack e impacto de negócio.
{: .prompt-info }

## Contexto

O fechamento mensal do banco de horas exigia navegação manual por empresa e filial, aplicação de filtros, download de planilhas e consolidação posterior dos dados. Esse fluxo era repetitivo, consumia tempo da equipe e aumentava o risco de erro humano.

## O que foi desenvolvido

- automação do acesso ao ambiente de RH e navegação pelos filtros;
- processamento de uma ou várias filiais em sequência;
- geração e download automatizado dos relatórios;
- tratamento e consolidação dos dados em arquivo final único;
- envio de notificações sobre andamento e resultado da execução.

## Tecnologias utilizadas

- **Python** para a lógica principal e tratamento dos dados;
- **Playwright** para automação do fluxo web;
- **Evolution API** para envio de notificações via WhatsApp;
- **Kestra** para orquestração, agendamento e execução remota;
- geração de arquivos consolidados em **CSV**.

## Valor do projeto

- reduz tempo operacional no fechamento mensal;
- elimina etapas manuais repetitivas;
- melhora confiabilidade na consolidação das informações;
- demonstra aplicação prática de automação com impacto direto no negócio.

## Observações

Este post foi estruturado como case de portfólio, destacando principalmente o problema resolvido, a solução aplicada e o valor entregue ao processo.
