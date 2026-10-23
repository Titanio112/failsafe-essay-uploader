# TAREFAS_ATUAIS.md — o que está aberto agora

Histórico completo (T1–T36, com as provas): `docs/historico/TAREFAS_T1_a_T36.md`.
Bugs: `docs/qa-issues/`. Pontos em aberto: `docs/PENDENCIAS.md`.
Regra de cada tarefa: só vira [x] com PROVA colada.

## Estado em 22/10/2026

- Branch `f4-producao` (não juntada à `limpeza`; sem remoto, sem push).
- Branch `revisao-autonoma` (saiu da `f4-producao` em 22/10): T42–T50,
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
- [ ] Revisar a branch `revisao-autonoma` (T42–T50): juntar ou descartar.
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

## T47 - Cópia do caderno, "O que precisa de você", menu [x]

- Antes de cada envio (modo teste, ensaio, produção) o caderno
  `relatorios/progresso.db` é copiado para
  `relatorios/copias/progresso_<AAAAMMDD_HHMMSS_micro>.db` (API de backup do
  SQLite; ficam as 30 mais recentes). Cópia falhou → nada é enviado.
  Como voltar uma cópia: docstring de modulos/base/copia_seguranca.py.
  ATENÇÃO: voltar uma cópia antiga faz o script esquecer os envios feitos
  depois dela (os de dias anteriores podem ir de novo); só com o arquivo
  atual perdido/estragado e conferindo o site antes.
- Fim de todo envio: seção "O que precisa de você" (conferir no site =
  REVISAO_MANUAL, não enviadas = ERRO com motivo, não tentadas).
- `python main.py` sem opções, num terminal de verdade, abre o menu
  (modulos/ferramentas/menu.py); as opções chamam o mesmo `main` com flags.
  Os comandos com flags continuam iguais.
- Arquivos: main.py, modulos/base/copia_seguranca.py (novo),
  modulos/envio/fluxo_envio_producao.py, modulos/ferramentas/menu.py (novo),
  tests/test_t47.py.
- Commit: 1c4c52e.

## T48 - Achados da 2ª varredura [x]

- Lista só vale na página certa: HTTP < 400, caminho `/minhas-redacoes` e
  texto "Você tem N crédito(s)"; senão ilegível → ERRO antes do clique
  (nunca "lista vazia").
- Contagem: total = max(arquivos do aluno/tema, caderno de hoje + 1);
  ensaio + modo teste na mesma conta não dão mais JA_ENVIADO falso.
- Botão "Enviar resposta" ausente → ERRO (nada clicado).
- Confirmação julga a contagem subir; linha antiga mudando de situação não
  atrapalha.
- Perto da meia-noite: checado uma vez antes de abrir o navegador.
- 2 logins seguidos falhando param tudo (mensagem: senha padrão errada?
  conta bloqueada?).
- `--desfazer-renomeacao` usa a raiz gravada no log (coluna `raiz`): desfazer
  uma revisão do modo teste nunca mexe nos arquivos reais.
- Acrescentar em CSV salvo pelo Excel (cp1252): o arquivo inteiro é
  convertido para UTF-8 antes.
- "Ana Souza 2.jpg" sozinho (só identificado tirando o número final) →
  REVISAO_MANUAL.
- Log esconde o VALOR dos segredos (senhas do .env, `senha=...`), não mais
  qualquer mensagem com a palavra "senha".
- XLSX aceita cabeçalho "E-mail".
- Mais combinações recusadas: `--desfazer-renomeacao` com outras fases,
  `--analise-remota` com `--envio-real`/`--modo-teste`/`--revisar`,
  `--ensaio 0`.
- Arquivos: main.py, modulos/base/{excecoes, progresso_relatorio}.py,
  modulos/dados/{arquivos_csv, planilha_arquivos}.py,
  modulos/envio/{envio_item, fluxo_envio_producao, fluxo_envio_teste}.py,
  modulos/ferramentas/revisao_interativa.py,
  modulos/site/{confirmacao, lista_redacoes}.py, tests/test_t43.py,
  tests/test_t48.py.
- Commit: 95f6f1e.

## T49 - `--resolver` (revisões manuais) [x]

