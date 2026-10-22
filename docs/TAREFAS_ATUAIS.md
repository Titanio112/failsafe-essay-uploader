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

- [x] Testar na conta de teste (T40): feito em 22/10 18:27–18:29, 4 ENVIADO
      (temas 0, 000, 000, 100), todas "Pendente". Contagem do 000 confirmada.
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
  pasta com LEIA-ME.md (era .txt; trocado a pedido do Antônio), `dados/dados_alunos.csv` (Nome;Email) e `.env` a partir
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

## T40 - Modo teste no mesmo caminho da produção + pastas de teste novas [x]

Pedido do Antônio (22/10): testar tudo na conta de teste antes do aluno real;
pastas de teste sem "3B" na frente.
- `testes/redacoes_teste/` refeita (antigas 0/00/000 em
  ..	estes_antigos_automacao_20261022.zip): `0 - Narração` (código direto),
  `Efeitos da aporofobia` (g), `Discriminação no trabalho` (2º no 000 + nome
  curto + "em branco"), `Impactos da invisibilidade da filiação` (Enter 100 +
  nome com erro). JPGs = cópias das imagens de teste antigas.
- Modo teste: `configurar_modo_teste` (pasta e aprovações em testes/),
  aprovações e `--revisar` valem no modo teste, o envio usa
  `executar_envio_producao(..., conta_teste=email)`: só lote da conta de
  teste, ENVIAR TESTE, ESQUEMA_SENHA_TESTE; a trava de produção não se aplica.
- `modulos/dados/conciliacao_completa.py`: conciliação + aprovações (uma só).
- Saiu `montar_fila_teste` (e tests/test_fila_teste.py). Testes do fluxo de
  teste ajustados (chave "pasta/arquivo", nome exato da conta de teste;
  arquivo inexistente agora = "nada para enviar", retorno 0).
- Testes reais de upload apontam para `0 - Narração/`.

PROVA:
```
$ python -m pytest -m "not real" -q
222 passed, 4 deselected
```
Simulação numa cópia (sem site, sem envio): dry-run -> fila 1; --revisar
(g, g, Enter, Enter, Enter) -> 3 pastas aprovadas, 2 renomeados; dry-run ->
fila 4 (0, 000, 000, 100); --envio-real respondendo "nao" -> mostra o lote de
teste e cancela, sem login.

## T41 - Visual do terminal padronizado num arquivo só [x]

Pedido do Antônio (22/10): o visual "polido" da revisão em todas as telas, e
um arquivo único para mudar o visual.
- `modulos/base/tela.py`: cores, papéis (ok/aviso/erro/info/fraco/bloqueado),
  símbolos, largura, linhas, barras, `titulo`, `cabecalho`, `secao`, `status`,
  `contagens`, `menu`, `comando`, `perguntar`, `caminho` e `FormatoTerminal`
  (log no terminal "  18:27:41 • mensagem"; o arquivo de log não muda).
- Aplicado em: dry-run (título, Dados, Resumo, Detalhes por tema com ✔/⚠/✘ por
  estado, Arquivos gerados, O que falta revisar), envio (título, lote, regras,
  confirmação, resumo colorido), análise remota, --preparar, revisão (passou a
  usar tela.py), avisos de planilha_arquivos e log.
- Caminhos aparecem curtos (relativos à pasta do projeto).
- `tests/test_t41.py`: nenhum arquivo além do tela.py tem código de cor;
  sem terminal não sai cor; mudar SIMBOLOS/LARGURA no tela.py muda a saída.

PROVA:
```
$ python -m pytest -m "not real" -q
228 passed, 4 deselected
```
