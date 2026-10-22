"""
T18: Validar implementação de aguardar_upload_aceito() com sinal real.

Fluxo:
1. Abrir navegador visível (slow_mo=500)
2. Login com conta de teste (ESQUEMA_EMAIL_TESTE / ESQUEMA_SENHA_TESTE)
3. Confirmar identidade (via /minhas-redacoes + dropdown)
4. Navegar para /wordings/new
5. Selecionar tema confirmado (código '0' - disponível na conta de teste)
6. Selecionar critério ENEM (value='1')
7. Anexar 1 JPG de testes/redacoes_teste/0/
8. CHAMAR A FUNÇÃO OFICIAL aguardar_upload_aceito(page)
9. AFIRMAR que retorna True (sinal detectado)
10. Logout e fechar navegador em finally

PROIBIDO: clicar em 'Enviar resposta', digitar 'ENVIAR TESTE', submeter formulário.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from playwright.sync_api import sync_playwright, Page

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv()

EMAIL_TESTE = os.getenv("ESQUEMA_EMAIL_TESTE")
SENHA_TESTE = os.getenv("ESQUEMA_SENHA_TESTE")

# Arquivo de teste JPG (primeiro da pasta 0)
JPGS_DIR = Path(__file__).parent.parent / "testes" / "redacoes_teste" / "0"
JPGS = sorted(JPGS_DIR.glob("*.jpg"))
assert JPGS, "Nenhum JPG encontrado em testes/redacoes_teste/0/"
ARQUIVO_TESTE = JPGS[0]
print(f"[DEBUG] Arquivo de teste: {ARQUIVO_TESTE}")

# Seletores CONFIRMADOS (AGENTS.md)
SELETORES = {
    "login_email": 'input[name="user[email]"]',
    "login_senha": 'input[name="user[password]"]',
    "login_entrar": 'input[name="commit"][value="Entrar"]',
    "identidade_dropdown": ".navbar-right .dropdown-toggle",
    "tema_select": 'select[name="wording[wording_proposal_id]"]',
    "criterio_select": 'select[name="wording[folder_id]"]',
    "anexo_input": 'input[name="wording[pages_attributes][0][file]"]',
    "botao_enviar": 'input[name="commit"][value="Enviar resposta"]',
}


@pytest.mark.real
def test_upload_aceito_t18():
    """Valida que aguardar_upload_aceito() detecta o sinal real de upload aceito."""
    from modulos.site.formulario_envio import aguardar_upload_aceito

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 1. Login
            print("[DEBUG] 1. Login...")
            page.goto("https://www.esquemaredacao.com.br/auth/users/sign_in", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            page.fill(SELETORES["login_email"], EMAIL_TESTE)
            page.fill(SELETORES["login_senha"], SENHA_TESTE)
            page.click(SELETORES["login_entrar"])
            page.wait_for_load_state("networkidle")
            print(f"[DEBUG]   Login OK, URL: {page.url}")

            # 2. Confirmar identidade - navegar para minhas-redacoes primeiro
            print("[DEBUG] 2. minhas-redacoes...")
            page.goto("https://www.esquemaredacao.com.br/minhas-redacoes", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            print(f"[DEBUG]   minhas-redacoes OK, URL: {page.url}")

            # Dropdown de identidade
            print("[DEBUG] 3. Dropdown identidade...")
            page.wait_for_selector(SELETORES["identidade_dropdown"], timeout=5000)
            page.click(SELETORES["identidade_dropdown"])
            page.wait_for_timeout(500)
            print("[DEBUG]   Dropdown clicked")

            # 3. Navegar para formulário
            print("[DEBUG] 4. Formulário...")
            page.goto("https://www.esquemaredacao.com.br/wordings/new", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector(SELETORES["tema_select"], timeout=10000)
            print(f"[DEBUG]   Formulário OK, URL: {page.url}")

            # 4. Selecionar tema (código '0' -> value="68" para "0- Narração")
            print("[DEBUG] 5. Selecionar tema 0 (value=68)...")
            page.select_option(SELETORES["tema_select"], value="68")
            print("[DEBUG]   Tema OK")

            # 5. Selecionar critério ENEM (value='1')
            print("[DEBUG] 6. Selecionar critério ENEM...")
            page.select_option(SELETORES["criterio_select"], value="1")
            print("[DEBUG]   Critério OK")

            # 6. Anexar JPG
            print("[DEBUG] 7. Anexar JPG...")
            page.set_input_files(SELETORES["anexo_input"], str(ARQUIVO_TESTE))
            print("[DEBUG]   Anexo OK")

            # 7. CHAMAR A FUNÇÃO OFICIAL - aguardar upload aceito
            print("[DEBUG] 8. Chamar aguardar_upload_aceito...")
            resultado = aguardar_upload_aceito(page, timeout_segundos=30)
            print(f"[DEBUG]   Resultado: {resultado}")

            # 8. AFIRMAR que retorna True
            assert resultado is True, f"aguardar_upload_aceito() retornou {resultado}, esperado True (sinal de upload aceito detectado)"

        finally:
            # Fechar contexto e navegador (sem logout — rota 404)
            context.close()
            browser.close()


if __name__ == "__main__":
    test_upload_aceito_t18()