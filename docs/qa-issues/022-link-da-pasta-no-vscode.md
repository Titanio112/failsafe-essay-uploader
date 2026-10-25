# 022 — Link da pasta de tema abria outra janela do VS Code

- **Tipo:** bug visual
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `main.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A T52 decidiu que, no terminal do VS Code, pasta não vira link. "Detalhes por tema" esquecia o `pasta=True`.

## Reprodução

TERM_PROGRAM=vscode: o nome da pasta virava `vscode://file/...`.

## Correção

`pasta=True` na chamada.
