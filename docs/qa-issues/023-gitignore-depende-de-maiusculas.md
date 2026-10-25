# 023 — .gitignore só protegia as fotos quando o git ignora maiúsculas

- **Tipo:** higiene do repositório público
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `.gitignore`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A regra era `redações plataforma/` e `*.jpg`, mas a pasta é "Redações plataforma" e as fotos são `.JPG`. Funcionava só porque o git do Windows ignora maiúsculas; no Linux, Mac ou WSL as fotos (com o nome do aluno) apareceriam para `git add`. `.heic`/`.webp` e `docs/historico/` (anotações de IA da pasta antiga) também não estavam cobertos.

## Reprodução

`git -c core.ignorecase=false check-ignore "Redações plataforma/x/A.JPG"`: não ignorado.

## Correção

Padrões sem depender de maiúscula (`*.[jJ][pP][gG]`, `[Rr]edações plataforma/`...), `.heic`, `.webp`, conteúdo de `testes/redacoes_teste/` (menos o .gitkeep) e `docs/historico/`. Teste com `core.ignorecase=false`.
