# TAREFAS_ATUAIS.md — Ordem: docs -> F2a (2 etapas) -> F2b -> F2c -> F2d -> F3

> Uma tarefa por vez. Só vira [x] com PROVA colada (saída literal, mín. 15 linhas
> + git diff --stat + git log --oneline -1). Formato conforme REGRAS seção 12.
> O Cline NUNCA digita ENVIAR / ENVIAR TESTE. Quem envia é o Antônio.

Legenda das verificações: "0 ocorrências" = rodar Select-String e colar saída vazia.

---

## T1 - Corrigir e versionar INVENTARIO.md [ ]
- Objetivo: substituir INVENTARIO.md pelo conteúdo corrigido (versão 07/10 que corrige os erros da seção 8 do CONTEXTO) e versionar INVENTARIO.md + REGRAS_CLINE_AUTOMACAO.md.
- Arquivos que PODE mexer: INVENTARIO.md, REGRAS_CLINE_AUTOMACAO.md.
- Arquivos que NÃO pode mexer: qualquer .py, .env, AGENTS.md, PROJECT_MEMORY.md, outros.
- Comando de verificação:
  Select-String -Path INVENTARIO.md -Pattern "46 untracked","7 rastreados"  (0 ocorrências)
  git add INVENTARIO.md REGRAS_CLINE_AUTOMACAO.md ; git commit ; git status --short
- PROVA: (colar aqui a saída)
- Fora de escopo: escrever o conteúdo por conta própria (o Antônio fornece o texto corrigido), apagar qualquer arquivo.

## T2 - Corrigir contradições dos documentos [ ]
- Objetivo: aplicar nas docs as correções da seção 8 do CONTEXTO (seletor de anexo, falso sinal de upload, regra de duplicidade, módulos inexistentes, ESQUEMA_SENHA_TESTE, remoção de "SALA", itens repetidos do PROJECT_MEMORY, autor estranho e item 5.5 cortado do DECISOES_PENDENTES). O Antônio fornece os textos corrigidos de AGENTS.md e PROJECT_MEMORY.md; em DECISOES_PENDENTES.md apenas trocar o autor e fechar o fragmento 5.5.
- Arquivos que PODE mexer: AGENTS.md, PROJECT_MEMORY.md, DECISOES_PENDENTES.md.
- Arquivos que NÃO pode mexer: qualquer .py, .env, tests/, TAREFAS_ATUAIS.md, INVENTARIO.md.
- Comando de verificação:
  Select-String -Path AGENTS.md,PROJECT_MEMORY.md -Pattern "wording\[attachment\]"  (0)
  Select-String -Path AGENTS.md,PROJECT_MEMORY.md -Pattern "ESQUEMA_TESTE_SENHA"    (0)
  Select-String -Path AGENTS.md,PROJECT_MEMORY.md -Pattern "SALA"                   (0)
  Select-String -Path AGENTS.md,PROJECT_MEMORY.md -Pattern "qualquer data"          (0)
  Select-String -Path AGENTS.md -Pattern "input\[name=\"wording\[pages_attributes\]\[0\]\[file\]\"\]"  (>=1)
  git add -A docs ; git commit
- PROVA: (colar aqui a saída)
- Fora de escopo: mudar regras de negócio, apagar seções sem instrução, criar documentos novos.

## T3 - Restaurar PROMPT_CLINE.md [ ]
- Objetivo: desfazer a exclusão acidental (decisão do dono é manter o arquivo).
- Arquivos que PODE mexer: PROMPT_CLINE.md (restaurar).
- Arquivos que NÃO pode mexer: todos os outros.
- Comando de verificação:
  git checkout -- PROMPT_CLINE.md ; git status --short  (não pode mais listar PROMPT_CLINE.md)
  Test-Path PROMPT_CLINE.md   (True)
- PROVA: (colar aqui a saída)
- Fora de escopo: editar o conteúdo do arquivo.

## T4 - F2a etapa 1a: apagar txt/bak rastreados (grupo A1, 22 itens) [ ]
- Objetivo: remover do repositório os .txt/.bak rastreados de lixo do grupo A1 do INVENTARIO seção 6.A.
- Arquivos que PODE mexer: SOMENTE os 22 do grupo A1 (git rm).
- Arquivos que NÃO pode mexer: qualquer outro.
- Comando de verificação:
  git rm PM_part1.txt PM_part2.txt PM_part3.txt PM_temp.txt TAREFAS_ATUAIS.md.bak commit_msg.txt diff.txt headers.txt launch_error.txt launch_error2.txt len.txt log_out.txt old_func.txt out.txt planilha_content.txt planilha_content2.txt pytest_output.txt send_flow_body.txt temp_content.txt temp_plataforma.txt test.txt test_error.txt
  git status --short
