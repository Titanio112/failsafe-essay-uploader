# 019 — Desfazer renomeação parava no primeiro arquivo aberto

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/ferramentas/revisao_interativa.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

O rename do desfazer não tinha try: um arquivo aberto parava tudo, os outros não voltavam e o resumo não aparecia.

## Reprodução

Log com 2 renomeações e a última foto aberta: PermissionError, nenhuma voltou.

## Correção

Arquivo aberto = mensagem "Nao desfeito ... (arquivo aberto?)" e segue com os outros.
