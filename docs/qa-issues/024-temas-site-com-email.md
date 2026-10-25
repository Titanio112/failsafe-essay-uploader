# 024 — dados/temas_site.csv (público) era regravado com parte do e-mail da conta

- **Tipo:** higiene do repositório público
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/site/analise_remota.py`, `dados/temas_site.csv`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

O menu 9 (análise remota) regrava o CSV versionado com o e-mail mascarado da conta (2 letras + domínio real), 109 vezes. Um commit depois dele publicaria isso.

## Reprodução

Leitura do código: `conta = mascarar_email(email)` gravado em toda linha.

## Correção

A coluna guarda só "teste" ou "aluno". O CSV atual foi limpo (0 "@").