- PROVA: (colar aqui a saída)
- Fora de escopo: apagar .py, untracked, pastas; commitar (commit é T7).

## T5 - F2a etapa 1b: apagar .py rastreados de lixo (grupo A2, 21 itens) [ ]
- Objetivo: remover os .py rastreados de lixo do grupo A2, incluindo conciliacao.py (ninguém importa).
- Arquivos que PODE mexer: SOMENTE os 21 do grupo A2 (git rm).
- Arquivos que NÃO pode mexer: qualquer outro .py de produção/teste.
- Comando de verificação:
  git status --short
  python -m pytest -m "not real" -q   (0 failed — obrigatório rodar e colar)
- PROVA: (colar aqui a saída)
- Fora de escopo: apagar plataforma.py (é F2d/T15), untracked, commitar.

## T6 - F2a etapa 1c: apagar pastas rastreadas temp/ e temp_conciliacao/ [ ]
- Objetivo: remover as 2 pastas rastreadas de lixo (grupo A3).
- Arquivos que PODE mexer: temp/, temp_conciliacao/ (git rm -r).
- Arquivos que NÃO pode mexer: qualquer outro.
- Comando de verificação:
  git status --short
  python -m pytest -m "not real" -q   (0 failed)
- PROVA: (colar aqui a saída)
- Fora de escopo: commitar (é T7), apagar untracked.

## T7 - F2a etapa 2: apagar untracked de lixo (grupo 6.B, 20 itens) + commit [ ]
- Objetivo: deletar do disco os 20 untracked de lixo, MANTENDO INVENTARIO.md e REGRAS_CLINE_AUTOMACAO.md, e commitar a F2a inteira.
- Arquivos que PODE mexer: SOMENTE os 20 untracked do grupo 6.B (del).
- Arquivos que NÃO pode mexer: INVENTARIO.md, REGRAS_CLINE_AUTOMACAO.md, .env, qualquer rastreado.
- Comando de verificação:
  git status --short   (não pode sobrar nenhum dos 20; INVENTARIO/REGRAS já commitados em T1)
  python -m pytest -m "not real" -q   (0 failed)
  git commit -m "F2a: remove lixo rastreado e untracked" ; git log --oneline -1
- PROVA: (colar aqui a saída)
- Fora de escopo: mover arquivos, criar modulos/, mexer em código.

## T8 - F2b: criar modulos/ e mover módulos sem dependência de plataforma [ ]
- Objetivo: criar modulos/ (com __init__.py vazio) e git mv de config.py, estados.py, excecoes.py, normalizacao.py, descoberta_arquivos.py.
- Arquivos que PODE mexer: criar modulos/__init__.py; mover os 5 listados.
- Arquivos que NÃO pode mexer: conteúdo interno dos arquivos movidos; login.py, lista_redacoes.py, formulario_envio.py, confirmacao.py, fluxo_envio_teste.py, planilha_arquivos.py, progresso_relatorio.py, main.py, plataforma.py, tests/.
- Comando de verificação:
  Test-Path modulos\\config.py,modulos\\estados.py,modulos\\excecoes.py,modulos\\normalizacao.py,modulos\\descoberta_arquivos.py,modulos\\__init__.py   (todos True)
  python -m py_compile modulos\\__init__.py
  git status --short   (mostra os 5 renomeados)
- PROVA: (colar aqui a saída)
- Fora de escopo: editar imports, criar dominio.py/avisos.py, pytest.

## T9 - F2b: criar modulos/dominio.py e modulos/avisos.py [ ]
- Objetivo: criar dominio.py com verificar_dominio_autorizado (cópia única, vinda de login.py) e avisos.py com _emitir_aviso (cópia única, vinda de descoberta_arquivos.py). NÃO remover ainda as cópias antigas (isso é T11).
- Arquivos que PODE mexer: criar modulos/dominio.py, modulos/avisos.py.
- Arquivos que NÃO pode mexer: qualquer arquivo existente.
- Comando de verificação:
  python -m py_compile modulos\\dominio.py modulos\\avisos.py
  python -m pyflakes modulos\\dominio.py modulos\\avisos.py   (sem "undefined name")
- PROVA: (colar aqui a saída)
- Fora de escopo: remover defs duplicadas, editar módulos existentes.

## T10 - F2b: mover os módulos restantes para modulos/ [ ]
- Objetivo: git mv de login.py, lista_redacoes.py, formulario_envio.py, confirmacao.py, fluxo_envio_teste.py, planilha_arquivos.py, progresso_relatorio.py para modulos/.
- Arquivos que PODE mexer: mover os 7 listados.
- Arquivos que NÃO pode mexer: conteúdo interno; main.py, plataforma.py, tests/.
- Comando de verificação:
  git status --short   (mostra os 7 renomeados)
  Test-Path modulos\\login.py,modulos\\lista_redacoes.py,modulos\\formulario_envio.py,modulos\\confirmacao.py,modulos\\fluxo_envio_teste.py,modulos\\planilha_arquivos.py,modulos\\progresso_relatorio.py  (todos True)
