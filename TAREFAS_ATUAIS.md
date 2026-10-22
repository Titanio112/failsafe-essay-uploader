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

## T19 - F3: envio de teste de ponta a ponta (1 arquivo) — executado pelo Antônio [x]
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
- Andamento (21/10, ainda [ ]):
  - 1ª execução 18:28: TypeError em selecionar_criterio antes do clique;
    nada enviado; banco ERRO. Corrigido na T18D.
  - 2ª execução 18:38: envio feito. Site /minhas-redacoes (print do Antônio):
    21/10/2026 | 0- Narração | 0.0 | Pendente | Aguarde a correção; saldo 999 -> 998.
    Confirmação automática quebrou após o clique (ModuleNotFoundError);
    banco REVISAO_MANUAL, sem reenvio. Corrigido na T18E.
  - Falta: ver a confirmação automática (Pendente) funcionando no script,
    num envio novo de outro tema/arquivo, para fechar a T19.
  - 3ª execução 19:03 (após T21, commit 6ad08a4): fechou a T19.
PROVA (execução do Antônio, 21/10/2026 19:03):
PS ...\automacao-redacoes> python main.py --modo-teste --envio-real
(... conciliação igual às anteriores ...)
2026-10-21 19:03:55,281 WARNING Fora da fila: 0/02Usuario Testes .jpg (codigo 0 repetido (revisao manual))
2026-10-21 19:03:55,281 WARNING Fora da fila: 0/03Usuario Testes Ignorar.jpg (codigo 0 repetido (revisao manual))
2026-10-21 19:03:55,281 WARNING Fora da fila: 0/04Usuario Testes Ignorar.jpg (codigo 0 repetido (revisao manual))
2026-10-21 19:03:55,281 WARNING Fora da fila: 0/05Usuario Testes Ignorar.jpg (codigo 0 repetido (revisao manual))
2026-10-21 19:03:55,281 WARNING Fora da fila: 00/005Usuario Ignorar.jpg (codigo 00 repetido (revisao manual))
Conta: ***
Fila de teste (3), na ordem; ja enviados hoje serao pulados:
  1. tema 0: 0/01Usuario Testes Ignorar.jpg
  2. tema 00: 00/004Usuario Ignorar.jpg
  3. tema 000: 000/0001Usuario Testes Ignorar.jpg
Qualquer erro ou resultado inconclusivo para a execucao.

Digite ENVIAR TESTE para confirmar a fila (qualquer outro texto cancela): ENVIAR TESTE
2026-10-21 19:04:40,762 INFO Fazendo login com conta de teste...
2026-10-21 19:04:46,773 INFO Login realizado: ***
2026-10-21 19:04:46,801 INFO Item 1/3: tema 0 (01Usuario Testes Ignorar.jpg)
2026-10-21 19:04:48,691 INFO Tema 0 ja enviado em 21/10/2026. Pulando.
2026-10-21 19:04:48,699 INFO Item 2/3: tema 00 (004Usuario Ignorar.jpg)
2026-10-21 19:04:58,305 INFO Envio confirmado: tema 00 -> Pendente
2026-10-21 19:04:58,314 INFO Item 3/3: tema 000 (0001Usuario Testes Ignorar.jpg)
2026-10-21 19:05:07,614 INFO Envio confirmado: tema 000 -> Pendente
2026-10-21 19:05:07,623 INFO Fila de teste concluida (3 item(ns)).

Banco (leitura somente, modulos/relatorios/progresso.db):
('teste@example.com', '0001Usuario Testes Ignorar.jpg', '000', 'ENVIADO', 'Confirmado na lista remota', '2026-10-21T22:05:07+00:00')
('teste@example.com', '004Usuario Ignorar.jpg', '00', 'ENVIADO', 'Confirmado na lista remota', '2026-10-21T22:04:58+00:00')
('teste@example.com', '01Usuario Testes Ignorar.jpg', '0', 'JA_ENVIADO', 'Ja enviado na lista remota', '2026-10-21T22:04:48+00:00')

## T20 - F3: reexecução idempotente [x]
- Objetivo: rodar de novo com os mesmos arquivos e confirmar que todos são pulados como duplicados (mesmo dia + mesmo tema).
- Arquivos que PODE mexer: nenhum (Antônio executa; o Cline só lê a saída).
- Arquivos que NÃO pode mexer: todos.
- Comando de verificação (Antônio roda e cola):
  python main.py --modo-teste --envio-real
  (saída: item(ns) marcados JA_ENVIADO / pulados; nenhum novo clique)
- PROVA (execução do Antônio, 21/10/2026 18:53, após T18E commit ff392b1):
PS ...\automacao-redacoes> python main.py --modo-teste --envio-real
2026-10-21 18:53:45,431 INFO Modo teste: processando aluno virtual Usuario Testes Ignorar
Pastas de temas: 3 | JPGs encontrados: 8
(... resumo da conciliação igual ao da T19 ...)
Arquivo: 01Usuario Testes Ignorar.jpg
Codigo do tema: 0
Conta: ***

Digite ENVIAR TESTE para confirmar (qualquer outro texto cancela): ENVIAR TESTE
2026-10-21 18:54:08,531 INFO Fazendo login com conta de teste...
2026-10-21 18:54:14,586 INFO Login realizado: ***
2026-10-21 18:54:16,674 INFO Tema 0 ja enviado em 21/10/2026. Pulando.

Banco (leitura somente, modulos/relatorios/progresso.db):
('teste@example.com', '01Usuario Testes Ignorar.jpg', '0', 'JA_ENVIADO', 'Ja enviado na lista remota', '2026-10-21T21:54:16+00:00')
Nenhum clique: o fluxo retorna antes de abrir o formulário.
- Fora de escopo: produção, outras contas.

## T21 - F3: modo teste percorre todos os arquivos de teste [x]
- Pedido do Antônio (21/10): em vez de parar no 1º arquivo (já enviado -> pula
  e termina), seguir para os próximos e enviar os liberados.
- Decisões do Antônio (21/10):
  - todos os liberados numa execução, um de cada vez, cada um esperando o
    Pendente; qualquer problema (ERRO ou REVISAO_MANUAL) para a execução toda;
  - ENVIAR TESTE digitado uma vez para a lista inteira, que é mostrada antes.
- Regras mantidas: mesmo dia + mesmo tema no site = JA_ENVIADO (pula e segue);
  1 arquivo por código por execução — no modo teste todos os arquivos são do
  mesmo aluno virtual, então só o 1º arquivo (ordem alfabética) de cada código
  entra; os demais ficam fora da fila (código repetido -> revisão manual);
  pasta sem código fica fora. Nenhum retry, nenhum 2º clique no mesmo item.
- Arquivos: modulos/fluxo_envio_teste.py (orquestra), novos
  modulos/fila_teste.py (monta a fila) e modulos/envio_teste_item.py
  (envio de 1 item, com o fail-closed da T18B–T18D), testes, TAREFAS_ATUAIS.md.
