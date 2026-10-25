# 018 — Conferência no site contava redação "Cancelada" como já enviada

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/site/conferencia_site.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

O envio ignora linhas "Cancelada", mas a conferência (menu 5) contava como "no site" e também como sobra de outro tema. A redação cancelada nunca aparecia como faltando.

## Reprodução

Site com a única linha do tema 100 "Cancelada": conferência dizia "no site".

## Correção

Canceladas não contam como no site nem como sobra. Tema só com cancelada = "cancelada no site (conferir)": aparece no resumo e não entra sozinho no envio (fail-closed).