- PROVA: (colar aqui a saída)
- Fora de escopo: editar imports (é T11+), apagar plataforma.py.

## T11 - F2c: corrigir imports internos de modulos/ e remover defs duplicadas [ ]
- Objetivo: dentro de modulos/, trocar cópias duplicadas por import de modulos.dominio / modulos.avisos e ajustar imports cruzados (planilha_arquivos -> descoberta_arquivos etc.).
- Arquivos que PODE mexer: somente .py dentro de modulos/.
- Arquivos que NÃO pode mexer: main.py, plataforma.py, tests/.
- Comando de verificação:
  python -m py_compile (todos os .py de modulos/)
  python -m pyflakes (todos os .py de modulos/)   (sem "undefined name")
  Select-String -Path modulos\\*.py -Pattern "def verificar_dominio_autorizado"  (1 ocorrência, em dominio.py)
  Select-String -Path modulos\\*.py -Pattern "def _emitir_aviso"  (1 ocorrência, em avisos.py)
- PROVA: (colar aqui a saída)
- Fora de escopo: pytest (suíte fica vermelha até T14 — esperado), editar tests/.

## T12 - F2c: atualizar imports de modulos/fluxo_envio_teste.py [ ]
- Objetivo: apontar os imports para modulos.* (era from login/lista_redacoes/...).
- Arquivos que PODE mexer: modulos/fluxo_envio_teste.py.
- Arquivos que NÃO pode mexer: lógica do fluxo, outros arquivos.
- Comando de verificação:
  python -m py_compile modulos\\fluxo_envio_teste.py ; python -m pyflakes modulos\\fluxo_envio_teste.py
- PROVA: (colar aqui a saída)
- Fora de escopo: ligar ao CLI (é T16), alterar comportamento.

## T13 - F2c: atualizar imports de main.py [ ]
- Objetivo: trocar o import da linha 46 (from plataforma import ...) pelos imports de modulos.*.
- Arquivos que PODE mexer: main.py.
- Arquivos que NÃO pode mexer: lógica de negócio, outros arquivos.
- Comando de verificação:
  python -m py_compile main.py ; python -m pyflakes main.py
  python main.py --help   (roda sem ImportError — colar saída)
- PROVA: (colar aqui a saída)
- Fora de escopo: ligar fluxo_envio_teste ao CLI (é T16).

## T14 - F2c: atualizar imports dos testes [ ]
- Objetivo: test_essenciais.py, test_identidade.py, test_imports_reais.py passam a importar de modulos.*. Proibido mudar o que os testes verificam.
- Arquivos que PODE mexer: tests/test_essenciais.py, tests/test_identidade.py, tests/test_imports_reais.py.
- Arquivos que NÃO pode mexer: qualquer .py de produção, plataforma.py.
- Comando de verificação:
  python -m pytest -m "not real" -q   (0 failed — colar total real)
- PROVA: (colar aqui a saída)
- Fora de escopo: alterar asserts/comportamento testado, apagar plataforma.py.

## T15 - F2d: apagar plataforma.py + fechar a limpeza [ ]
- Objetivo: com zero imports restantes de plataforma, apagar o arquivo, rodar a suíte, commitar e criar tag pos-limpeza.
- Arquivos que PODE mexer: plataforma.py (git rm).
- Arquivos que NÃO pode mexer: qualquer outro.
- Comando de verificação:
  Select-String -Path *.py,modulos\\*.py,tests\\*.py -Pattern "from plataforma|import plataforma"  (0 ocorrências)
  python -m pytest -m "not real" -q   (0 failed — colar total real)
  git commit -m "F2d: remove plataforma.py" ; git tag pos-limpeza ; git log --oneline -1
- PROVA: (colar aqui a saída)
- Fora de escopo: criar módulos NOVOS (progresso.py, relatorios.py, logging_config.py, tabelas.py, fluxo_dryrun.py, fluxo_analise_remota.py — fica para depois da F3, decisão do Antônio).

## T16 - F3: ligar o envio de teste ao CLI [ ]
- Objetivo: `python main.py --modo-teste --envio-real` passa a chamar executar_envio_teste() em vez de imprimir [BLOQUEADO].
- Arquivos que PODE mexer: main.py (somente o roteamento de argumentos).
- Arquivos que NÃO pode mexer: modulos/fluxo_envio_teste.py, qualquer outro.
- Comando de verificação:
  python main.py --modo-teste --envio-real
  (critério: NÃO imprime [BLOQUEADO]; para no prompt pedindo ENVIAR TESTE.
   Quem verifica digita algo diferente de ENVIAR TESTE para abortar.)
  python main.py --modo-teste   (sem --envio-real continua [BLOQUEADO])
