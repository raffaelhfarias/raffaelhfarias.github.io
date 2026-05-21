---
title: "Auditorias VIDIBR com alertas via WhatsApp"
description: Automação para monitoramento de auditorias no portal VIDIBR com memória de estado, gatilho por comando e notificações em tempo real.
date: 2026-05-01 00:00:00 -0300
categories: [Automação]
tags: [Python, Playwright, WhatsApp]
comments: true
image: /assets/img/posts/covers/auditoria-vidibr-cover.svg
---

# Auditorias VIDIBR com alertas via WhatsApp

Projeto de automação criado para acompanhar auditorias no portal VIDIBR, identificar novos formulários e enviar notificações detalhadas via WhatsApp sem depender de acompanhamento manual contínuo.

> Acessos do projeto: fluxo `envio_auditoria.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Em processos de auditoria, atrasos na identificação de novos formulários ou ocorrências reduzem a capacidade de resposta da operação. O objetivo deste fluxo foi transformar esse monitoramento em uma rotina confiável, com consultas agendadas e também acionamento sob demanda por comando no WhatsApp.

## O que foi desenvolvido

- agendamento recorrente no Kestra para monitoramento do portal ao longo do dia;
- gatilho por webhook para execução sob demanda quando alguém envia o comando `parcial auditoria`;
- automação web com Playwright para login, navegação e captura dos dados relevantes;
- persistência do último formulário processado usando KV Store, evitando duplicidade de alertas;
- envio automatizado das notificações para grupo de WhatsApp via Evolution API.

## Tecnologias utilizadas

- **Kestra** para orquestração, agendamento e webhooks;
- **Python** para a lógica do fluxo e tratamento dos dados;
- **Playwright** para navegação automatizada no portal VIDIBR;
- **KV Store** para controle de estado da última ocorrência processada;
- **Evolution API** para envio das mensagens no WhatsApp.

## Valor do projeto

- reduz dependência de verificação manual do portal;
- melhora tempo de reação da operação frente a novas auditorias;
- evita reenvios desnecessários com controle de estado persistente;
- demonstra automação orientada a evento com integração real entre scraping e comunicação operacional.

## Observações

O fluxo combina execução agendada e execução por comando, o que aumenta flexibilidade operacional sem perder rastreabilidade. É um bom exemplo de automação que atua como “sensor” de processo e canal de alerta ao mesmo tempo.
