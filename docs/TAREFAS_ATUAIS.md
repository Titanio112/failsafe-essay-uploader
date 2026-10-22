# TAREFAS_ATUAIS.md — o que está aberto agora

Histórico completo (T1–T36, com as provas): `docs/historico/TAREFAS_T1_a_T36.md`.
Bugs: `docs/qa-issues/`. Regra de cada tarefa: só vira [x] com PROVA colada.

## Estado em 22/10/2026

- Branch `f4-producao` (não juntada à `limpeza`; sem remoto, sem push).
- Envio para alunos reais BLOQUEADO (`PRODUCAO_BLOQUEADA = True`, T30).
  Só o modo teste envia. Liberar só com ordem do Antônio.
- Pastas aprovadas: aporofobia -> 000 (genérico). Faltam filiação (100),
  discriminação e tecnologia (000, genérico) e a revisão dos nomes
  (`python main.py --revisar`), que o Antônio fará depois.

## Pendências do Antônio

- [ ] Rodar `--revisar`: Enter na filiação, `g` na discriminação e na
      tecnologia, depois os nomes.
- [ ] Decidir quando liberar o envio para alunos reais (T25 suspensa).

## Reorganização pedida em 22/10 (limpeza, sobras, módulos)

## T37 - Fase 1: limpeza de arquivos e documentos [x]

Pedido do Antônio: "pode fazer as limpezas".
- Backup antes de apagar: `..\descartados_automacao_20261022.zip` (fora do
  projeto, 268 arquivos, 15,9 MB, conferido com testzip).
- Apagados (estavam no zip): conteúdo de `logs/` (185 arq., testes de 2–3/10),
  `diagnosticos/` (66 arq., páginas do site de 4–5/10, algumas logadas),
  `modulos/relatorios/` (cópia idêntica do banco atual), os bancos
  `relatorios/progresso.db.antigo_20261007` e `.backup_20261006`, as cópias de
  teste em `redacoes_pendentes/`, `__pycache__/` e `.pytest_cache/`.
  As pastas `logs/` e `diagnosticos/` ficam (o código grava nelas).
- Documentos: na raiz ficam só `AGENTS.md` e `PROJECT_MEMORY.md` (+ README na
  Fase 2). `DECISOES_PENDENTES.md` e `REGRAS_CLINE_AUTOMACAO.md` -> `docs/`.
  Desatualizados -> `docs/historico/`: TAREFAS (T1–T36), AUDITORIA_SELETORES,
  FLUXO_FASE3, INVENTARIO, PROMPT_CLINE, HANDOFF, COMO_TESTAR_DRYRUN.
  Referências corrigidas em AGENTS.md, PROJECT_MEMORY.md, REGRAS e fila_producao.py.

## T38 - Fase 2: repetições, sobras, sem limite por aluno, pasta padrão e primeiro uso [ ]
## T39 - Fase 3: módulos em subpastas [ ]
