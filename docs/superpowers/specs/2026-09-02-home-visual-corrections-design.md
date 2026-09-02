# Correções localizadas da página inicial

## Objetivo

Garantir que o domínio raiz conduza ao portfólio atual e melhorar a proporção visual da página inicial PT/EN, sem alterar cases, artigos ou a identidade editorial existente.

## Escopo aprovado

- Reforçar a página `/` com redirecionamento imediato para `/pt/`, mantendo meta refresh e link como fallbacks.
- Remover “Currículo sob medida” / “Tailored résumé” do cabeçalho e da seção final de contato.
- Manter o CTA contextual de solicitação de currículo existente no Hero.
- Reduzir localmente o espaçamento vertical das sete seções da home e as margens internas entre títulos e conteúdo.
- Reduzir o título do Hero de `6.5rem` para no máximo aproximadamente `4.75rem`, preservando escala responsiva.

## Limites

- Não alterar tokens globais, páginas de projetos, cases, artigos ou Sobre.
- Não publicar currículo genérico.
- Não introduzir JavaScript na home, além do redirecionamento mínimo da raiz.

## Verificação

- Teste RED/GREEN para o redirecionamento e para a ausência dos dois links removidos em PT/EN.
- Asserções responsivas para o tamanho máximo do Hero e menor ritmo vertical.
- Build e testes E2E focados em desktop e Pixel 7.
