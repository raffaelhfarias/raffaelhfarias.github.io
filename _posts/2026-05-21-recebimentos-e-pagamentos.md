---
title: "Recebimentos e pagamentos para conciliação contábil"
description: Automação financeira multicanal para extração de relatórios, liquidações e dados de recebimento usados em conciliação contábil.
date: 2026-05-21 00:00:00 -0300
categories: [Automação]
tags: [Python, Browserless, Financeiro]
comments: true
image: /assets/img/posts/covers/recebimentos-pagamentos-cover.svg
---

# Recebimentos e pagamentos para conciliação contábil

Projeto voltado à extração automatizada de dados financeiros em diferentes portais, consolidando informações de recebimentos, pagamentos e liquidações para apoiar rotinas de conciliação contábil.

> Acessos do projeto: módulo `flow_envio_recebimentos_pagamentos/` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Conciliação financeira costuma depender de múltiplas fontes, formatos e acessos distintos. Quando esse processo é manual, o time perde tempo navegando por sistemas, limpando dados e reorganizando informações antes mesmo de começar a análise contábil.

## O que foi desenvolvido

- automações para coleta em diferentes origens financeiras, como relatórios CAR, Mooz e portais de boletos;
- uso de componentes reutilizáveis para limpeza e padronização de valores monetários e volumes de títulos;
- conexão com Browserless para navegação mais resiliente em fluxos sensíveis à detecção;
- logging estruturado para facilitar rastreabilidade e diagnóstico;
- arquitetura modular com separação entre componentes, páginas e scripts de negócio.

## Tecnologias utilizadas

- **Kestra** como camada de orquestração do ecossistema;
- **Python** para parsing, limpeza, logging e regras de negócio;
- **Playwright** e **Browserless** para extração automatizada nos portais;
- componentes próprios de **data cleaning** para padronização dos dados financeiros;
- abordagem de **Page Object Model** para facilitar manutenção.

## Valor do projeto

- reduz esforço operacional em rotinas financeiras repetitivas;
- melhora qualidade e consistência dos dados antes da conciliação;
- facilita manutenção com arquitetura modular e logging detalhado;
- fortalece o portfólio em automação aplicada a contexto financeiro real.

## Observações

Este case representa um conjunto de automações financeiras complementares. Em vez de um único script isolado, o valor aqui está na construção de uma base reutilizável e mais robusta para processos de conciliação.