- `python main.py --resolver` (menu opção 6): para cada REVISAO_MANUAL
  pergunta se chegou no site: `s` → ENVIADO, `n` → ERRO (vai de novo na
  próxima execução), Enter pula, `q` sai.
- A data do registro não muda (contagem de hoje continua certa); cada
  resposta fica em `relatorios/resolucoes_<data>.csv`. `--resolver` roda
  sozinho (com outras fases é recusado).
- Arquivos: main.py, modulos/envio/fluxo_envio_producao.py,
  modulos/ferramentas/{menu, resolver (novo)}.py, tests/test_t49.py.
- Commit: 6b9ef3c.

## T50 - Textos do terminal [x]

- Estados com nomes do dia a dia (`tela.ROTULO_DO_ESTADO`): pronto, nome
  parecido, mais de um aluno, sem aluno, pasta sem tema, tema fora do site,
  decidir à mão, enviada, já estava no site, não enviada (erro).
- Resumo da conferência: "Prontas para enviar", "Nome parecido (confirmar
  no --revisar)"...; acentos nas mensagens.
- A conferência termina com "• Só conferência: nada foi enviado." (sem a
  linha vermelha `[BLOQUEADO]`).
- Tela do envio com a seção "Como funciona"; resumo do envio e "O que
  precisa de você" sem códigos internos; motivos de erro dizem o que fazer.
- Menu renumerado (6 = resolver).
- Arquivos: main.py, modulos/base/tela.py, modulos/envio/{envio_item,
  fluxo_envio_producao}.py, modulos/ferramentas/menu.py + ajustes de texto
  em 11 testes.
- Commit: b8c8ba3.

PROVA (suíte completa depois da T50, 22/10; totais de cada tarefa não
foram medidos em separado):
```
$ python -m pytest -m "not real" -q -p no:warnings
342 passed, 4 deselected in 11.86s
```

## T51 - Links para os arquivos, progresso ao vivo, envio sem janela [x]

Pedido do Antônio (22/10, pelo celular): "decidir à mão" obriga a procurar
o arquivo no Explorador; quer um link direto. Progresso com noção de tempo.
Navegador visível continua o padrão (ainda testando), mas a pessoa escolhe.
- `tela.link` / `tela.link_arquivo` (OSC 8, só num terminal de verdade):
  Ctrl+clique abre a foto ou a pasta. Na conferência (pasta e arquivo), na
  revisão, no "O que precisa de você" e no `--resolver`.
- `tela.linha_progresso` + `fluxo_envio_producao.Andamento`: depois de cada
  redação (e de cada aluno pulado) mostra "N de T redações, barra, %,
  passou X, faltam ~Y" (média por redação até agora, pausas incluídas).
- `--sem-janela` (headless); no menu, envio pergunta "Mostrar o navegador?
  (Enter = sim)". Padrão: mostra.
- conftest: os testes não dependem do relógio (a trava da meia-noite deu
  ERRO em 34 testes rodando às 23:56).
- Textos "decidir a mao" -> "decidir à mão".
- Testes: tests/test_t51.py.

PROVA (depois da T51, 23/10 00:0x):
```
$ python -m pytest -m "not real" -q -p no:warnings
353 passed, 4 deselected
```

## T52 - Links que abrem, ver a foto, Configurações, conferir no site [x]

Pedido do Antônio (23/10, pelo celular): o link aparecia, mas Ctrl+clique
não abria nada; a escolha do navegador é configuração (menu); conferir nas
contas dos alunos o que já foi enviado, sem enviar, com progresso. As
redações que estão hoje na pasta já foram enviadas à mão há tempo (data
incerta): só servem para testar.
- Causa do link: `PathCreateFromUrlW` (o que o Windows usa) lê `%C3%A7` como
  dois caracteres -> `RedaÃ§Ãµes` (provado em 23/10 com ctypes; nomes 8.3
  desligados no D:, então não há atalho só-ASCII). `tela.uri_de`: fora do
  VS Code, `file:///` com acento cru (o Windows converte certo); no VS Code
  (`TERM_PROGRAM=vscode`, o terminal do print) `vscode://file/...` e pasta
  sem link. NÃO conferido no terminal do Antônio.
- Plano B que não depende do terminal: `v` em `--revisar` (nomes) e no
  `--resolver` abre a foto (`tela.abrir` -> `os.startfile`).
