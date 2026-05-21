---
title: "Relatório IAF Trimestral automatizado"
description: Automação para verificar atualização do dashboard IAF, extrair indicadores e enviar resumos formatados por WhatsApp com controle de envio diário.
date: 2026-05-02 00:00:00 -0300
categories: [Automação]
tags: [Python, Playwright, Kestra]
comments: true
image: /assets/img/posts/covers/iaf-trimestral-cover.svg
---

# Relatório IAF Trimestral automatizado

Fluxo de automação desenvolvido para verificar se o dashboard IAF foi atualizado, extrair os indicadores relevantes e distribuir um resumo formatado via WhatsApp de forma controlada e sem duplicidade.

> Acessos do projeto: fluxo `envio_iaf.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Relatórios executivos e indicadores trimestrais precisam chegar rápido às áreas interessadas, mas nem sempre a atualização da fonte acontece em horário previsível. Por isso, a automação foi estruturada para monitorar a disponibilidade do dado e somente disparar o fluxo completo quando a atualização realmente ocorre.

## O que foi desenvolvido

- janela de verificação horária para detectar atualização do dashboard IAF;
- separação entre etapa de monitoramento e etapa de execução completa;
- extração automatizada dos dados usando Playwright;
- geração de mensagem formatada e resumo em arquivo para distribuição;
- controle de envio diário com KV Store para evitar notificações repetidas no mesmo dia;
- envio segmentado por canais de WhatsApp conforme o público alvo.

## Tecnologias utilizadas

- **Kestra** para orquestração e regras condicionais do fluxo;
- **Python** para extração, formatação e lógica de negócio;
- **Playwright** para navegação e coleta do conteúdo atualizado;
- **Browserless** para execução remota do navegador;
- **KV Store** para registrar a última data de envio;
- **Evolution API** para distribuição das mensagens.

## Valor do projeto

- automatiza uma rotina que depende da atualização de fonte externa;
- evita ruído operacional com envios duplicados;
- acelera a distribuição de indicadores para as áreas interessadas;
- demonstra uso de automação com lógica condicional e controle de recorrência.

## Observações

Esse case mostra bem como automação não é apenas “extrair e enviar”, mas também decidir quando executar, quando ignorar e como preservar a qualidade da comunicação com o usuário final.
