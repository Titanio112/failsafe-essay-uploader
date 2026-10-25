# 006 — Anotações de trabalho das IAs publicadas no repositório

- **Tipo:** higiene do repositório público
- **Status:** resolvido daqui para frente em 24/10/2026 (commit 8801a0d); o histórico antigo fica como está (decisão do Antônio, 24/10/2026)
- **Local:** `docs/TAREFAS_ATUAIS.md`, `docs/PENDENCIAS.md` e scripts de rascunho em commits antigos
- **Encontrado em:** 24/10/2026, na conferência do repositório depois da publicação

## Descrição

A regra do projeto é que nada de memória ou anotação de assistente de IA vá
para o GitHub. O `.gitignore` já barrava `AGENTS.md`, `PROJECT_MEMORY.md`,
`CLAUDE.md`, `.claude/` e afins, mas não barrava a lista de tarefas
(`docs/TAREFAS_ATUAIS.md`) nem a de pendências (`docs/PENDENCIAS.md`), que são
anotações de trabalho das IAs. As duas foram publicadas junto com o resto.

Os commits antigos também guardam scripts de rascunho que as IAs usaram
(`pm_new.py`, `read_platform*.py`, `update_tasks.py`...). Nenhum deles tem
senha, e-mail real, nome de aluno ou o usuário do Windows: isso foi limpo antes
da publicação (issue 005) e conferido de novo.

## Reprodução

```
git ls-files docs
# docs/PENDENCIAS.md e docs/TAREFAS_ATUAIS.md apareciam
git check-ignore -v docs/PENDENCIAS.md
# (nada: não estava ignorado)
```

## Correção

- Os dois arquivos saíram do git (`git rm --cached`; continuam só no computador)
  e entraram no `.gitignore`, numa seção própria para anotações de IA.
- Varredura de todo o histórico, do `main` e das issues contra a lista de
  alunos e os valores do `.env` (sem imprimir os valores): nada encontrado.
- O histórico **não** foi reescrito: os arquivos antigos não têm dado
  sensível, e reescrever exigiria `push --force` (destrutivo).

**Prevenção:** antes de todo push, `git ls-files` sem arquivo de IA e a
varredura de dados sensíveis.
