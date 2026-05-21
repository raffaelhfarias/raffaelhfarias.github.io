---
title: "Folha de pagamento via WhatsApp para XLSX"
description: Subflow para receber PDF da folha via WhatsApp, extrair os dados e devolver o arquivo processado em XLSX automaticamente.
date: 2026-05-21 00:00:00 -0300
categories: [Automação]
tags: [Python, PDF, WhatsApp]
comments: true
image: /assets/img/posts/covers/folha-pagamento-whatsapp-cover.svg
---

# Folha de pagamento via WhatsApp para XLSX

Subflow criado para receber uma folha de pagamento em PDF via WhatsApp, processar a extração dos dados e devolver automaticamente um arquivo XLSX estruturado para o usuário solicitante.

> Acessos do projeto: fluxo `flow_folha_pagamento.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Em muitas rotinas administrativas, o arquivo chega por mensagem e precisa ser transformado manualmente em uma planilha utilizável. Esse fluxo foi pensado para encurtar esse caminho: o usuário envia o documento, a automação processa e o retorno acontece no mesmo canal de comunicação.

## O que foi desenvolvido

- subflow com entrada do `message_key_id` e do remetente para buscar o PDF original;
- download do documento via Evolution API a partir da mensagem recebida;
- processamento do PDF e extração dos dados em Python;
- geração do arquivo final em formato XLSX;
- envio automático do documento processado de volta ao WhatsApp com `sendMedia`;
- tratamento de erro com retorno claro ao usuário final.

## Tecnologias utilizadas

- **Kestra** para orquestração do subflow;
- **Python** para leitura, extração e geração do XLSX;
- **Evolution API** para download e devolução do documento no WhatsApp;
- processamento de **PDF** como origem e **XLSX** como saída útil para operação.

## Valor do projeto

- reduz trabalho manual de transformar PDF em planilha;
- melhora experiência do usuário ao usar o próprio WhatsApp como interface;
- encurta tempo de resposta em uma rotina documental recorrente;
- demonstra automação orientada a documento com retorno automatizado no mesmo canal.

## Observações

Esse case é interessante porque mostra um padrão de automação conversacional: a mensagem vira entrada do processo, o documento é tratado no backend e o resultado volta diretamente para o solicitante.