- Fora de escopo: produção, RAIZ, fallback por value, main.py.
- Feito: fluxo_envio_teste.py (300 -> 127 linhas) monta a fila, mostra a
  lista, pede ENVIAR TESTE uma vez, faz login uma vez e chama
  enviar_item_teste para cada item; para no 1º estado que não seja
  ENVIADO/JA_ENVIADO. O fail-closed de cada item (T18B–T18D) foi movido sem
  mudança de regra para envio_teste_item.py. Com a pasta de teste atual a
  fila é: 0/01..., 00/004..., 000/0001... (5 arquivos ficam fora por código repetido).
- Limite da prova com stash: com o fluxo antigo, os patches de
  envio_teste_item não se aplicam; os 2 testes que "passam" ali passam
  porque o fluxo antigo para antes de clicar, não porque percorre a fila.
- Pendência vista no caminho (fora de escopo): o bloco `if __name__ == "__main__"`
  de fluxo_envio_teste.py usa `from progresso_relatorio import` sem `modulos.`.
PROVA:
$ python -m py_compile modulos/fluxo_envio_teste.py modulos/envio_teste_item.py modulos/fila_teste.py
[exit 0]
$ python -m pyflakes modulos/fluxo_envio_teste.py modulos/envio_teste_item.py modulos/fila_teste.py tests/test_fila_teste.py tests/test_fluxo_envio_teste_fail_closed.py
[exit 0]
$ python -m pytest tests/test_fila_teste.py tests/test_fluxo_envio_teste_fail_closed.py -v -m "not real"
tests/test_fila_teste.py::test_layout_da_pasta_de_teste PASSED           [  5%]
tests/test_fila_teste.py::test_pasta_sem_codigo_fica_fora PASSED         [ 10%]
tests/test_fila_teste.py::test_arquivo_inexistente_fica_fora_e_proximo_do_codigo_entra PASSED [ 15%]
tests/test_fila_teste.py::test_codigos_sao_strings_distintas PASSED      [ 20%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_retorna_false_revisao_manual PASSED [ 25%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_confirmacao_inconclusiva_revisao_manual PASSED [ 30%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_clicar_enviar_levanta_captcha_bloqueio_revisao_manual PASSED [ 35%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_aguardar_confirmacao_levanta_exception_generica_revisao_manual PASSED [ 40%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_falha_antes_do_clique_saldo_indisponivel_erro PASSED [ 45%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_falha_antes_do_clique_codigo_invalido_erro PASSED [ 50%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_criterio_e_anexo_com_argumentos_corretos PASSED [ 55%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_arquivo_inexistente_aborta_sem_login PASSED [ 60%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_upload_nao_aceito_erro_sem_clique PASSED [ 65%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_tema_nao_selecionado_erro_sem_clique PASSED [ 70%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_tema_selecionado_diferente_erro_sem_clique PASSED [ 75%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_pula_ja_enviado_e_envia_o_proximo PASSED [ 80%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_para_no_primeiro_inconclusivo PASSED [ 85%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_para_no_primeiro_erro_pre_clique PASSED [ 90%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_cancelada_nao_faz_login PASSED [ 95%]
tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_confirmacao_ok_enviado PASSED [100%]
============================= 20 passed in 1.57s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 67%]
...................................                                      [100%]
107 passed, 4 deselected, 8 warnings in 5.21s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat   (arquivos novos são untracked e não aparecem aqui)
 TAREFAS_ATUAIS.md                           |  17 ++
 modulos/fluxo_envio_teste.py                | 240 ++++------------------------
 tests/test_fluxo_envio_teste_fail_closed.py | 101 ++++++++++--
 3 files changed, 138 insertions(+), 220 deletions(-)
[exit 0]
$ git status --short
 M TAREFAS_ATUAIS.md
 M modulos/fluxo_envio_teste.py
 M tests/test_fluxo_envio_teste_fail_closed.py
?? modulos/envio_teste_item.py
?? modulos/fila_teste.py
?? tests/test_fila_teste.py
[exit 0]
$ git stash push -- modulos/fluxo_envio_teste.py
Saved working directory and index state WIP on limpeza: c3ffcd8 T20: registra prova de reexecucao idempotente e andamento da T19
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -q -m "not real" -k fila   (fluxo de c3ffcd8: só o 1º arquivo)
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_pula_ja_enviado_e_envia_o_proximo
FAILED tests/test_fluxo_envio_teste_fail_closed.py::TestFailClosedPosClique::test_fila_para_no_primeiro_inconclusivo
2 failed, 2 passed, 12 deselected in 1.01s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (e84272aef1725e0f9b1f88ccada1606bdc4803fa)
$ python -m pytest tests/test_fluxo_envio_teste_fail_closed.py -q -m "not real" -k fila   (T21)
4 passed, 12 deselected in 0.92s

## T22 - Pós-F3: RAIZ, fallback por value, import do __main__ e docs [x]
- Pedido/autorização do Antônio (21/10).
- R1: `RAIZ` em modulos/config.py apontava para `modulos/` (sobra da
  modularização). Efeito: banco/relatórios em modulos/relatorios/, padrão de
  pasta_raiz em modulos/redacoes_pendentes/, config.ini procurado em modulos/.
  Corrigir para a raiz do projeto.
- R2: `selecionar_tema_por_codigo` tentava `select_option(value=codigo)` se a
  seleção pelo texto falhasse; o value do combo é o id da proposta, não o
  código. Remover o fallback (a T18D já confere o tema selecionado).
- R3: bloco `__main__` de fluxo_envio_teste.py: `from progresso_relatorio`
  sem `modulos.`.
- R4: PROJECT_MEMORY.md e AGENTS.md com o estado pós-F3.
- Arquivos: modulos/config.py, modulos/formulario_envio.py,
  modulos/fluxo_envio_teste.py (só o __main__), teste novo
  tests/test_pos_f3.py, PROJECT_MEMORY.md, AGENTS.md, TAREFAS_ATUAIS.md.
- Dados: NÃO mover/apagar bancos. modulos/relatorios/progresso.db tem o
  histórico de 21/10; relatorios/progresso.db é o antigo (06–07/10). A troca
  fica para o Antônio (comandos no relatório).
- Fora de escopo: caminhos relativos ao diretório atual (dados/, diagnosticos/,
  testes/), F4.
- Feito: RAIZ = Path(__file__).resolve().parent.parent; fallback por value
  removido (e 2 imports sem uso de formulario_envio.py); import do __main__
  com `modulos.`; teste novo varre modulos/*.py e main.py (inclusive dentro
  de funções) atrás de import interno sem prefixo. PROJECT_MEMORY.md e
  AGENTS.md atualizados (módulos, lista, upload, D1, seletores, pendências F4).
PROVA:
$ python -m py_compile modulos/config.py modulos/formulario_envio.py modulos/fluxo_envio_teste.py
[exit 0]
$ python -m pyflakes modulos/config.py modulos/formulario_envio.py modulos/fluxo_envio_teste.py tests/test_pos_f3.py
[exit 0]
$ python -m pytest tests/test_pos_f3.py -v -m "not real"
tests/test_pos_f3.py::test_raiz_e_a_pasta_do_projeto PASSED              [ 20%]
tests/test_pos_f3.py::test_caminhos_padrao_ficam_na_raiz PASSED          [ 40%]
tests/test_pos_f3.py::test_selecao_pelo_texto_falha_nao_tenta_value PASSED [ 60%]
tests/test_pos_f3.py::test_codigo_ausente_no_combo_nao_seleciona_nada PASSED [ 80%]
tests/test_pos_f3.py::test_nenhum_import_interno_sem_prefixo_modulos PASSED [100%]
============================== 5 passed in 0.57s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 64%]
........................................                                 [100%]
112 passed, 4 deselected, 8 warnings in 4.95s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat   (tests/test_pos_f3.py é novo/untracked e não aparece aqui)
 AGENTS.md                    | 94 +++++++++++++++++++++++++++-----------------
 PROJECT_MEMORY.md            | 53 +++++++++++++++++--------
 TAREFAS_ATUAIS.md            | 21 ++++++++++
 modulos/config.py            |  3 +-
 modulos/fluxo_envio_teste.py |  2 +-
 modulos/formulario_envio.py  | 16 ++------
 6 files changed, 124 insertions(+), 65 deletions(-)
[exit 0]
$ git stash push -- modulos/config.py modulos/formulario_envio.py modulos/fluxo_envio_teste.py
Saved working directory and index state WIP on limpeza: ea09e34 T19: registra prova do envio de teste com confirmacao automatica; F3 concluida
$ python -m pytest tests/test_pos_f3.py -q -m "not real"   (modulos de ea09e34, antes da T22)
FAILED tests/test_pos_f3.py::test_raiz_e_a_pasta_do_projeto - AssertionError:...
FAILED tests/test_pos_f3.py::test_caminhos_padrao_ficam_na_raiz - AssertionEr...
FAILED tests/test_pos_f3.py::test_selecao_pelo_texto_falha_nao_tenta_value - ...
FAILED tests/test_pos_f3.py::test_codigo_ausente_no_combo_nao_seleciona_nada
FAILED tests/test_pos_f3.py::test_nenhum_import_interno_sem_prefixo_modulos
5 failed in 0.75s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (62f0fdfd1a4f5a05987f15b0a2a9c030a457eddd)
$ python -m pytest tests/test_pos_f3.py -q -m "not real"   (T22)
5 passed in 0.66s

## T23 - Remove todos os restos de "sala" do código [x]
- Decisão do Antônio (21/10): salas NUNCA existiram — foram alucinação do
  Cline. Confirmação de produção = `ENVIAR`.
- Restos encontrados (grep -i sala em modulos/, main.py, tests/):
  - modulos/config.py:108 `cfg.coluna_sala` — campo não existe; com seção
    `[planilha]` no config.ini dá AttributeError (testado).
  - modulos/planilha_arquivos.py: campo `Aluno.sala`, leitura da coluna
    "sala" com padrão "SEM_SALA", docstring "aluno da sala".
  - modulos/estados.py: docstring "aluno da sala".
  - modulos/progresso_relatorio.py: coluna "sala" no CSV e prefixo `[sala]`
    na fila do dry-run.
  - modulos/fluxo_envio_teste.py e main.py: `Aluno(..., sala="TESTE")`.
  - tests/test_essenciais.py: coluna "sala" nas planilhas de teste e
    filtros `a.sala == "A"` / `"TESTE"`; tests/test_identidade.py: `sala="TESTE"`.
- Autorização (Antônio, 21/10): mexer em tests/test_essenciais.py só para
  tirar a sala dos dados de teste, sem enfraquecer nenhum teste. Os filtros
  por sala viram filtros pelos MESMOS nomes (mesmos subconjuntos de alunos).
- Planilha real com coluna extra (ex.: "sala") continua sendo lida: coluna
  ignorada. Teste novo garante isso e barra a palavra "sala" no código.
- Fora de escopo: docs históricos (DECISOES_PENDENTES.md, INVENTARIO.md),
  relatórios já gerados em relatorios/.
- Feito: linha coluna_sala removida; Aluno = (nome, email, creditos);
  carregar_alunos lê só nome/e-mail e ignora colunas extras; CSV sem coluna
  "sala" e fila do dry-run sem prefixo `[sala]`; modo teste e main sem
  sala="TESTE"; docstrings corrigidas. Testes: coluna "sala" tirada das
  planilhas de teste; filtros `a.sala == "A"/"TESTE"` trocados por
  NOMES_GRUPO_PRINCIPAL (Ana Lalara, Bruno, Diana — os mesmos da antiga "A")
  e NOMES_CONTA_TESTE (Usuario Testes Ignorar). Mesma quantidade de testes
  e de asserts (abaixo).
- Pendência vista (fora de escopo): pyflakes acusa imports sem uso que já
  existiam em main.py (32), planilha_arquivos.py (7) e vários testes.
  tests/test_estatico.py passa assim mesmo. Nenhum aviso novo nesta tarefa.
PROVA:
$ python -m py_compile modulos/config.py modulos/planilha_arquivos.py modulos/estados.py modulos/progresso_relatorio.py modulos/fluxo_envio_teste.py main.py
[exit 0]
$ python -m pytest tests/test_sem_sala.py -v -m "not real"
tests/test_sem_sala.py::test_codigo_nao_menciona_sala PASSED             [ 20%]
tests/test_sem_sala.py::test_aluno_so_tem_nome_email_creditos PASSED     [ 40%]
tests/test_sem_sala.py::test_config_ini_com_secao_planilha_nao_quebra PASSED [ 60%]
tests/test_sem_sala.py::test_planilha_com_coluna_extra_e_lida_e_coluna_ignorada PASSED [ 80%]
tests/test_sem_sala.py::test_relatorios_sem_sala PASSED                  [100%]
============================== 5 passed in 0.55s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 61%]
.............................................                            [100%]
117 passed, 4 deselected, 8 warnings in 5.34s
[exit 0]
$ git diff --check
[exit 0]
$ git diff --stat   (tests/test_sem_sala.py é novo/untracked e não aparece aqui)
 TAREFAS_ATUAIS.md              | 22 ++++++++++++
 main.py                        |  4 +--
 modulos/config.py              |  1 -
 modulos/estados.py             |  2 +-
 modulos/fluxo_envio_teste.py   |  2 +-
 modulos/planilha_arquivos.py   | 17 +++------
 modulos/progresso_relatorio.py |  5 ++-
 tests/test_essenciais.py       | 82 ++++++++++++++++++++++--------------------
 tests/test_identidade.py       | 14 ++++----
 9 files changed, 83 insertions(+), 66 deletions(-)
[exit 0]
$ pyflakes: avisos por arquivo, HEAD x agora (sem avisos novos)
modulos/config.py: HEAD=0 agora=0 novos=0
modulos/planilha_arquivos.py: HEAD=7 agora=7 novos=0
modulos/estados.py: HEAD=0 agora=0 novos=0
modulos/progresso_relatorio.py: HEAD=0 agora=0 novos=0
modulos/fluxo_envio_teste.py: HEAD=0 agora=0 novos=0
main.py: HEAD=32 agora=32 novos=0
tests/test_essenciais.py: HEAD=45 agora=45 novos=0
tests/test_identidade.py: HEAD=7 agora=7 novos=0
tests/test_sem_sala.py: [exit 0]
$ testes e asserts em test_essenciais.py / test_identidade.py: HEAD x agora
tests/test_essenciais.py: def test_ HEAD=50 agora=50 | assert HEAD=154 agora=154
tests/test_identidade.py: def test_ HEAD=7 agora=7 | assert HEAD=22 agora=22
$ git stash push -- modulos/config.py modulos/planilha_arquivos.py modulos/estados.py modulos/progresso_relatorio.py modulos/fluxo_envio_teste.py main.py
Saved working directory and index state WIP on limpeza: 8b035fe docs: registra decisao 5.3 (confirmacao ENVIAR; salas nunca existiram)
$ python -m pytest tests/test_sem_sala.py -q -m "not real"   (codigo de 8b035fe, com sala)
FAILED tests/test_sem_sala.py::test_codigo_nao_menciona_sala - assert ['estad...
FAILED tests/test_sem_sala.py::test_aluno_so_tem_nome_email_creditos - Assert...
FAILED tests/test_sem_sala.py::test_config_ini_com_secao_planilha_nao_quebra
FAILED tests/test_sem_sala.py::test_planilha_com_coluna_extra_e_lida_e_coluna_ignorada
FAILED tests/test_sem_sala.py::test_relatorios_sem_sala - TypeError: Aluno.__...
5 failed in 0.73s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (e7b12cdcf80cae0ddc08d4ddef383fbaf364f54f)
$ python -m pytest tests/test_sem_sala.py -q -m "not real"   (T23)
5 passed in 0.63s

## T24 - F4: fluxo de envio de produção (offline; envio real só pelo Antônio) [x]
- Pedido do Antônio (22/10): seguir sozinho até ficar pronto, usando bom senso
  nas dúvidas, numa branch separada para poder voltar. Branch: `f4-producao`
  (criada a partir de `limpeza` em ea80e09). Para voltar: `git checkout limpeza`.
- Decisões de bom senso (REVISAR, Antônio pode mudar qualquer uma):
  - P1 Fila real = só `EXATO_UNICO` da conciliação (fuzzy, ambíguo, sem par,
    código inválido/repetido nunca entram — regra já existente).
  - P2 Não reenviar o que o banco já registra como ENVIADO, JA_ENVIADO ou
    REVISAO_MANUAL (nem em outro dia: é o mesmo arquivo). ERRO pode tentar
    de novo (não houve clique).
  - P3 Limite de 4 envios por aluno **por execução** (`max_envios_por_aluno`);
    o resto fica para a próxima execução. O saldo de créditos é lido antes de
    cada item; saldo 0/ilegível para o aluno.
  - P4 Uma confirmação `ENVIAR` para o lote inteiro, mostrado antes
    (aluno, e-mail mascarado, tema, arquivo). `--limite-alunos` e
    `--limite-redacoes` cortam o lote antes da confirmação.
  - P5 Senha: `ESQUEMA_SENHA_PADRAO` (.env ou getpass). Um contexto de
    navegador por aluno (sem cookie de um aluno no outro).
  - P6 Falhas: login/identidade de um aluno falha -> itens dele ERRO e segue
    para o próximo aluno (nada clicado). ERRO num item -> para esse aluno e
    segue. REVISAO_MANUAL (depois do clique) ou Captcha/bloqueio -> para a
    execução inteira.
  - P7 Pausa aleatória de 8–15 s entre envios (`pausa_envio_*` do config).
  - P8 Códigos do site na conciliação: `dados/temas_site.csv` como referência
    (igual ao dry-run); a trava real é o combo da conta logada, conferido
    item a item antes do clique (T18D).
- Arquivos: main.py, modulos/envio_teste_item.py -> modulos/envio_item.py
  (o envio de 1 item é o mesmo do teste), modulos/fila_teste.py (campo de
  chave do progresso), novos modulos/fila_producao.py e
  modulos/fluxo_envio_producao.py, testes, docs.
- Proibido nesta tarefa: rodar main.py, abrir navegador, login, digitar ENVIAR.
- Feito:
  - `python main.py --envio-real` (sem --modo-teste) deixou de ser bloqueado:
    concilia, gera os relatórios e chama `executar_envio_producao`.
    Fail-closed antes de ler a planilha se `dados/temas_site.csv` não tiver
    códigos; erro claro se a planilha não existir.
  - Sem `--envio-real` (dry-run) imprime `[BLOQUEADO] Envio real desativado.`
    no fim, como o AGENTS.md documenta.
  - main.py: 32 imports sem uso removidos (pyflakes 32 -> 0).
  - Nuance de P6: Captcha detectado DENTRO de um item (antes do clique) vira
    ERRO só daquele aluno; o login do próximo aluno pega o bloqueio e para tudo.
- Teste protegido alterado (com justificativa): em tests/test_essenciais.py,
  `test_fail_closed_envio_real_sem_codigos_site` fixava "produção sempre
  aborta" (regra da F3). Agora testa o fail-closed da F4: sem
  dados/temas_site.csv -> retorna 2, mensagem cita o CSV e a planilha NÃO é
  lida. Mesmos 50 testes; asserts 154 -> 155.
PROVA:
$ python -m py_compile main.py modulos/envio_item.py modulos/fila_teste.py modulos/fila_producao.py modulos/fluxo_envio_producao.py modulos/fluxo_envio_teste.py
[exit 0]
$ python -m pyflakes main.py modulos/envio_item.py modulos/fila_teste.py modulos/fila_producao.py modulos/fluxo_envio_producao.py modulos/fluxo_envio_teste.py tests/test_fila_producao.py tests/test_fluxo_envio_producao.py tests/test_fluxo_envio_teste_fail_closed.py
[exit 0]
$ python -m pytest tests/test_fila_producao.py tests/test_fluxo_envio_producao.py -v -m "not real"
tests/test_fila_producao.py::test_so_exato_unico_entra_com_chave_pasta_arquivo PASSED [  4%]
tests/test_fila_producao.py::test_nao_reenvia_o_que_o_banco_ja_registrou[ENVIADO] PASSED [  9%]
tests/test_fila_producao.py::test_nao_reenvia_o_que_o_banco_ja_registrou[JA_ENVIADO] PASSED [ 13%]
tests/test_fila_producao.py::test_nao_reenvia_o_que_o_banco_ja_registrou[REVISAO_MANUAL] PASSED [ 18%]
tests/test_fila_producao.py::test_erro_anterior_pode_tentar_de_novo PASSED [ 22%]
tests/test_fila_producao.py::test_limite_de_envios_por_aluno_nesta_execucao PASSED [ 27%]
tests/test_fila_producao.py::test_codigo_repetido_arquivo_inexistente_e_sem_codigo_ficam_fora PASSED [ 31%]
tests/test_fila_producao.py::test_limite_de_alunos_e_de_redacoes PASSED  [ 36%]
tests/test_fluxo_envio_producao.py::test_lote_inteiro_enviado_uma_confirmacao_um_contexto_por_aluno PASSED [ 40%]
tests/test_fluxo_envio_producao.py::test_confirmacao_diferente_de_ENVIAR_cancela_sem_login[enviar] PASSED [ 45%]
tests/test_fluxo_envio_producao.py::test_confirmacao_diferente_de_ENVIAR_cancela_sem_login[ENVIAR TESTE] PASSED [ 50%]
tests/test_fluxo_envio_producao.py::test_confirmacao_diferente_de_ENVIAR_cancela_sem_login[] PASSED [ 54%]
tests/test_fluxo_envio_producao.py::test_confirmacao_diferente_de_ENVIAR_cancela_sem_login[sim] PASSED [ 59%]
tests/test_fluxo_envio_producao.py::test_login_falha_marca_erro_do_aluno_e_segue PASSED [ 63%]
tests/test_fluxo_envio_producao.py::test_identidade_divergente_nao_envia_nada_do_aluno PASSED [ 68%]
tests/test_fluxo_envio_producao.py::test_erro_em_item_para_o_aluno_e_segue_para_o_proximo PASSED [ 72%]
tests/test_fluxo_envio_producao.py::test_revisao_manual_para_a_execucao_inteira PASSED [ 77%]
tests/test_fluxo_envio_producao.py::test_captcha_no_login_para_a_execucao_inteira PASSED [ 81%]
tests/test_fluxo_envio_producao.py::test_nada_para_enviar_nao_pede_confirmacao PASSED [ 86%]
tests/test_fluxo_envio_producao.py::test_limites_chegam_ao_lote PASSED   [ 90%]
tests/test_fluxo_envio_producao.py::test_main_envio_real_chama_fluxo_de_producao PASSED [ 95%]
tests/test_fluxo_envio_producao.py::test_main_sem_envio_real_nao_chama_fluxo_de_producao PASSED [100%]
============================= 22 passed in 1.84s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 51%]
...................................................................      [100%]
139 passed, 4 deselected, 8 warnings in 8.31s
[exit 0]
$ git diff --check
[exit 0]
$ pyflakes main.py: HEAD x agora
HEAD=32 agora=0
$ testes e asserts em test_essenciais.py: HEAD x agora
def test_ HEAD=50 agora=50 | assert HEAD=154 agora=155
$ git stash push -- main.py
Saved working directory and index state WIP on f4-producao: ea80e09 T23: remove todos os restos de sala (config, Aluno, planilha, relatorios, testes)
$ python -m pytest tests/test_fluxo_envio_producao.py tests/test_essenciais.py -q -m "not real" -k "main or fail_closed"   (main.py de ea80e09: producao bloqueada)
FAILED tests/test_fluxo_envio_producao.py::test_main_envio_real_chama_fluxo_de_producao
FAILED tests/test_fluxo_envio_producao.py::test_main_sem_envio_real_nao_chama_fluxo_de_producao
FAILED tests/test_essenciais.py::test_fail_closed_envio_real_sem_codigos_site
3 failed, 2 passed, 59 deselected in 1.11s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (8e358da3c487158f21a8465acae8c1df475cf538)
$ (mesmo comando, T24)
5 passed, 59 deselected in 1.08s

## T25 - F4: primeiro envio real de produção (1 aluno) — executado pelo Antônio [ ]
- Pré-requisitos (Antônio) — atualizado na T26:
  1. Lista de alunos: `dados/dados_alunos.csv` (já existe; Nome;Email; a
     coluna Senha é ignorada e pode ser apagada).
  2. `.env` com `ESQUEMA_SENHA_PADRAO` (senão o script pergunta a senha).
  3. Redações em `redacoes_pendentes/<código> - <título>/<Nome>.JPG`.
     Hoje `redacoes_pendentes/` tem cópias de TESTE (0, 00, 000, 88) — tirar
     de lá antes. As reais estão em `Redações plataforma/3B - <título>/`:
     copiar para `redacoes_pendentes/` trocando "3B" pelo código do tema
     (o dry-run sugere o código).
  4. `dados/temas_site.csv` com os códigos do combo (tem 108, de 01/10).
  5. (Recomendado) a troca do banco de progresso explicada na T22.
- Passo 0 (T27), atualizar os códigos dos temas (só leitura no site, conta
  de teste; digitar ANALISAR):
  python main.py --analise-remota
- Passo 1, dry-run (não envia, não abre navegador):
  python main.py
  Conferir `relatorios/relatorio_conciliacao.csv` e, em
  `dados/nomes_aprovados.csv`, escrever `sim` nas sugestões certas;
  rodar o dry-run de novo e ver a fila crescer.
- Passo 2, envio real de 1 aluno e 1 redação:
  python main.py --envio-real --limite-alunos 1 --limite-redacoes 1
  Conferir a lista mostrada; digitar ENVIAR; ver no site
  (/minhas-redacoes do aluno) a linha nova como "Pendente".
- Passo 3, reexecução idempotente: o mesmo comando deve mostrar o item como
  já registrado (fora do lote) ou JA_ENVIADO, sem novo clique.
- PROVA: (colar a saída dos 3 passos + a situação vista no site)
- Fora de escopo: lote grande antes deste passar.

## T26 - F4: produção com os dados reais (lista em dados/, nomes aprovados, senha só no .env) [x]
- Pedido do Antônio (22/10): lista de alunos em `dados/` (nome, e-mail, senha
  padrão); senha só no .env ("mais seguro"); analisar o que impede a
  produção de funcionar na prática e corrigir; perguntar o que for ambíguo.
- Segurança feita antes (commit e0bd23e): `dados/dados_alunos.csv` no .gitignore
  (nunca tinha sido versionado — `git log --all` vazio).
- Análise com os dados reais (só leitura; nada enviado):
  - `dados/dados_alunos.csv`: 70 alunos, `Nome;Email;Senha`, sem nome repetido.
    O código não lia esse arquivo (lia um XLSX em redacoes_pendentes/ que não existe).
  - `Redações plataforma/`: 4 pastas, 130 JPGs (extensão `.JPG`), arquivo = nome
    do aluno (ex.: "Alice Lalato.JPG").
  - Nomes: só **4/130** batem exato com a lista (regra atual). **107** são nome
    curto que cabe em um único aluno (ex.: "Ana Lalara Larili" -> "Ana Lalara
    Larili dos Larito"); 2 cabem em vários; 17 sem candidato (erros de digitação
    como "Isabela Larulii", "Gilherme", sufixos "2"/"impactos", e "X em branco").
  - Temas: as pastas são "3B - <título>": "3B" NÃO é código (regra), então
    hoje TODAS dariam SEM_CODIGO. Só 1 dos 4 títulos existe em
    dados/temas_site.csv (código 100, filiação; CSV lido em 01/10).
- Mudanças desta tarefa:
  - R1 Lista de alunos padrão = `dados/dados_alunos.csv` (`;` ou `,`, colunas
    Nome/Email; XLSX continua aceito pelo config). Coluna Senha é IGNORADA
    (aviso na tela); senha só de `ESQUEMA_SENHA_PADRAO` no .env.
  - R2 (1ª tentativa descartada) Um estado `NOME_PARCIAL_UNICO` que mandava
    nome curto direto para a fila quebrou o teste protegido
    `test_conciliacao_sugestao_fuzzy` ("variação de nome -> revisão humana
    obrigatória"). A regra está certa (aluno errado é grave): revertido.
  - R2 (feito) `dados/nomes_aprovados.csv` (`;`, no .gitignore):
    nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo. O dry-run ACRESCENTA
    sugestões (nome parcial único, ou parecido >= 70%) com `aprovado` vazio e
    nunca mexe no que já existe. Linha com `aprovado=sim` faz aquele nome de
    arquivo valer como nome exato do aluno (EXATO_UNICO, observação
    "nome aprovado"). E-mail fora da lista ou mesmo nome aprovado para 2
    alunos -> ignorado com aviso. Folha "em branco" nunca vira sugestão.
    Revisão humana continua obrigatória, mas é feita UMA vez por nome.
  - R3 Pasta sem código: o dry-run lista as pastas sem código e o tema mais
    parecido do dados/temas_site.csv ("provavel" >= 85%, "FRACO, conferir"
    60–85%, nenhum < 60%). Só sugere; renomear a pasta é com o Antônio.
- Simulação offline com os dados reais (sem gravar em dados/, pastas
  renomeadas em memória para 100–103): sem nomes aprovados -> fila 4/130;
  65 sugestões (37 "nome parcial", 28 "parecido"); aprovando só as 37
  "nome parcial" -> **fila 87/130**. Com as pastas originais "3B - ..." a fila
  é 0 (falta código). Sobra: só primeiro nome ("Douglas"), erros de
  digitação (sugeridos para aprovar), 2 ambíguos, 17 sem candidato.
- Limite da prova com stash: os testes novos importam funções novas; com o
  código antigo a coleta falha (ImportError), não um assert por assert.
- Fora de escopo (perguntar ao Antônio): análise remota para atualizar
  temas_site.csv (3 dos 4 temas reais não estão nele).
PROVA:
$ python -m py_compile main.py modulos/config.py modulos/planilha_arquivos.py modulos/nomes_aprovados.py modulos/sugestao_temas.py
[exit 0]
$ python -m pyflakes main.py modulos/config.py modulos/nomes_aprovados.py modulos/sugestao_temas.py tests/test_dados_reais_t26.py tests/test_fluxo_envio_producao.py
[exit 0]
$ python -m pytest tests/test_dados_reais_t26.py -v -m "not real"
tests/test_dados_reais_t26.py::test_padrao_e_dados_alunos_csv PASSED     [ 11%]
tests/test_dados_reais_t26.py::test_csv_com_senha_le_nome_email_e_ignora_senha[;] PASSED [ 22%]
tests/test_dados_reais_t26.py::test_csv_com_senha_le_nome_email_e_ignora_senha[,] PASSED [ 33%]
tests/test_dados_reais_t26.py::test_csv_sem_colunas_obrigatorias_da_erro_claro PASSED [ 44%]
tests/test_dados_reais_t26.py::test_sem_aprovacao_nome_curto_nao_entra_na_fila PASSED [ 55%]
tests/test_dados_reais_t26.py::test_sugestoes_gravadas_sem_aprovar_nada PASSED [ 66%]
tests/test_dados_reais_t26.py::test_nome_aprovado_entra_na_fila_como_exato PASSED [ 77%]
tests/test_dados_reais_t26.py::test_aprovacao_com_email_fora_da_lista_ou_em_conflito_e_ignorada PASSED [ 88%]
tests/test_dados_reais_t26.py::test_sugere_codigo_so_para_pasta_sem_codigo PASSED [100%]
============================== 9 passed in 0.53s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 48%]
........................................................................ [ 97%]
....                                                                     [100%]
148 passed, 4 deselected, 8 warnings in 6.75s
[exit 0]
$ git diff --check
[exit 0]
$ pyflakes planilha_arquivos.py: HEAD x agora
HEAD=7 agora=6
$ git stash push -- modulos/config.py modulos/planilha_arquivos.py main.py
Saved working directory and index state WIP on f4-producao: e0bd23e chore: ignora dados/dados_alunos.csv (tem senhas)
$ python -m pytest tests/test_dados_reais_t26.py -q -m "not real"   (codigo de e0bd23e)
ERROR tests/test_dados_reais_t26.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.91s
[exit 2]
$ git stash pop
Dropped refs/stash@{0} (1640594de31c33172e9ea1c7420c6e65728e09e9)
$ (mesmo comando, T26)
9 passed in 0.62s

## T27 - F4: análise remota, identidade tolerante, "Processando", folha em branco, relatório [x]
- Pedido do Antônio (22/10): "pode implementar todas" as sugestões da T26;
  gostou da análise remota; deixar o script "mais inteligente" (pode passar
  um pouco do MVP); achou erro -> reportar e resolver.
- Decisões de bom senso (revisar):
  - Q1 Análise remota `--analise-remota` + confirmação `ANALISAR`: login na
    CONTA DE TESTE (nenhum aluno é usado), abre /wordings/new, lê o combo de
    temas e regrava `dados/temas_site.csv` (backup do anterior em
    `dados/temas_site.<data>.bak.csv`). Só leitura no site: nada é enviado.
  - Q2 Identidade: aceita nome igual OU um nome contido no outro com a mesma
    1ª palavra (site abreviado: "Ana Lalara" x "Ana Lalara Larili dos Larito").
    Pessoa diferente continua IdentidadeDivergente (aluno inteiro ERRO).
  - Q3 "Processando arquivo": se no fim dos 120 s a linha nova do tema de hoje
    está em "Processando arquivo", conta como RECEBIDA (ENVIADO). Antes do
    envio a lista não tinha esse tema hoje (checagem de duplicidade), então a
    linha só pode ser a nossa. Sem linha nenhuma -> REVISAO_MANUAL, como antes.
  - Q4 Folha "em branco" (nome do arquivo com "em branco"): nunca entra na
    fila, nem aprovada em nomes_aprovados.csv -> REVISAO_MANUAL.
  - Q5 (extra) Ao fim do envio de produção grava
    `relatorios/envio_<data_hora>.csv` (aluno, e-mail mascarado, arquivo,
    tema, estado, detalhe) para conferir o que aconteceu.
- Bugs achados viram `docs/qa-issues/NNN-*.md` (regra 9 do AGENTS.md); sem
  remoto no GitHub, `gh issue` não é possível neste repositório.
- Bugs achados e resolvidos:
  - 001 (`docs/qa-issues/001-codigo-repetido-no-combo.md`): `0000` aparece 2x
    no combo, mas main.py lia os códigos num set (sumia o repetido) e a trava
    antes do clique escolhia o 1º `0000` às cegas -> redação podia ir para o
    Simulado errado. Agora: lista com repetidos (conciliação marca SIMULADO) e
    `envio_item` dá ERRO sem clicar se o código aparece 2x no combo.
  - (pego pelo teste novo antes do commit) folha em branco ainda contava em
    "dois arquivos do mesmo aluno no mesmo tema" e bloqueava a redação
    verdadeira do aluno. Corrigido na 1ª passada da conciliação.
- Teste protegido alterado (justificativa): `test_fail_closed_analise_remota_sem_codigos_site`
  fixava "--analise-remota sempre aborta" (não existia). Agora: sem digitar
  ANALISAR -> retorna 2 sem abrir navegador, sem gravar CSV e sem ler planilha.
  Mesmos 50 testes; asserts 155 -> 155.
- pyflakes de tests/test_essenciais.py: 45 avisos antigos (imports sem uso),
  iguais aos de antes; nenhum novo.
PROVA:
$ python -m py_compile main.py modulos/login.py modulos/confirmacao.py modulos/envio_item.py modulos/planilha_arquivos.py modulos/fluxo_envio_producao.py modulos/analise_remota.py modulos/nomes_aprovados.py
[exit 0]
$ python -m pyflakes main.py modulos/confirmacao.py modulos/envio_item.py modulos/fluxo_envio_producao.py modulos/analise_remota.py modulos/nomes_aprovados.py tests/test_t27.py
[exit 0]  (tests/test_essenciais.py: 45 avisos antigos, ver acima)
$ python -m pytest tests/test_t27.py -v -m "not real"
============================= 20 passed in 0.96s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 42%]
........................................................................ [ 85%]
........................                                                 [100%]
168 passed, 4 deselected, 8 warnings in 6.59s
[exit 0]
$ git diff --check
[exit 0]
$ testes e asserts em test_essenciais.py: HEAD x agora
def test_ HEAD=50 agora=50 | assert HEAD=155 agora=155
$ git stash push -- modulos/confirmacao.py modulos/envio_item.py main.py
Saved working directory and index state WIP on f4-producao: 8216f96 T26: lista de alunos em dados/, nomes aprovados por humano, sugestao de codigo de tema; senha so no .env
$ python -m pytest tests/test_t27.py -q -m "not real"   (confirmacao/envio_item/main de 8216f96)
FAILED tests/test_t27.py::test_processando_ate_o_fim_conta_como_recebido - mo...
FAILED tests/test_t27.py::test_main_le_codigos_com_repetidos - AssertionError...
FAILED tests/test_t27.py::test_envio_item_nao_clica_com_codigo_repetido_no_combo
3 failed, 17 passed in 1.08s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (1725fbf1422644c532fd4ca6273a87bb695dc453)
$ python -m pytest tests/test_t27.py -q -m "not real"   (T27)
20 passed in 1.07s

## T28 - F4: rodar direto nas redações reais (--pasta) e aprovar código por pasta [x]
- Execuções do Antônio (22/10, 10:58–11:00, após T27):
  - `python main.py --analise-remota` -> 109 temas gravados, backup criado,
    código repetido ['0000']. OK (T27 funcionando no site real).
  - `python main.py` e `--envio-real --limite-alunos 1 --limite-redacoes 1` ->
    "Nada para enviar": o script leu `redacoes_pendentes/`, que só tem as 11
    cópias de TESTE ("Usuario Testes Ignorar", que não está na lista de
    alunos). As 130 redações reais estão em `Redações plataforma/`. Não é bug
    do envio; faltava apontar para a pasta certa.
  - O aviso "Coluna 'Senha' ... ignorada" saía 2 vezes (print + UserWarning).
- Combo atualizado (22/10): dos 4 temas reais, só "filiação" existe no site
  (código 100). "aporofobia", "discriminação no trabalho" e "tecnologia e
  saúde mental" NÃO estão entre os 109 temas da conta de teste -> essas
  redações não têm como ser enviadas até o tema existir no site (decisão do
  Antônio / da plataforma).
- Mudanças:
  - `--pasta "<pasta>"`: lê as redações de qualquer pasta (sem copiar).
  - `dados/pastas_aprovadas.csv` (`;`, no .gitignore):
    pasta;codigo;tema;aprovado;semelhanca. O dry-run acrescenta as pastas sem
    código com o tema mais parecido; o Antônio confere (pode digitar outro
    código) e escreve `sim`. Pasta aprovada vale como "<codigo> - <pasta>"
    só para extrair o código; o arquivo continua no mesmo lugar. Sem renomear.
  - Avisos aparecem uma vez só.
  - `dados/*.bak.csv` no .gitignore; `dados/temas_site.csv` atualizado (109).
PROVA:
$ python -m py_compile main.py modulos/planilha_arquivos.py modulos/sugestao_temas.py modulos/config.py
[exit 0]
$ python -m pyflakes main.py modulos/sugestao_temas.py modulos/config.py tests/test_t28.py tests/test_fluxo_envio_producao.py
[exit 0]
$ python -m pytest tests/test_t28.py -v -m "not real"
tests/test_t28.py::test_pasta_sem_codigo_nao_entra_sem_aprovacao PASSED  [ 16%]
tests/test_t28.py::test_pasta_aprovada_entra_com_o_codigo_e_mantem_o_nome_real PASSED [ 33%]
tests/test_t28.py::test_aprovacao_nao_sobrescreve_pasta_que_ja_tem_codigo PASSED [ 50%]
tests/test_t28.py::test_sugestoes_de_pasta_gravadas_e_aprovacao_lida PASSED [ 66%]
tests/test_t28.py::test_main_pasta_inexistente_da_erro_claro PASSED      [ 83%]
tests/test_t28.py::test_main_dry_run_com_pasta_e_pasta_aprovada PASSED   [100%]
============================== 6 passed in 0.71s ==============================
[exit 0]
$ python -m pytest -m "not real" -q
........................................................................ [ 41%]
........................................................................ [ 82%]
..............................                                           [100%]
174 passed, 4 deselected, 8 warnings in 6.36s
[exit 0]
$ git diff --check
[exit 0]
$ git stash push -- main.py modulos/planilha_arquivos.py
Saved working directory and index state WIP on f4-producao: 85aeb5c T27: analise remota, identidade tolerante, Processando = recebido, folha em branco, relatorio do envio; corrige bug 001 (0000 repetido no combo)
$ python -m pytest tests/test_t28.py -q -m "not real"   (main/planilha_arquivos de 85aeb5c)
FAILED tests/test_t28.py::test_pasta_aprovada_entra_com_o_codigo_e_mantem_o_nome_real
FAILED tests/test_t28.py::test_aprovacao_nao_sobrescreve_pasta_que_ja_tem_codigo
FAILED tests/test_t28.py::test_main_pasta_inexistente_da_erro_claro - SystemE...
FAILED tests/test_t28.py::test_main_dry_run_com_pasta_e_pasta_aprovada - Syst...
4 failed, 2 passed in 1.11s
[exit 1]
$ git stash pop
Dropped refs/stash@{0} (0807e6104cbcb8bf529e9748f4f10a3988b94d9f)
$ (mesmo comando, T28)
6 passed in 0.72s

- Ajuste pós-commit cd00f9a (achado rodando o dry-run real, offline):
  `python main.py --pasta "Redações plataforma"` não gerou sugestões de NOME,
  porque com a pasta ainda sem código todo item fica SEM_CODIGO e as
  sugestões só olhavam FUZZY/SEM_ALUNO/AMBIGUO. Agora sugere para todo nome
  que não é o nome exato de um aluno, em qualquer estado.
  - Prova: com nomes_aprovados.py antigo (stash) o teste
    `test_sugestao_de_nome_sai_mesmo_com_pasta_sem_codigo` FALHA; com o novo, passa.
  - `python -m pytest -m "not real" -q` -> 175 passed, 4 deselected.
  - Dry-run real (sem site): 4 pastas em dados/pastas_aprovadas.csv e
    64 sugestões em dados/nomes_aprovados.csv (37 nome parcial único,
    27 parecidos). Fila real ainda 0: falta o Antônio aprovar.

---

## T29 - F4: revisão no terminal (--revisar) e análise remota na conta de um aluno [x]

Pedido do Antônio (22/10): revisar aluno por aluno pelo terminal em vez de
editar CSV; os 3 temas "que não existem" talvez existam com outro nome.

- `python main.py --pasta "Redações plataforma" --revisar` (nada é enviado):
  - Parte 1, pastas sem código: mostra os 5 temas mais parecidos de
    dados/temas_site.csv. Enter aceita só se for provável (>= 85%); digitar o
    código aprova; texto busca outro tema; `p` pula; `q` sai. Código fora do
    CSV ou repetido no combo (0000) é recusado. Grava `sim` em
    dados/pastas_aprovadas.csv (a pasta não é renomeada).
  - Parte 2, nomes: um nome por vez, agrupado (o mesmo "Alice Lalato" nas 4
    pastas é uma pergunta só). Enter aceita quando há UMA sugestão; número
    escolhe; texto busca o aluno; `p` pula; `q` sai. Confirmado -> o arquivo é
    RENOMEADO para o nome exato do aluno (pedido do Antônio), com log em
    relatorios/renomeacoes_<data_hora>.csv.
  - Não renomeia: folha em branco; arquivo com ENVIADO/ENVIANDO/JA_ENVIADO/
    REVISAO_MANUAL no banco (a chave do progresso é pasta/arquivo: renomear
    depois de enviar abriria reenvio); quando já existe arquivo com o nome do
    aluno na mesma pasta (duas redações do mesmo aluno: decidir à mão).
  - Sem terminal/Ctrl+C -> sai salvando o que já foi feito.
- `--desfazer-renomeacao relatorios/renomeacoes_<data>.csv --pasta ...` volta
  os nomes (do último para o primeiro).
- `--analise-remota --conta-aluno EMAIL`: lê o combo na conta de um aluno da
  lista (senha ESQUEMA_SENHA_PADRAO do .env; identidade conferida com o nome
  da lista). Motivo: no combo da conta de TESTE (109 temas) não há aporofobia
  nem discriminação no trabalho; o combo do aluno pode ter outros temas.
  Ao fim mostra os códigos novos e os que sumiram em relação ao CSV anterior.
- Observação "codigo ausente ou invalido" em arquivo sem aluno e pasta sem
  código passou a ser "aluno nao identificado" (a antiga confundia).

PROVA:
```
$ python -m pytest tests/test_t29.py -q
18 passed
$ python -m pytest -m "not real" -q
193 passed, 4 deselected
```
- Simulação numa CÓPIA do projeto (pasta temporária) com as 130 redações
  reais: aprovou 100 para a filiação com Enter, recusou Enter nas FRACAS,
  renomeou Alice Lalato (4 pastas) e Ana Lalara Larili (3); a busca
  "aporofobia" não achou nada no CSV atual (conta de teste). Arquivos reais
  não foram tocados.

- Ajuste pós-uso real (Antônio, 22/10): a Parte 1 confundia (porcentagens).
  Agora: "Provavelmente e o tema 100: ..." (Enter confirma) ou "Nenhum tema do
  site tem o nome bem parecido"; sem %; palavra digitada procura temas que
  contêm a palavra (sem acento, ex.: "rua"); `t` lista todos os temas.
  - Antônio: todos os alunos veem os MESMOS temas (padrão da plataforma).
    A página pública do site não lista temas (conferido no navegador, sem
    login). Logo, o combo lido (109) é a lista; os 3 temas existem com outro
    nome. Candidatos por sentido, para o Antônio decidir: aporofobia -> 102
    (arquitetura hostil, pessoas em situação de rua) / 90 / 48; discriminação
    no trabalho -> 64; tecnologia e saúde mental -> 75 (ou 85).
  - REGRA do Antônio (22/10): nunca enviar redação nas contas dos alunos de
    verdade. Claude não envia, não digita ENVIAR e não loga em conta de aluno.
  - `python -m pytest -m "not real" -q` -> 195 passed, 4 deselected.

---

## F3 concluída quando: T19 [x] + T20 [x] com provas coladas.
- ✅ F3 concluída em 21/10/2026 (T19 e T20 com provas acima).

## Pendências de decisão (não implementar sem resposta do Antônio)
- D1: a lista /minhas-redacoes da conta de teste está vazia ou mostra as 2
  redações enviadas manualmente em 30/09? (muda o esperado de duplicidade no T19)
- D2: sinal de "upload aceito" (só resolvido em T17/T18 com observação real).
- D3: módulos NOVOS (progresso.py, relatorios.py, logging_config.py, tabelas.py,
  fluxo_dryrun.py, fluxo_analise_remota.py) ficam para depois da F3? (padrão: sim)
