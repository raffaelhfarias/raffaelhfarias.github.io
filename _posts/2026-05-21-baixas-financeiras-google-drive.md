---
title: "Baixas financeiras com Google Drive e Retaguarda"
description: Fluxo automatizado para detectar novos arquivos no Google Drive, processar baixas no Retaguarda e notificar o resultado por WhatsApp.
date: 2026-05-21 00:00:00 -0300
categories: [Automação]
tags: [Python, Playwright, Google Drive]
comments: true
image: /assets/img/posts/covers/baixas-financeiras-cover.svg
---

# Baixas financeiras com Google Drive e Retaguarda

Automação criada para acompanhar a chegada de novos arquivos financeiros no Google Drive, processar as baixas no sistema Retaguarda e informar o status final automaticamente via WhatsApp.

> Acessos do projeto: fluxo `flow_baixas_financeiro.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Quando a rotina depende do recebimento de planilhas em pasta compartilhada, o gargalo geralmente aparece entre a chegada do arquivo e o registro manual no sistema. Esse fluxo foi pensado para eliminar esse intervalo operacional e transformar o arquivo em ação quase imediata.

## O que foi desenvolvido

- gatilho automático para novos arquivos no Google Drive;
- suporte a execução manual com ID e nome do arquivo como entrada;
- processamento das baixas no Retaguarda com Playwright;
- execução em lote controlado com `ForEach` e limite de concorrência;
- notificações automáticas de sucesso e erro via WhatsApp;
- logging do lote processado para rastreabilidade.

## Tecnologias utilizadas

- **Kestra** para trigger, loop e orquestração do fluxo;
- **Google Workspace Drive Trigger** para detectar novos arquivos;
- **Python** e **Playwright** para o processamento das baixas;
- **Evolution API** para retorno operacional por WhatsApp;
- integração com o sistema **Retaguarda** como destino do processo.

## Valor do projeto

- reduz o tempo entre a chegada do arquivo e a baixa no sistema;
- minimiza risco operacional em rotina financeira sensível;
- melhora visibilidade do processo com retorno automático por mensagem;
- demonstra integração entre trigger de arquivos, automação web e notificação.

## Observações

Esse é um case forte de automação orientada a eventos: o arquivo surge, o fluxo executa, o sistema é atualizado e o time recebe o retorno, sem depender de acompanhamento manual constante.
