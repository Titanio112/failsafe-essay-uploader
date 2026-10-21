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

## T18B - F3: fail-closed após tentativa de envio [x]
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
