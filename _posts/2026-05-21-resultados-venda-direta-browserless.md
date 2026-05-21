---
title: "Resultados de venda direta com Browserless e 2FA"
description: Automação para extração de resultados de venda direta com Browserless, persistência de cookies, 2FA por TOTP e envio automático via WhatsApp.
date: 2026-05-21 00:00:00 -0300
categories: [Automação]
tags: [Python, Browserless, 2FA]
comments: true
image: /assets/img/posts/covers/resultados-vd-cover.svg
---

# Resultados de venda direta com Browserless e 2FA

Fluxo de automação desenvolvido para extrair resultados de venda direta em ambiente protegido por autenticação mais sensível, usando Browserless, persistência de sessão, renovação periódica de cookies e autenticação 2FA automatizada.

> Acessos do projeto: fluxo `envio_resultados_vd.yml` no ecossistema `auto_kestra`
{: .prompt-info }

## Contexto

Automatizar sistemas com login externo, Google, 2FA e mecanismos de detecção costuma ser um desafio técnico relevante. Neste caso, além de extrair os resultados, era necessário manter a sessão viva, renovar autenticação periodicamente e garantir confiabilidade no envio dos dados por ciclo.

## O que foi desenvolvido

- separação entre modo de renovação de autenticação e modo de execução completa;
- renovação horária dos cookies de sessão para preservar acesso;
- uso de Browserless via CDP com stealth e `headless=false` para reduzir bloqueios;
- login com Google e tratamento de 2FA via TOTP;
- leitura de múltiplos ciclos de venda direta com metas por configuração;
- envio automatizado dos resultados por WhatsApp com persistência do estado anterior.

## Tecnologias utilizadas

- **Kestra** para orquestração dos modos de execução;
- **Python** para extração, consolidação e envio;
- **Playwright** com conexão remota em **Browserless**;
- **TOTP / 2FA** para autenticação automatizada no fluxo Google;
- **Namespace Files** e `state.json` para reaproveitamento de sessão;
- **Evolution API** para envio dos resultados.

## Valor do projeto

- resolve um cenário mais avançado de automação autenticada;
- reduz risco de queda de sessão em rotina recorrente;
- melhora confiabilidade de coleta em ambiente com restrições de acesso;
- demonstra domínio técnico em autenticação, sessão persistente e scraping resiliente.

## Observações

Entre os cases do ecossistema, este é um dos mais interessantes do ponto de vista de engenharia, porque combina automação web, autenticação multifator, persistência de estado e execução recorrente em produção.
