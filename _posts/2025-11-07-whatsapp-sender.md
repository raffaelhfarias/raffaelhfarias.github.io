---
title: "Extração e Envio Automático de Metas e Resultados"
description: Automação para captura de metas, extração de dados de vendas e envio automatizado de relatórios via WhatsApp.
date: 2025-11-07 00:00:00 -0300
categories: [Automação]
tags: [Python, Automação]
comments: true
image: https://raw.githubusercontent.com/raffaelhfarias/automated_whatsapp_reporting/refs/heads/main/videos/whatsappsender.gif
---

# Whatsapp Sender Report

Automação desenvolvida para capturar metas compartilhadas em grupos de WhatsApp, consolidar dados de vendas e enviar relatórios automaticamente para acompanhamento operacional.

> Repositório do projeto: [github.com/raffaelhfarias/automated_whatsapp_reporting](https://github.com/raffaelhfarias/automated_whatsapp_reporting)
{: .prompt-info }

## Visão geral

O projeto foi criado para reduzir o trabalho manual envolvido na leitura de metas, coleta de indicadores e comunicação dos resultados. A solução conecta diferentes etapas do processo, desde a captura da informação até o envio final da mensagem, com foco em confiabilidade e agilidade.

## Principais entregas

- captura automática de metas enviadas por WhatsApp;
- extração de dados de vendas a partir de sistemas internos;
- validação e padronização dos dados coletados;
- geração de mensagens com resultados consolidados;
- envio automatizado de relatórios para os destinatários definidos;
- uso de logs e flags para reduzir falhas recorrentes e facilitar o monitoramento.

## Tecnologias utilizadas

- **Python** para a lógica principal da automação;
- **Selenium** e **undetected-chromedriver** para automação web;
- **PyAutoGUI** para interações complementares com interface;
- **lxml** para tratamento e leitura de estruturas HTML/XML;
- **python-dotenv** para configuração segura por variáveis de ambiente;
- **pywhatkit** para apoio no envio automatizado via WhatsApp.

## Fluxo da solução

1. leitura e identificação das metas compartilhadas;
2. coleta dos dados necessários nos sistemas de origem;
3. tratamento e validação das informações;
4. montagem do relatório final;
5. envio automatizado da mensagem para acompanhamento do time.

## Resultado de negócio

A automação reduz esforço operacional, aumenta a velocidade de resposta e diminui o risco de erro humano em um processo que antes exigia acompanhamento manual.

## Como executar

```bash
git clone https://github.com/raffaelhfarias/automated_whatsapp_reporting
cd automated_whatsapp_reporting
python -m venv .venv
```

Depois disso:

- ative o ambiente virtual;
- instale as dependências com `pip install -r requirements.txt`;
- configure as variáveis de ambiente do projeto;
- execute a aplicação conforme a documentação do repositório.

## Observações

> Para execução completa, o ambiente precisa estar preparado para automação do navegador e integração com WhatsApp.

## Licença

MIT
