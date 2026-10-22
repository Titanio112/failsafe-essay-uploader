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

## T38 - Fase 2: repetições, sobras, sem limite por aluno, pasta padrão e primeiro uso [x]

Pedidos do Antônio (22/10): "não era pra ter limite do aluno"; pasta padrão
= a dele; primeira vez: mostrar onde colocar cada coisa; tirar repetições.
- Sem limite por aluno: saiu `max_por_aluno` do lote e `max_envios_por_aluno`
  do Config. `Progresso.registrar_envio`/`LimiteEnvios` ficam só porque o
  teste protegido usa (marcados "não usado pelo fluxo").
- Pasta padrão: `Redações plataforma/` (constante `PASTA_REDACOES`).
  `redacoes_pendentes/` removida.
- Primeiro uso: `python main.py --preparar` (modulos/primeiro_uso.py) cria a
  pasta com LEIA-ME.txt, `dados/dados_alunos.csv` (Nome;Email) e `.env` a partir
  do `.env.example`, sem sobrescrever nada, e mostra ✔/✘ do que falta. O
  dry-run sem lista de alunos ou sem pasta mostra o guia (antes: erro do Python).
- README.md novo na raiz (como usar).
- Repetições: `verificar_dominio_autorizado` ficou só em login.py (era 4x).
  `detectar_ja_enviado` removida (trocada por `contar_tema_hoje` na T35).
  Config: 9 campos sem uso removidos (base_url, login_path, tema,
  estilo_correcao, max_envios_teste, exigir_aprovacao_fuzzy, 3 esperas).
  Funções antigas usadas só pelo teste protegido ficaram (exigir_envio_real,
  verificar_duplicidade, contar_linhas_codigo_data, validar_codigo_site).
- Dicas do dry-run apontam para `--revisar`.

PROVA:
```
$ python -m pytest -m "not real" -q
219 passed, 4 deselected
$ python main.py        (sem --pasta: lê "Redações plataforma")
Pastas de temas: 4 | JPGs encontrados: 130
```
## T39 - Fase 3: módulos em subpastas [x]

- `modulos/base/` (config, estados, excecoes, progresso_relatorio),
  `modulos/dados/` (planilha_arquivos, normalizacao, nomes_aprovados,
  sugestao_temas), `modulos/site/` (login, lista_redacoes, formulario_envio,
  confirmacao, analise_remota), `modulos/envio/` (envio_item, fila_teste,
  fila_producao, fluxo_envio_teste, fluxo_envio_producao),
  `modulos/ferramentas/` (revisao_interativa, primeiro_uso). `git mv` (histórico
  preservado). Imports atualizados em main.py, modulos e tests (37 arquivos;
  em tests/test_essenciais.py só o caminho dos imports mudou).
- `RAIZ` agora é `parents[2]` (config.py ficou um nível mais fundo);
  test_pos_f3 confere.
- Testes que varrem os .py (test_sem_sala, test_pos_f3) passaram a usar
  rglob: com glob("*.py") eles passariam sem checar nada.
- test_estatico (pyflakes) corrigido: a lista antiga citava arquivos da raiz
  que não existem (config.py, login.py...); agora varre main.py + modulos/** +
  tests/. Prova: um arquivo plantado em modulos/site/ com nome indefinido e a
  palavra "sala" fez test_estatico e test_sem_sala FALHAREM; apagado depois.
- AGENTS.md (módulos, pastas, segurança, testes, git), PROJECT_MEMORY.md e
  README.md atualizados.

PROVA:
```
$ python -m pytest -m "not real" -q
219 passed, 4 deselected
```
