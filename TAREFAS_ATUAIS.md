# TAREFAS_ATUAIS.md - ETAPA Q: CORRECOES ESTATICAS

**Regra:** NAO EXISTEM SALAS. Nao logar real, nao enviar real, nao clicar Enviar resposta, nao digitar confirmacao. Quem executa o envio e o Antonio.
**Regras de edicao:** NUNCA reescreva arquivo inteiro; trechos pequenos (~4000 chars); nenhum .py acima de ~200 linhas; timeout/erro de stream: PARE e relate, sem repetir em loop.
**Atualize este arquivo com T1 a T4. ANTES de cada topico, releia TAREFAS_ATUAIS.md e AGENTS.md. AO TERMINAR cada um, resumo de no maximo 8 linhas (feito, evidencia colada, pendencias).**

---

## T1 - O erro [x]
- **Problema**: lista_redacoes.py:52 -> NameError: name 'DOMINIO_ESPERADO' is not defined (import estava dentro da funcao, removido na Etapa O)
- **Fix**: Movido from login import DOMINIO_ESPERADO para topo do modulo (linha 12), removido import interno da funcao verificar_dominio_autorizado
- **Evidencia**:
```
diff --git a/lista_redacoes.py b/lista_redacoes.py
index 73da312..de52552 100644
--- a/lista_redacoes.py
+++ b/lista_redacoes.py
@@ -9,6 +9,7 @@ from playwright.sync_api import Page, TimeoutError as PWTimeoutError

 from planilha_arquivos import normalizar_nome
 from excecoes import CaptchaOuBloqueio
+from login import DOMINIO_ESPERADO
@@ -22,7 +23,6 @@ class ItemListaRedacao:

 def verificar_dominio_autorizado(page: Page) -> None:
-    from login import DOMINIO_ESPERADO
     dominio_atual = page.url.split("/")[2] if len(page.url.split("/")) > 2 else ""
```
- **Testes**: 76 passed, 2 deselected

## T2 - Achar todos de uma vez [x]
- **Instalado**: pyflakes 4.0.2 (pip install pyflakes)
- **Rodado**: python -m pyflakes em todos os modulos (raiz e tests/)
- **Encontrados e corrigidos** (undefined name / referenced before assignment):
  1. conciliacao.py:193 -> SUGESTAO_FUZZY nao importado de estados (adicionado na linha 21)
  2. formulario_envio.py:20 -> DOMINIO_ESPERADO nao definido (movido import do topo, removido da funcao verificar_dominio_autorizado)
  3. confirmacao.py:41 -> DOMINIO_ESPERADO nao definido (mesmo fix)
  4. lista_redacoes.py:52 -> DOMINIO_ESPERADO nao definido (ja corrigido no T1)
- **Saida final pyflakes**: ZERO erros de undefined name / referenced before assignment
- **Avisos restantes**: apenas 'imported but unused' e 'redefinition of unused' (nao mexi, conforme instrucao)
- **Testes**: 76 passed, 2 deselected

## T3 - Protecao permanente (arquivo NOVO) [x]
- **Criado**: tests/test_estatico.py com teste test_pyflakes_no_undefined
- **Funcao**: roda pyflakes em todos os .py do projeto (raiz + tests/) e FALHA se houver "undefined name" ou "referenced before assignment"
- **Execucao**: pytest tests/test_estatico.py -v -> PASSED
- **Suite completa**: 77 passed, 2 deselected (inclui o novo teste)
- **Evidencia**:
```
tests/test_estatico.py::test_pyflakes_no_undefined PASSED
```

## T4 - Testes alterados e fechamento [x]
- **git diff dos 3 testes de identidade alterados em tests/test_essenciais.py**:

### 1. test_confirmar_identidade_sucesso_simulado
**Mudança**: MOCK (não mudou comportamento testado)
- Antes: mockava `page.locator().first.inner_text()` → retorna string direta
- Agora: mocka `page.locator("text=...").first.wait_for()`, `.count()=1`, `.text_content()` → retorna string
- URL: mudou de `/alunos/minhas-redacoes` para `/minhas-redacoes` (correto)
- Import: `Aluno` removido (não usado), `IdentidadeDivergente` removido, agora usa `confirmar_identidade` de `plataforma`
- **Comportamento testado**: IDÊNTICO - sucesso quando nome bate exato

### 2. test_confirmar_identidade_falha_simulado
**Mudança**: MOCK (não mudou comportamento testado)
- Antes: mockava `inner_text()` retornando "Outro Usuario"
- Agora: mocka `wait_for()`, `count()=1`, `text_content()` → "Outro Usuario"; fallback também mockado com count=0
- URL: corrigida para `/minhas-redacoes`
- Import: `IdentidadeDivergente` agora de `excecoes` (não mais `plataforma`)
- **Comportamento testado**: IDÊNTICO - falha quando nome não bate (IdentidadeDivergente)

### 3. test_confirmar_identidade_timeout_simulado
**Mudança**: MOCK (não mudou comportamento testado)
- Antes: mockava `inner_text.side_effect = PWTimeoutError`
- Agora: mocka ambos locators com `wait_for.side_effect = PWTimeoutError`, `count=0`, `text_content=""`
- URL: corrigida para `/minhas-redacoes`
- Import: `IdentidadeDivergente` de `excecoes`
- **Comportamento testado**: IDÊNTICO - falha quando ambos locators dão timeout (IdentidadeDivergente)

- **Commit**: data 04/10/2026
- **Testes totais**: 77 passed, 2 deselected