- `modulos/ferramentas/configuracoes.py` + menu 11: "Mostrar o navegador"
  sim/não gravado em `config.ini` `[plataforma] headless` (só a linha muda;
  sem config.ini, cria). O menu não pergunta mais a cada envio;
  `--sem-janela` continua valendo numa execução.
- `modulos/site/conferencia_site.py` + `--conferir-site` + menu 5: alunos
  com foto conferida; login, identidade, lê `/minhas-redacoes`, compara por
  tema em QUALQUER data (no site / em parte / não está / não conferido).
  `CONFERIR`, trava de um envio por vez, um contexto por aluno, CAPTCHA ou 2
  contas seguidas sem abrir param, progresso por aluno, CSV em
  `relatorios/conferencia_site_<data>.csv`. Não importa `enviar_item` nem
  grava caderno (teste confere). NUNCA rodado no site (só o Antônio roda).
- Menu renumerado: 5 Conferir no site, 6 Enviar, 7 Resolver, 8 Temas,
  9 Desfazer, 10 Primeiro uso, 11 Configurações.
- Testes: tests/test_t52.py (+ t47/t49/t51 ajustados).

PROVA (23/10):
```
$ python -m pytest -m "not real" -q -p no:warnings
370 passed, 4 deselected in 9.65s
$ echo nao | python main.py --conferir-site
 CONFERÊNCIA NO SITE  ·  só leitura, nada é enviado
  Vou entrar na conta de 36 aluno(s), ler Minhas redações e comparar com as 126
  foto(s) da pasta. ...
  Digite CONFERIR para começar (qualquer outro texto cancela):   ⚠ Cancelado: nenhuma conta foi aberta.
```

## T53 - Depois da 1ª conferência no site [x]

O Antônio rodou `--conferir-site` (23/10 ~01:04, 36 alunos, 7 min 10 s):
98 "no site", 28 "não está no site" (todas do tema 100), 0 sem abrir. Ctrl+clique
funcionou (abre a pasta). Pediu: relatório clicável, opção de já enviar as
que faltam, Configurações confusas (digitou "não" e deu "Opção inválida"),
créditos de quem fez.
- Análise do CSV: em 23 alunos a pasta tem 3x000 + 1x100 e o site 4x000
  (outros 5: mesma conta, sobra de 000). Ou seja, a filiação foi mandada à
  mão como 000. Sem tratar isso, "enviar as que faltam" duplicaria 28.
  `comparar` agora marca OUTRO_TEMA quando há sobra de outro tema no site;
  `faltam_enviar` só pega FORA_DO_SITE de conta lida sem erro. Reaplicado ao
  CSV real: 98 no site, 28 talvez com outro tema, 0 a enviar.
- `executar_conferencia_site(..., depois=)` -> `main._enviar_faltantes`:
  produção bloqueada -> só avisa; senão "Montar o envio só destas? (s/n)" e
  `executar_envio_producao` com o lote só delas (ENVIAR e travas de sempre).
- Configurações: pergunta direta "s = mostrar, n = esconder (Enter = deixar)".
- `tela.caminho` vira link (relatórios clicáveis). Pasta com o arquivo
  selecionado no Explorador: não dá por link (o Antônio achou demais).
- `modulos/base/sobre.py`: "Feito por Antônio (Titanio112) · com ajuda do
  Claude (Anthropic) · versão 2026.10.23" no rodapé do menu.
- Testes: tests/test_t53.py; test_t52 ajustado.

PROVA (23/10):
```
$ python -m pytest -m "not real" -q -p no:warnings
379 passed, 4 deselected in 10.02s
$ (regra nova aplicada ao relatorios/conferencia_site_20261023_010426.csv)
{'no site': 98, 'talvez no site com outro tema': 28}
faltam enviar: 0
```

## T54 - Tela da conferência limpa, menu "Enviar as que faltam" [x]

O Antônio rodou a conferência de novo (23/10 ~01:24): 98 no site, 28 "talvez
com outro tema", 0 faltando; relatório clicável e créditos ok. Pediu: tela
menos poluída (linhas quebravam), opção no menu para enviar as que faltam
sem refazer a conferência, e entender por que não apareceu "Montar o
envio?" (resposta: não faltava nenhuma; agora a tela diz isso).
- `_mostrar_aluno`: linha em branco entre alunos; cada foto em 1 linha
  (`✔ no site  tema 000  30/09/2026  pasta…`), cabe em 80 colunas; o nome
  do arquivo saiu (é o do aluno, já no cabeçalho); a pasta abre a foto.
