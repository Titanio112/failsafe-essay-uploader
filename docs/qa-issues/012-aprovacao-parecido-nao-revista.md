# 012 — Aprovação de nome "parecido" valia para sempre, mesmo com aluno novo igual

- **Tipo:** bug de dado
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/nomes_aprovados.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A T46 derruba a aprovação antiga quando a lista muda, mas só para o motivo "nome parcial". "Ana" aprovada para Ana Souza continuava valendo depois de entrar Ana Lima, e nenhuma sugestão nova aparecia para a aluna nova.

## Reprodução

Aprovação `Ana;Ana Souza;...;sim;parecido 100%` + lista com Ana Souza e Ana Lima: a foto "Ana.jpg" ia para Ana Souza.

## Correção

Aprovação de qualquer motivo é ignorada (com aviso) se outro aluno da lista parece com o nome tanto quanto o aprovado. Nome que já tem linha ganha sugestão para o aluno novo.
