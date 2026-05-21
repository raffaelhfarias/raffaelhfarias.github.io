---
title: "Extração de banco de horas dos colaboradores ativos"
description: Automação para extração e consolidação de banco de horas com Python, Playwright, Evolution API e Kestra.
date: 2026-03-19 00:00:00 -0300
categories: [Automação]
tags: [Python, Automação]
comments: true
---

# Automação de Extração de Banco de Horas

Projeto de automação criado para eliminar o processo manual de extração de banco de horas no portal Sólides, consolidando dados de múltiplas filiais e notificando o time responsável ao longo da execução.

## Contexto do problema

O fechamento mensal do banco de horas exigia um processo repetitivo e sensível a erros: acessar o portal, navegar filial por filial, ajustar filtros de período, baixar planilhas separadas e consolidar manualmente os saldos dos colaboradores.

Esse fluxo consumia tempo operacional, criava gargalos no RH e aumentava o risco de inconsistências na conferência final.

## Solução desenvolvida

A solução automatiza o processo de ponta a ponta:

1. acessa o ambiente de RH em modo automatizado;
2. autentica e navega pelos filtros necessários;
3. processa uma filial específica ou várias filiais em sequência;
4. gera e baixa os relatórios do período configurado;
5. trata os dados extraídos e consolida tudo em um único arquivo final;
6. envia notificações com o andamento e o resultado da execução.

## Tecnologias utilizadas

- **Python** para a lógica principal e tratamento dos dados;
- **Playwright** para automação do fluxo web;
- **Evolution API** para envio de notificações via WhatsApp;
- **Kestra** para orquestração, agendamento e execução remota;
- processamento de planilhas e geração de arquivos consolidados em **CSV**.

## Impacto gerado

- redução significativa do tempo gasto no fechamento mensal;
- eliminação de etapas manuais repetitivas;
- menor risco de erro humano na consolidação;
- maior visibilidade operacional com notificações automáticas;
- processo mais escalável para múltiplas filiais.

## Valor de negócio

Além do ganho técnico, a automação melhora a previsibilidade da rotina de RH e libera tempo da equipe para atividades analíticas e de conferência, em vez de tarefas mecânicas de extração.

## Observação

Este case foi publicado com foco na solução e no impacto de negócio. Se você quiser, posso depois transformar este post em um estudo de caso ainda mais completo, com arquitetura, fluxo técnico e resultados esperados.

## Licença

MIT