- O log "Conferencia no site N de M" vai só para o arquivo
  (`so_no_arquivo`; filtro no console em `configurar_logging`).
- `faltantes_do_relatorio` + `--enviar-faltantes` + menu 7: só relatório de
  hoje; só fotos ainda conferidas na pasta; segue `_enviar_faltantes`
  (bloqueio, lote, ENVIAR). Menu renumerado (8 Resolver ... 12 Configurações).
- Ideia para depois (não feita, pedido dele): créditos com o nome como link
  (GitHub).
- Testes: tests/test_t54.py (+ t47/t49/t52 renumerados).

PROVA (23/10):
```
$ python -m pytest -m "not real" -q -p no:warnings
388 passed, 4 deselected in 12.48s
  THEO VECANO LAVETO  <th***@x.com>
    ✔ no site      tema 000  30/09/2026    3B - Efeitos da aporofobia
    ⚠ outro tema?  tema 100  como 000?     3B - Impacatos da Invisibilidade da …
```

## T55 - Ensaio real ok; revisão da pasta de teste pelo menu [x]

23/10 02:17-02:18, o Antônio rodou o ENSAIO (menu 3) com 3 redações reais
da Alice -> conta de teste: 3 enviadas, todas "Pendente", "Tudo certo",
progresso ao vivo 1/3 -> 3/3 (1 min 21 s). Confirmado no site real:
critério ENEM conferido, leitura da lista (T48: HTTP, endereço, saldo),
confirmação só da linha nova, cópia do caderno antes do envio.
Ele tentou testar o `v` mas a pasta real não tinha nada para revisar e o
menu não tinha como revisar a pasta de teste (só `--modo-teste --revisar`).
- Menu 4 agora pergunta: Enter/c = conferir, r = revisar, e = enviar.
- Testes: t47/t52 ajustados.

## T56 - Revisão do código novo (T51-T55) [x]

Pedido do Antônio (23/10, antes de dormir): revisar o código novo, juntar a
`revisao-autonoma` na `f4-producao` e abrir a fase seguinte. Feito: junção
fast-forward (tag `f4-antes-da-revisao`), branch `f5-validacao` (F5 =
validação com dados reais antes de liberar a produção). Dois revisores
(conferência/envio e links/menu/config), só leitura. Bloqueio da produção
confirmado em todos os caminhos. Corrigido, cada um com teste que falhava antes:
1. `comparar`: fotos do 000 na pasta podiam "gastar" linhas que eram de outro
   tema e fazer uma redação já enviada parecer faltando -> com qualquer
   sobra, todas as "não está" do aluno viram "outro tema?" (fail-closed).
2. Menu 7: relatório também precisa bater o TEMA (pasta reaprovada depois).
3. Menu 7: lote montado com a fila inteira (mesma foto em duas pastas).
4. Menu 7: as checagens do `--envio-real` (temas_site.csv, lista, bloqueio).
5. Conferência: logout + fechar o navegador protegidos no `finally`.
6. Conferência: navegador caído não perde o relatório (CSV sempre gravado).
7. Menu 7: relatório salvo pelo Excel (ANSI/vírgulas) -> aviso, sem quebrar.
8. Resumo: "Não tentadas (parou antes)" separado de "conta não abriu".
9. Config: `[plataforma] ; nota` não duplica a seção (arquivo não quebra).
10. Config: `headless = sim` ou config.ini com erro não derrubam o menu.
11. Config: `[Plataforma]` e BOM: grava onde o script lê; gravação que
    deixaria o arquivo inválido volta atrás.
12. Resolver: registro do modo teste abre a foto da pasta de teste (antes
    abriria uma foto real com o mesmo nome); `v` só aparece se a foto existe.

PROVA (23/10):
```
$ git stash (só o código) ; pytest tests/test_t56.py
12 failed, 1 passed
$ git stash pop ; python -m pytest -m "not real" -q -p no:warnings
403 passed, 4 deselected in 14.88s
```

