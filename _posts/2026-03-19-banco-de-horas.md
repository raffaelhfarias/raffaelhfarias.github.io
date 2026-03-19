---
title: "Extração de banco de horas dos colaboradores ativos"
description: Sistema robusto para extração de banco de horas dos colaboradores, utilizando Evolution API, Kestra e Python. 
date: 2026-03-19 00:00:00 +0800
categories: [Automação]
tags: [Python, Automation]
comments: true
---


<h1 align="center">
  <br>
  <a href="https://raw.githubusercontent.com/raffaelhfarias/automated_whatsapp_reporting/refs/heads/main/imagens/"><img src="https://raw.githubusercontent.com/raffaelhfarias/automated_whatsapp_reporting/refs/heads/main/imagens/simpleImage.png" alt="robot" width="200"></a>
  <br>
  Whatsapp Sender Report - BANCO DE HORAS
  <br>
</h1>

<h4 align="center">Sistema robusto para extração de banco de horas dos colaboradores, utilizando Evolution API, Kestra e Python.</h4>

# Automação de Extração de Banco de Horas (Sólides) 🚀

> Um projeto focado em resolver um gargalo real do departamento de Recursos Humanos através da engenharia de automação.

## 💢 O Problema
O fechamento mensal do banco de horas é uma tarefa crítica, mas o processo de extração do portal Sólides é extremamente manual. Periodicamente, um analista de RH precisava acessar o portal, navegar empresa por empresa (filial por filial), configurar as datas do período, realizar download de planilhas separadas e consolidar os saldos de horas de dezenas/centenas de colaboradores preenchendo as informações "na mão". Um trabalho repetitivo, lento e altamente suscetível a erros humanos.

## 🎯 A Solução
Para transformar completamente essa operação, desenvolvi um robô (automação via RPA) capaz de realizar este processo de ponta a ponta, de forma 100% autônoma. 

A automação segue o seguinte raciocínio:
1. Acessa o painel de RH via navegador oculto (Headless).
2. Autentica localizando os elementos da interface (formulários) de forma segura.
3. Inicia um loop pelas necessidades solicitadas, podendo processar uma filial específica ou iterar automaticamente por todas (mais de 13 filiais atendidas).
4. Aplica os filtros, gera os relatórios, extrai as planilhas.
5. Em background, o sistema lê, limpa as tabelas (identificando colaboradores e saldos) e **consolida tudo automaticamente em um único arquivo CSV** limpo e pronto para conferência.
6. Ao final (ou durante o progresso), o time recebe **notificações completas via WhatsApp** de quantos colaboradores foram extraídos com sucesso.

## 🛠️ Tecnologias Utilizadas
- **Python**: Coração da automação, englobando toda a lógica de repetição, padronização e estruturação dos dados (`xlrd`, processamento do `.csv`).
- **Playwright**: Framework poderoso selecionado para simular o clique a clique e navegar pela interface web, garantindo alta resiliência na automação e espera ativa por carregamento dos elementos do site.
- **Evolution API**: Integração estratégica para envio de mensagens, mantendo a equipe de RH a par do processo em tempo real pelo canal que eles mais utilizam: o WhatsApp.
- **Kestra**: Para orquestrar o processo. Ao conectar a este orquestrador de dados, a automação passa a poder ser acionada remotamente na nuvem via interface ou programada para rodar toda madrugada da data limite do fechamento do espelho de ponto.

## 💡 Impacto para o Negócio (Business Value)
- **Ganho de Produtividade**: Horas de trabalho monótono reduzidas a poucos minutos de execução automática.
- **Precisão Total**: O fim de erros provenientes do tradicional e arriscado *"copiar e colar"*.
- **Acessibilidade e Usabilidade**: Mesmo os gestores sem contexto técnico podem interagir com a solução e ficar 100% cientes do que está ocorrendo através de notificações do Kestra e do WhatsApp.

## License

MIT

---

> GitHub [@raffaelhfarias](https://github.com/raffaelhfarias) &nbsp;&middot;&nbsp;
> Linkedin [Projeto](https://www.linkedin.com/in/raffael-henrique/)&nbsp;&middot;&nbsp;
