# 029 — Código do tema aceita "3-B", "3 B" e "23.10" (decisão do Antônio)

- **Tipo:** pergunta (regra decidida)
- **Status:** resolvido em 25/10/2026 (T58, decisão do Antônio: opção b; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/normalizacao.py` (`PADRAO_CODIGO_ARQUIVO`)
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A regra decidida é: código = número no começo da pasta seguido de espaço, "_", "." ou "-"; "3B" colado não é código. Por isso "3-B - Aporofobia", "3 B ...", "3_B ..." e "23.10 ..." viram os temas 3 e 23, que existem no site, e as redações entram na fila sem pergunta.

## Reprodução

`PADRAO_CODIGO_ARQUIVO.match("3-B - Aporofobia")` -> "3"; "23.10 Aporofobia" -> "23".

## Correção

Decisão do Antônio (25/10): "3-B" é turma e sala da escola, não serve para o script nem para a
plataforma (que não tem turmas). Turma em qualquer forma ("3B", "3-B", "3 B", "3_B", "2º ano")
e datas ("23.10", "23-10-2026") no começo do nome não são mais código: a pasta cai em "sem
código" e a revisão (menu 2) sugere o tema pelo nome, sem a turma. Código de verdade continua
valendo ("0 - Narração", "003-Narração", "100 - A importância"). Pastas reais: nada mudou
(126 prontas, mesmas aprovações).
