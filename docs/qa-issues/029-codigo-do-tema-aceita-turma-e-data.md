# 029 — Código do tema aceita "3-B", "3 B" e "23.10" (decisão do Antônio)

- **Tipo:** pergunta (regra decidida)
- **Status:** aberta: depende de decisão do Antônio
- **Local:** `modulos/dados/normalizacao.py` (`PADRAO_CODIGO_ARQUIVO`)
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A regra decidida é: código = número no começo da pasta seguido de espaço, "_", "." ou "-"; "3B" colado não é código. Por isso "3-B - Aporofobia", "3 B ...", "3_B ..." e "23.10 ..." viram os temas 3 e 23, que existem no site, e as redações entram na fila sem pergunta.

## Reprodução

`PADRAO_CODIGO_ARQUIVO.match("3-B - Aporofobia")` -> "3"; "23.10 Aporofobia" -> "23".

## Correção

Não corrigido: muda uma regra decidida. Opções: (a) manter; (b) recusar número seguido de letra solta ou de outro número ("3-B", "23.10"), mandando para revisão. Hoje as pastas reais não têm esse formato.
