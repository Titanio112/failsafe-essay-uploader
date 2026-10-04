# TAREFAS_ATUAIS.md - ETAPA N: CORRIGIR O LOGIN

**Regra:** NAO EXISTEM SALAS. Nao logar real, nao enviar real, nao clicar Enviar resposta, nao digitar confirmacao. Quem executa o envio e o Antonio.
**Regras de edicao:** NUNCA reescreva arquivo inteiro; trechos pequenos (~4000 chars); nenhum .py acima de ~300 linhas; timeout/erro de stream: PARE e relate, sem repetir em loop.
**Atualize este arquivo com T1 a T6. ANTES de cada topico, releia TAREFAS_ATUAIS.md e AGENTS.md. AO TERMINAR cada um, resumo de no maximo 8 linhas (feito, evidencia colada, pendencias).**

---

## T1 - Origem do bug [x]
- **Commit que introduziu o bug**: Modularizacao (linhas de checkpoint) - login.py criado a partir de plataforma.py
- **Codigo funcionando na Etapa E (commit 03f591a)**:
  ```python
  # Apos click no botao submit:
  page.wait_for_load_state("networkidle")
  verificar_dominio_autorizado(page)
  # Navegar para /minhas-redacoes apos login
  page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
  page.wait_for_load_state("networkidle")
  verificar_dominio_autorizado(page)
  return page
  ```
- **Bug introduzido no login.py**: linha 33 `page.wait_for_url("**/alunos/**", timeout=15000)` - o path `/alunos/` NAO existe no site. O destino pos-login confirmado e `/minhas-redacoes`.
- **Sim, foi a modularizacao** que moveu o login de plataforma.py para login.py e quebrou o criterio de sucesso.

## T2 - Corrigir o criterio de sucesso [x]
- O sucesso do login NAO pode depender da URL de destino. Depois de clicar em entrar: se a URL ainda contem "/sign_in" ou aparece mensagem de erro, LoginFalhou. Senao, navegue para /minhas-redacoes e confirme que NAO redirecionou para sign_in e que existe o saldo ("Voce tem N credito(s)") ou o menu do usuario. Qualquer outra coisa: LoginFalhou com URL atual e texto de erro visivel na mensagem (nunca senha, e-mail completo, token ou cookie).
- Sem retry automatico; 3 falhas seguidas continuam abortando a analise.

**Evidencia:** login.py linhas 21-56 corrigido; testes em test_login_criterio.py passam (7/7).

## T3 - Testes offline (pagina simulada) [x]
- **Arquivo novo**: `tests/test_login_criterio.py` (7 testes)
- **Cobertura**:
  - Destino "/" com saldo visivel -> sucesso
  - Destino "/minhas-redacoes" -> sucesso
  - Destino "/alunos/x" com saldo -> sucesso
  - Permanece em sign_in com erro -> LoginFalhou
  - /minhas-redacoes redireciona para sign_in -> LoginFalhou
  - Sem saldo e sem menu do usuario -> LoginFalhou
  - Apenas menu do usuario (sem saldo) -> sucesso
- **pytest -q completo**: 54 passed, 2 deselected (7 novos + 47 anteriores)
- NAO editei `tests/test_essenciais.py`

## T4 - Corrigir documentacao e codigo [x]
- **Ocorrencias de "/alunos/" em .py** (todas corrigidas para /minhas-redacoes ou /nova-redacao):
  - confirmacao.py:41 -> corrigido
  - formulario_envio.py:20 -> corrigido  
  - lista_redacoes.py:33 -> corrigido
- **AGENTS.md**: sem ocorrencias de "/alunos/" (ja limpo)
- **PROJECT_MEMORY.md**: "Passo (c) EM ANDAMENTO" -> "Passo (c) CONCLUIDO"; removido "PASSO (c)" dos proximos passos
- Mapeamento do site: CONCLUIDO (seletores validados: ler_lista_redacoes, ler_combo_temas, confirmar_identidade, selecionar_tema_por_codigo)

## T5 - Status da Etapa M [x]
- **T3 (matriz)**: NÃO foi feito na Etapa M — não há registro no PROJECT_MEMORY.md
- **T4 (mutação)**: NÃO foi feito na Etapa M — não há registro no PROJECT_MEMORY.md
- **T5 (testes novos)**: NÃO foi feito na Etapa M — não há registro no PROJECT_MEMORY.md
- **Evidência**: PROJECT_MEMORY.md só registra até ETAPA L (modularização completa, 47 testes). A contagem atual de testes offline é 54 (47 originais + 7 novos de test_login_criterio.py). Não houve T3/T4/T5 da Etapa M implementados.

## T6 - Fechar [ ]
- Commit com data 04/10/2026. PARE e relate: git log, pytest, TAREFAS_ATUAIS.md, e o comando exato para o Antonio rodar o teste real com --tb=short.
