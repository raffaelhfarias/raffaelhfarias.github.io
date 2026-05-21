---
title: "Aniversariantes automáticos com Google Sheets e WhatsApp"
description: Rotina automatizada para exportar base de aniversariantes do Google Sheets, processar os dados e disparar mensagens via WhatsApp.
date: 2026-05-21 00:00:00 -0300
categories: [Automação]
tags: [Python, Google Sheets, WhatsApp]
comments: true
image: /assets/img/posts/covers/aniversariantes-whatsapp-cover.svg
---

# Aniversariantes automáticos com Google Sheets e WhatsApp

Automação voltada para marketing interno e comunicação, responsável por extrair diariamente a base de aniversariantes do Google Sheets, processar as informações e realizar o disparo automatizado da mensagem no WhatsApp.

> Acessos do projeto: fluxo `flow_aniversarios.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Mesmo rotinas simples de comunicação podem se tornar frágeis quando dependem de alguém lembrar do processo todos os dias. Este fluxo foi criado para tornar esse disparo previsível, usando a base viva do Google Sheets como fonte e o WhatsApp como canal final.

## O que foi desenvolvido

- agendamento diário no Kestra para executar o processo no início da manhã;
- exportação automática da planilha do Google Sheets para XLSX;
- uso de Service Account para acesso confiável aos dados atualizados;
- processamento em Python a partir da base exportada;
- disparo automatizado da mensagem para o grupo correto via WhatsApp;
- notificação de erro para número administrativo em caso de falha.

## Tecnologias utilizadas

- **Kestra** para agendamento e orquestração;
- **Google Workspace Drive Export** para converter a planilha em XLSX;
- **Python** para leitura e processamento da base;
- **Evolution API** para envio das mensagens no WhatsApp;
- **Google Service Account** para autenticação com a origem dos dados.

## Valor do projeto

- elimina dependência manual em uma rotina diária recorrente;
- garante uso da base mais atualizada disponível;
- melhora consistência da comunicação interna;
- demonstra automação leve, útil e com impacto real no dia a dia.

## Observações

Este case é um bom exemplo de automação simples, mas de alto valor operacional. Nem toda automação precisa ser complexa para gerar resultado relevante para a empresa.