- PROVA: (colar aqui a saída)
- Fora de escopo: login real, navegar no site, anexar, clicar em enviar.

## T17 - F3: descobrir o sinal de "upload aceito" (só observação) [x]
- Objetivo: medir o que muda na página /wordings/new depois do anexo (DOM, console, requisições de rede), usando a conta de teste. Resultado documentado em comentário no teste.
- Arquivos que PODE mexer: tests/test_upload_sinal.py (@pytest.mark.real); escrever logs em logs/.
- Arquivos que NÃO pode mexer: qualquer .py existente; .env.
- Comando de verificação:
  python -m pytest tests/test_upload_sinal.py -v -m real
  (login + selecionar tema + ENEM + anexar 1 JPG de testes/redacoes_teste/ + capturar console/respostas/DOM + context.close()+browser.close() no finally, sem navegar a logout. PROIBIDO clicar em "Enviar resposta".)
- PROVA:
  python -m pytest tests/test_upload_sinal.py -v -m real
  1 passed in 23.47s
  upload_indicators_encontrados = 1
  erros = []
  11 snapshots com .progress .bar visível
  width: 100%
  texto "Arquivo carregado"
  JSON sanitizado salvo em logs/
  finally com context.close() e browser.close(), sem logout URL e sem página 404
  não houve clique em "Enviar resposta"
  não houve digitação de "ENVIAR TESTE"
  nenhuma redação submetida
  saldo não medido; sem submissão, nenhum consumo era esperado
- Fora de escopo: clicar em enviar, digitar confirmação, chutar seletor. Se nada mudar na página: registrar em DECISOES_PENDENTES.md e PARAR.

## T18 - F3: implementar aguardar_upload_aceito com a evidência [x]
- Objetivo: implementar/aguardar o sinal observado em T17 em modulos/formulario_envio.py.
- Arquivos que PODE mexer:
  modulos/formulario_envio.py,
  tests/test_upload_sinal.py,
  tests/test_upload_aceito_t18.py
- Arquivos que NÃO pode mexer: outros módulos, main.py.
- Comando de verificação:
  python -m pytest -m "not real" -q   (0 failed)
  python -m pytest tests/test_upload_sinal.py -v -m real        # T17: descoberta/observação do sinal
  python -m pytest tests/test_upload_aceito_t18.py -v -m real   # T18: validação oficial
- PROVA:
  python -m pytest tests/test_upload_aceito_t18.py -v -m real
  1 passed in 16.50s
  Login → minhas-redacoes → dropdown identidade → /wordings/new
  Tema selecionado: value="68" (código '0')
  Critério ENEM: value="1"
  JPG anexado: testes/redacoes_teste/0/01Usuario Testes Ignorar.jpg
  aguardar_upload_aceito(page, timeout_segundos=30) retornou True
  Não houve clique em "Enviar resposta"
  Não houve digitação de "ENVIAR TESTE"
  Encerramento: context.close() + browser.close() no finally, sem navegar a /auth/users/sign_out, sem 404
  Nenhuma redação submetida
  Saldo não foi medido nesta execução; sem submissão, não houve consumo esperado
- Fora de escopo: inventar seletor não observado em T17. Sem evidência suficiente: registrar em DECISOES_PENDENTES.md e PARAR.

## T18B - F3: fail-closed após tentativa de envio [x] (corrigida na T18C)
- Objetivo: depois de iniciar a tentativa de clique em "Enviar resposta",
  qualquer resultado inconclusivo deve registrar REVISAO_MANUAL,
  sem retry automático.
- Arquivos que PODE mexer:
  modulos/fluxo_envio_teste.py
  e criar exclusivamente o novo arquivo offline
  `tests/test_fluxo_envio_teste_fail_closed.py`,
  com mocks necessários para testar `executar_envio_teste`
  sem navegador, sem login e sem envio.
- Arquivos que NÃO pode mexer:
  main.py, .env, seletores confirmados, timeout de confirmação,
  T19, e documentação não necessária.
- Regras obrigatórias:
  - clique_iniciado=False antes do try;
  - clique_iniciado=True imediatamente antes de clicar_enviar(page);
  - ConfirmacaoInconclusiva depois da tentativa → REVISAO_MANUAL;
  - retorno False de aguardar_confirmacao depois da tentativa
    → REVISAO_MANUAL;
  - CaptchaOuBloqueio ou Exception após tentativa
    → REVISAO_MANUAL;
  - falha antes da tentativa → ERRO;
  - Pendente confirmado → ENVIADO;
  - nenhum retry;
  - nenhum segundo clique;
  - T19 continua executada somente por Antônio.
