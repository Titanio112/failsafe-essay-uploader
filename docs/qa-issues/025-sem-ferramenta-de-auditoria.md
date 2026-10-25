# 025 — Não havia ferramenta para a auditoria antes do push

- **Tipo:** melhoria (prevenção)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/ferramentas/auditoria_publica.py` (novo)
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

As issues 005 e 006 mandam conferir antes de todo push, mas era um passo manual, sem script; a 006 mostrou que a conferência só de olho falha.

## Reprodução

—

## Correção

`python -m modulos.ferramentas.auditoria_publica`: confere os arquivos do `git ls-files` (nome proibido: IA, foto, banco, planilha, .env, CSV fora da lista; conteúdo com nome/e-mail de aluno, valor do .env ou o usuário do Windows) e diz só ONDE, nunca o valor. Saída 1 = não faça push.
