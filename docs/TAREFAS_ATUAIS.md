# TAREFAS_ATUAIS.md — o que está aberto agora

Histórico completo (T1–T36, com as provas): `docs/historico/TAREFAS_T1_a_T36.md`.
Bugs: `docs/qa-issues/`. Pontos em aberto: `docs/PENDENCIAS.md`.
Regra de cada tarefa: só vira [x] com PROVA colada.

## Estado em 22/10/2026

- Branch `f4-producao` (não juntada à `limpeza`; sem remoto, sem push).
- Branch `revisao-autonoma` (saiu da `f4-producao` em 22/10): T42–T46,
  para o Antônio revisar e juntar ou descartar. A `f4-producao` não mudou.
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
- [ ] Revisar a branch `revisao-autonoma` (T42–T46): juntar ou descartar.
- [ ] Rodar o ensaio: `python main.py --ensaio 3`, depois com
      `--envio-real` (ENVIAR TESTE). Confere também o critério ENEM (T44) no site.
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
  Fase 2). `DECISOES_PENDENTES.md` e `REGRAS_CLINE_AUTOMACAO.md` -> `docs/`
  (em 22/10, depois da T46, `DECISOES_PENDENTES.md` -> `docs/historico/`;
  o que segue aberto está em `docs/PENDENCIAS.md`).
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
- Primeiro uso: `python main.py --preparar` (modulos/ferramentas/primeiro_uso.py) cria a
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

## Revisão autônoma pedida em 22/10 (branch `revisao-autonoma`)

## T42 - Ensaio: redações reais na conta de teste [x]

Por quê: testar fotos, temas reais (inclusive o 000) e aprovações do
`--revisar` antes de liberar a produção, sem abrir conta de aluno.
- `python main.py --ensaio [N]` (padrão 3): conciliação real (lista de
  alunos, `Redações plataforma/`, aprovações de `dados/`), amostra da fila
  validada em rodízio entre pastas, TODA para a conta de teste. Sem
  `--envio-real` só lista; com ele pede ENVIAR TESTE e usa ESQUEMA_SENHA_TESTE.
- Chave no banco `ensaio/pasta/arquivo` na conta de teste; o registro do
  aluno real nunca é tocado; o que já foi no ensaio não volta.
- Funciona com `PRODUCAO_BLOQUEADA = True`. Recusa se ESQUEMA_EMAIL_TESTE
  for e-mail de aluno. Não combina com --modo-teste/--revisar/--analise-remota.
- Arquivos: main.py, modulos/envio/ensaio.py (novo),
  modulos/envio/fluxo_envio_producao.py, tests/test_t42.py.
- Commit: c522337.

## T43 - Nomes e arquivos como vêm de verdade [x]

- "Ana 2.jpg" / "Ana (2).jpg" identificam a mesma aluna e mandam os arquivos
  dela na pasta para REVISAO_MANUAL (página 2? cópia?).
- Número no início do ARQUIVO numa pasta SEM código de tema → REVISAO_MANUAL
  (é página, não tema). `_` no nome separa palavras (em `extrair_pessoa`;
  `normalizar_nome` igual por causa do teste protegido).
- Ignorados calados: `._*`, `~$*`, Thumbs.db, desktop.ini. Subpasta dentro
  do tema: aviso e ignorada.
- CSV do Excel (cp1252), cabeçalho "E-mail" e linha `sep=;` aceitos;
  acrescentar linha em CSV sem quebra final corrigido
  (modulos/dados/arquivos_csv.py, novo).
- pastas_aprovadas: linha cujo `tema` começa por outro código que o
  `codigo` é ignorada com aviso (Excel tira os zeros: 000 -> 0).
- `--desfazer-renomeacao` recusa arquivo com estado de envio no banco; a
  revisão grava o log antes de renomear; banco ilegível bloqueia renomear.
- main explica lista de alunos ilegível (antes: traceback); `--pasta` com
  `--modo-teste` é recusado.
- Arquivos: main.py, modulos/dados/{arquivos_csv, conciliacao_completa,
  nomes_aprovados, normalizacao, planilha_arquivos, sugestao_temas}.py,
  modulos/ferramentas/{primeiro_uso, revisao_interativa}.py, tests/test_t43.py.
- Commit: 97e220d.

## T44 - Segurança do envio [x]

- Critério ENEM conferido (`option:checked` value 1); senão ERRO sem clique.
- CAPTCHA/bloqueio de domínio durante um item para a execução INTEIRA (P6).
- Confirmação julga só a linha NOVA (linhas do mesmo tema hoje que já
  existiam, ex.: Corrigida ou erro antigo, não dão falso erro).
- Tabela achada pelo cabeçalho Data|Tema|Nota|Situação; paginação → fail-closed.
- Mesma foto (sha256) não vai duas vezes: no lote, nem se já registrada
  para o aluno com outro nome/pasta.
- "Hoje" = Brasília (UTC-3 fixo, modulos/base/relogio.py); nada entre
  23:55 e 00:05.
- Um envio por vez: trava do sistema em `relatorios/envio.trava`
  (modulos/base/trava.py).
- Domínio exatamente www.esquemaredacao.com.br; identidade exata na conta
  de teste; depois do clique espera sair de /wordings/new (30 s); sqlite
  timeout 30 s; traceback com palavra de segredo não vai para o log; modo
  teste recusa e-mail de teste que é de aluno.
- Arquivos: modulos/base/{relogio, trava}.py (novos),
  progresso_relatorio.py, modulos/envio/{ensaio, envio_item, fila_producao,
  fila_teste, fluxo_envio_producao, fluxo_envio_teste}.py,
  modulos/site/{confirmacao, formulario_envio, lista_redacoes, login}.py,
  main.py, tests/test_t44.py (+ ajustes de mock em 7 testes).
- Commits: e9565c5 (+ 0c806a3: teste offline do clique, sem retry, espera sair do formulário).

## T45 - Conferência mais curta, log em arquivo, roda de qualquer pasta [x]

- Dry-run: pasta sem código de tema vira uma linha de resumo (nomes
  exatos/parecidos/sem aluno/a decidir).
- "Proximo passo" sugere `python main.py --ensaio 3` quando há fila validada.
- Log gravado em `logs/automacao.log`.
- `python main.py` de outra pasta funciona (chdir para o projeto).
- Arquivos: main.py, tests/conftest.py, tests/test_t45.py.
- Commit: aae436c.

## T46 - Opções fora de lugar recusadas, aprovação antiga, saldo [x]

- `--conta-aluno` sem `--analise-remota` e `--limite-*` fora do
  `--envio-real` de produção → recusados (saída 2).
- Aprovação "nome parcial" antiga é ignorada quando a lista passa a ter mais
  de um aluno que combina.
- Teste de coleta sem caminho fixo (tests/test_imports_reais.py).
- Saldo só pelo texto "Você tem N crédito(s)" (sem o fallback que pegava
  qualquer número + "crédito").
- Arquivos: main.py, modulos/dados/nomes_aprovados.py,
  modulos/site/lista_redacoes.py, tests/test_imports_reais.py, tests/test_t46.py.
- Commits: 93fc944, 5cd0610.

PROVA (suíte completa depois da T46, 22/10; totais de cada tarefa não
foram medidos em separado):
```
$ python -m pytest -m "not real" -q -p no:warnings
300 passed, 4 deselected
```