- Provas exigidas:
  - py_compile;
  - testes offline exclusivamente em
    `tests/test_fluxo_envio_teste_fail_closed.py`,
    sem navegador, sem login e sem envio;
  - git diff --check;
  - Git limpo após commit;
  - nenhum teste real;
  -
PROVA:
python -m py_compile modulos\fluxo_envio_teste.py
<exit code 0>

python -m pyflakes modulos\fluxo_envio_teste.py tests\test_fluxo_envio_teste_fail_closed.py
<exit code 0>

python -m pytest tests\test_fluxo_envio_teste_fail_closed.py -q -m "not real"
....
4 passed in 0.82s

python -m pytest tests\ -q -m "not real"
........................................................................ [ 87%]
..........                                                               [100%]
============================== warnings summary ===============================
tests/test_essenciais.py::test_conciliacao_exato_unico
tests/test_essenciais.py::test_conciliacao_sugestao_fuzzy
tests/test_essenciais.py::test_aluno_sem_arquivo
tests/test_essenciais.py::test_nao_jpg_ignorado_com_aviso
  d:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\tests\test_essenciais.py:192: UserWarning: [AVISO] Arquivo ignorado (extens�o n�o permitida): 000 - Narra��o/005 - Teste.jpeg (ext: .jpeg)
    return descobrir_arquivos(config_teste)

tests/test_essenciais.py::test_conciliacao_exato_unico
tests/test_essenciais.py::test_conciliacao_sugestao_fuzzy
tests/test_essenciais.py::test_aluno_sem_arquivo
tests/test_essenciais.py::test_nao_jpg_ignorado_com_aviso
  d:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\tests\test_essenciais.py:192: UserWarning: [AVISO] Arquivo ignorado (extens�o n�o permitida): 001 - Carta/006 - Teste.pdf (ext: .pdf)
    return descobrir_arquivos(config_teste)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
82 passed, 4 deselected, 8 warnings in 4.20s

git diff --check
warning: in the working copy of 'TAREFAS_ATUAIS.md', LF will be replaced by CRLF the next time Git touches it

git diff --stat
 modulos/fluxo_envio_teste.py    | 17 ++++++++++++----
 tests/test_fluxo_envio_teste_fail_closed.py |  56 ++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 69 insertions(+), 4 deletions(-)

git log --oneline -1
0a20919 F3: validar sinal real de upload T17/T18 nenhuma execução de main.py;
  - nenhum clique de envio.
- Fora de escopo:
  - envio real;
  - clique no botão;
  - digitar ENVIAR TESTE;
  - alterar saldo, seletores, timeout, regras de duplicidade,
    login, browser ou logout;
  - alterar `tests/test_essenciais.py`;
  - criar qualquer outro arquivo além de
    `tests/test_fluxo_envio_teste_fail_closed.py`.
- Reaberta: bug de ordem de argumentos em marcar() nos ramos Captcha/Exception; corrigido na T18C.

## T18C - F3: corrige ordem de argumentos de marcar e torna o teste fail-closed real [x]
- Objetivo: nos ramos `except CaptchaOuBloqueio` e `except Exception` de
  `executar_envio_teste`, `progresso.marcar()` recebia
  (aluno_id, arquivo, codigo_tema, estado) em vez de
  (aluno_id, arquivo, estado, pasta=codigo_tema), gravando estado="0".
  Corrigir a chamada e fazer o teste ler o estado real do banco (7 casos).
- Arquivos mexidos:
  modulos/fluxo_envio_teste.py
  tests/test_fluxo_envio_teste_fail_closed.py
  TAREFAS_ATUAIS.md
- Nenhum teste real, nenhum main.py, nenhum login, nenhum clique de envio.
PROVA (passo 2 - verificação, código corrigido):
$ python -m py_compile modulos/fluxo_envio_teste.py
[exit 0]
$ python -m pyflakes modulos/fluxo_envio_teste.py tests/test_fluxo_envio_teste_fail_closed.py
[exit 0]
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -v -m "not real"
collecting ... collected 7 items

tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_retorna_false_revisao_manual PASSED [ 14%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_confirmacao_inconclusiva_revisao_manual PASSED [ 28%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_clicar_enviar_levanta_captcha_bloqueio_revisao_manual PASSED [ 42%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_exception_generica_revisao_manual PASSED [ 57%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_falha_antes_do_clique_saldo_indisponivel_erro PASSED [ 71%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_falha_antes_do_clique_codigo_invalido_erro PASSED [ 85%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_confirmacao_ok_enviado PASSED [100%]

============================== 7 passed in 0.87s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 84%]
.............                                                            [100%]
(8 warnings de test_essenciais.py:192 - arquivos .jpeg/.pdf ignorados, esperados)
85 passed, 4 deselected, 8 warnings in 4.24s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat
 modulos/fluxo_envio_teste.py                |   4 +-
 tests/test_fluxo_envio_teste_fail_closed.py | 286 ++++++++++++++++++++--------
 2 files changed, 206 insertions(+), 84 deletions(-)
[exit 0]

PROVA (passo 3 - o teste pega o bug):
$ git stash push -- modulos/fluxo_envio_teste.py
Saved working directory and index state WIP on limpeza: c00d208 T18B: fail-closed após tentativa de envio
[exit 0]
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -v -m "not real"   (código com o bug, versão c00d208)
>       assert estado["estado"] == REVISAO_MANUAL
E       AssertionError: assert '0' == 'REVISAO_MANUAL'
E         
E         - REVISAO_MANUAL
E         + 0

tests\test_fluxo_envio_teste_fail_closed.py:191: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_clicar_enviar_levanta_captcha_bloqueio_revisao_manual
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_exception_generica_revisao_manual
========================= 2 failed, 5 passed in 1.09s =========================
[exit 1]
$ git stash pop
	modified:   modulos/fluxo_envio_teste.py
	modified:   tests/test_fluxo_envio_teste_fail_closed.py
Dropped refs/stash@{0} (8cd5489fa238c1be846c1b4b96c8dca0201bff53)
[exit 0]
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -v -m "not real"   (código corrigido restaurado)
============================== 7 passed in 0.95s ==============================
[exit 0]
$ git status --short
 M modulos/fluxo_envio_teste.py
 M tests/test_fluxo_envio_teste_fail_closed.py

## T18D - F3: corrige defeitos pré-clique achados na 1ª execução da T19 [x]
- Origem: 1ª execução da T19 (21/10, Antônio) parou com
  `TypeError: selecionar_criterio() takes 1 positional argument but 2 were given`
  antes do clique (nada enviado; banco gravou ERRO, "Excecao: TypeError").
- Defeitos (todos antes do clique, em modulos/fluxo_envio_teste.py):
  - A: `selecionar_criterio(page, "ENEM")` — a função só aceita `page` (ENEM fixo value=1).
  - B: `anexar_arquivo(page, arquivo)` recebe só o nome do arquivo, não o caminho completo.
  - C: retorno de `aguardar_upload_aceito` ignorado — upload não aceito ainda clicava.
  - D: retorno de `selecionar_tema_por_codigo` ignorado, e o fallback por
    `value=codigo` pode escolher tema errado; o tema selecionado não era conferido.
- Regras: falha em A–D → ERRO, sem clique. Tema conferido lendo a opção
  selecionada do combo `wording[wording_proposal_id]` e comparando o código (string exata).
- Arquivos autorizados (Antônio, 21/10): modulos/fluxo_envio_teste.py
  (mesmo acima de 200 linhas), tests/test_fluxo_envio_teste_fail_closed.py,
  TAREFAS_ATUAIS.md.
- Testes: mocks com `autospec=True` (pega erro de assinatura como o A) + casos novos.
- Fora de escopo: RAIZ em modulos/config.py (banco/relatórios em modulos/relatorios/),
  fallback por value em modulos/formulario_envio.py, T19.
- Casos novos (5): criterio/anexo com argumentos corretos, arquivo inexistente
  (sem login), upload não aceito, tema não selecionado, tema selecionado diferente
  ("00" != "0"). Todos exigem ERRO e 0 cliques.
- Limite da prova com stash: no código antigo o TypeError de A aborta antes,
  então C e D falham por A (detalhe "Excecao: TypeError" em vez do detalhe
  esperado), não isoladamente.
PROVA:
$ python -m py_compile modulos/fluxo_envio_teste.py
[exit 0]
$ python -m pyflakes modulos/fluxo_envio_teste.py tests/test_fluxo_envio_teste_fail_closed.py
[exit 0]
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -q -m "not real"
............                                                             [100%]
12 passed in 1.24s
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 80%]
..................                                                       [100%]
90 passed, 4 deselected, 8 warnings in 5.02s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat
 TAREFAS_ATUAIS.md                           |  19 +++++
 modulos/fluxo_envio_teste.py                |  61 ++++++++++---
 tests/test_fluxo_envio_teste_fail_closed.py | 128 +++++++++++++++++++++++-----
 3 files changed, 179 insertions(+), 29 deletions(-)
[exit 0]
$ git stash push -- modulos/fluxo_envio_teste.py
Saved working directory and index state WIP on limpeza: 2ac15be T18C: corrige ordem de argumentos de marcar e torna o teste fail-closed real
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -q -m "not real"   (fluxo de 2ac15be, com os defeitos)
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_retorna_false_revisao_manual
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_confirmacao_inconclusiva_revisao_manual
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_clicar_enviar_levanta_captcha_bloqueio_revisao_manual
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_exception_generica_revisao_manual
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_criterio_e_anexo_com_argumentos_corretos
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_arquivo_inexistente_aborta_sem_login
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_upload_nao_aceito_erro_sem_clique
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_tema_nao_selecionado_erro_sem_clique
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_tema_selecionado_diferente_erro_sem_clique
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_confirmacao_ok_enviado
10 failed, 2 passed in 1.64s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (ffcbad8fa6c1a556f5a2703b8d6c7fc258cf3344)
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -q -m "not real"   (corrigido)
12 passed in 1.33s
$ git status --short
 M TAREFAS_ATUAIS.md
 M modulos/fluxo_envio_teste.py
 M tests/test_fluxo_envio_teste_fail_closed.py

## T18E - F3: corrige leitura da lista /minhas-redacoes (confirmação e duplicidade) [x]
- Origem: 2ª execução da T19 (21/10 18:38, Antônio). Envio feito no site
  (lista: 21/10/2026 | 0- Narração | 0.0 | Pendente; saldo 999 -> 998), mas o
  script quebrou após o clique com
  `ModuleNotFoundError: No module named 'lista_redacoes'` (confirmacao.py:33).
  Banco gravou REVISAO_MANUAL ("Excecao: ModuleNotFoundError") — fail-closed ok.
- Layout observado em /minhas-redacoes (print do Antônio, 21/10; igual à fixture):
  Data | Tema | Nota | Situação | (botão). Data sem hora: dd/mm/aaaa.
- Defeitos:
  - E1: import sem prefixo `modulos.` em confirmacao.py.
  - E2: ler_lista_redacoes lia a data na 3ª coluna (Nota). Data é a 1ª.
    Efeito: confirmação nunca acharia a linha e a duplicidade nunca
    detectaria o envio do dia (T20 reenviaria).
  - E4: lista ilegível virava "não enviado" em detectar_ja_enviado (fail-open).
- Decisão D1 (Antônio, 21/10): opção (a) — lista vazia = pode enviar
  (o saldo já é lido antes na mesma página; sem saldo, aborta).
  Lista ilegível (cabeçalho diferente, linhas sem dados) = não envia.
- Arquivos autorizados (Antônio, 21/10): modulos/confirmacao.py,
  modulos/lista_redacoes.py, testes correspondentes (arquivo novo
  tests/test_lista_redacoes_layout_real.py), TAREFAS_ATUAIS.md.
- Fora de escopo: tests/test_essenciais.py, fluxo_envio_teste.py, RAIZ,
  fallback por value, T19/T20.
- Feito: ler_lista_redacoes(page) passou a usar ler_lista_redacoes_html
  (mesmo parser da fixture); cabeçalho presente e diferente -> RuntimeError;
  linhas com <td> e nenhuma lida -> RuntimeError; detectar_ja_enviado:
  lista vazia -> (False, ""), lista ilegível -> RuntimeError (no fluxo vira
  ERRO antes do clique). Import corrigido em confirmacao.py. Removidos 4
  imports sem uso que já existiam (pyflakes).
- Limite da prova com stash: o parser HTML antigo já lia as colunas certas;
  o defeito E2 estava no parser via locator, que agora delega para ele.
- Ponto em aberto: o HTML de uma conta sem nenhuma redação não foi observado.
  Se vier uma linha-aviso com <td> (ex.: "Nenhuma redação"), o envio é
  bloqueado (fail-closed) até observar e ajustar.
PROVA:
$ python -m py_compile modulos/lista_redacoes.py modulos/confirmacao.py
[exit 0]
$ python -m pyflakes modulos/lista_redacoes.py modulos/confirmacao.py tests/test_lista_redacoes_layout_real.py
[exit 0]
$ python -m pytest tests/test_lista_redacoes_layout_real.py -v -m "not real"
tests/test_lista_redacoes_layout_real.py::test_layout_real_le_data_na_primeira_coluna PASSED [ 11%]
tests/test_lista_redacoes_layout_real.py::test_ler_lista_redacoes_da_pagina_usa_layout_real PASSED [ 22%]
tests/test_lista_redacoes_layout_real.py::test_envio_do_dia_detectado_como_ja_enviado PASSED [ 33%]
tests/test_lista_redacoes_layout_real.py::test_cabecalho_diferente_levanta PASSED [ 44%]
tests/test_lista_redacoes_layout_real.py::test_linhas_de_dados_ilegiveis_levanta PASSED [ 55%]
tests/test_lista_redacoes_layout_real.py::test_detectar_lista_com_itens_sem_dados_levanta PASSED [ 66%]
tests/test_lista_redacoes_layout_real.py::test_tabela_so_com_cabecalho_e_lista_vazia PASSED [ 77%]
tests/test_lista_redacoes_layout_real.py::test_detectar_lista_vazia_pode_enviar PASSED [ 88%]
tests/test_lista_redacoes_layout_real.py::test_aguardar_confirmacao_acha_pendente_de_hoje PASSED [100%]
============================== 9 passed in 0.75s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 72%]
...........................                                              [100%]
99 passed, 4 deselected, 8 warnings in 4.89s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat   (o arquivo de teste novo é untracked e não aparece aqui)
 TAREFAS_ATUAIS.md         | 23 ++++++++++++++++
 modulos/confirmacao.py    |  5 ++--
 modulos/lista_redacoes.py | 67 ++++++++++++++++++++---------------------------
 3 files changed, 53 insertions(+), 42 deletions(-)
[exit 0]
$ git stash push -- modulos/lista_redacoes.py modulos/confirmacao.py
Saved working directory and index state WIP on limpeza: 2322651 T18D: corrige defeitos pre-clique (criterio, caminho do anexo, upload e tema conferidos)
$ python -m pytest tests/test_lista_redacoes_layout_real.py -q -m "not real"   (modulos de 2322651, com os defeitos)
E           AttributeError: 'PaginaFalsa' object has no attribute 'locator'
E           AttributeError: 'PaginaFalsa' object has no attribute 'locator'
E       Failed: DID NOT RAISE RuntimeError
E       Failed: DID NOT RAISE RuntimeError
E       Failed: DID NOT RAISE RuntimeError
E       ModuleNotFoundError: No module named 'lista_redacoes'
FAILED tests/test_lista_redacoes_layout_real.py::test_ler_lista_redacoes_da_pagina_usa_layout_real
FAILED tests/test_lista_redacoes_layout_real.py::test_envio_do_dia_detectado_como_ja_enviado
FAILED tests/test_lista_redacoes_layout_real.py::test_cabecalho_diferente_levanta
FAILED tests/test_lista_redacoes_layout_real.py::test_linhas_de_dados_ilegiveis_levanta
FAILED tests/test_lista_redacoes_layout_real.py::test_detectar_lista_com_itens_sem_dados_levanta
FAILED tests/test_lista_redacoes_layout_real.py::test_aguardar_confirmacao_acha_pendente_de_hoje
6 failed, 3 passed in 1.10s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (aeb063716d42e841235fa1b7e1b6738642d81c6a)
$ python -m pytest tests/test_lista_redacoes_layout_real.py -q -m "not real"   (corrigido)
9 passed in 0.85s
$ git status --short
 M TAREFAS_ATUAIS.md
 M modulos/confirmacao.py
 M modulos/lista_redacoes.py
?? tests/test_lista_redacoes_layout_real.py

## T19 - F3: envio de teste de ponta a ponta (1 arquivo) — executado pelo Antônio [ ]
- Objetivo: cumprir o critério de pronto da F3 na conta de teste.
- Arquivos que PODE mexer: nenhum (o Cline só apoia; quem executa é o Antônio).
- Arquivos que NÃO pode mexer: todos — proibido o Cline digitar ENVIAR TESTE ou clicar.
- Comando de verificação (Antônio roda e cola):
  python main.py --modo-teste --envio-real
  O Antônio vê no navegador: tema selecionado -> ENEM -> arquivo anexado;
  o Antônio digita ENVIAR TESTE; 1 clique; site mostra
  "Processando arquivo" e depois "Pendente".
- PROVA: (colar aqui a saída do terminal + a situação vista no site)
- Fora de escopo: retry automático, 2º envio na mesma execução, alunos reais.

## T20 - F3: reexecução idempotente [ ]
- Objetivo: rodar de novo com os mesmos arquivos e confirmar que todos são pulados como duplicados (mesmo dia + mesmo tema).
- Arquivos que PODE mexer: nenhum (Antônio executa; o Cline só lê a saída).
- Arquivos que NÃO pode mexer: todos.
- Comando de verificação (Antônio roda e cola):
  python main.py --modo-teste --envio-real
  (saída: item(ns) marcados JA_ENVIADO / pulados; nenhum novo clique)
- PROVA: (colar aqui a saída)
- Fora de escopo: produção, outras contas.

---

## F3 concluída quando: T19 [x] + T20 [x] com provas coladas.

## Pendências de decisão (não implementar sem resposta do Antônio)
- D1: a lista /minhas-redacoes da conta de teste está vazia ou mostra as 2
  redações enviadas manualmente em 30/09? (muda o esperado de duplicidade no T19)
- D2: sinal de "upload aceito" (só resolvido em T17/T18 com observação real).
- D3: módulos NOVOS (progresso.py, relatorios.py, logging_config.py, tabelas.py,
  fluxo_dryrun.py, fluxo_analise_remota.py) ficam para depois da F3? (padrão: sim)
