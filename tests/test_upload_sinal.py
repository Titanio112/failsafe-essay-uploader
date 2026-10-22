"""
T17: Descobrir o sinal real de 'upload aceito' — apenas observação.

Fluxo:
1. Abrir navegador visível (slow_mo=500)
2. Login com conta de teste (ESQUEMA_EMAIL_TESTE / ESQUEMA_SENHA_TESTE)
3. Confirmar identidade
4. Navegar para /wordings/new
5. Selecionar tema confirmado (código '0' - disponível na conta de teste)
6. Selecionar critério ENEM (value='1')
7. Anexar 1 JPG de testes/redacoes_teste/0 - Narração/
8. Observar mudanças no DOM, console e rede (aguardar alguns segundos)
9. Registrar evidência sanitizada em logs/
10. Logout e fechar navegador em finally

PROIBIDO: clicar em 'Enviar resposta', digitar 'ENVIAR TESTE', submeter formulário.
"""
import os
import json
import time
from pathlib import Path
from datetime import datetime

import pytest
from playwright.sync_api import sync_playwright, Page, ConsoleMessage, Response

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv()

EMAIL_TESTE = os.getenv("ESQUEMA_EMAIL_TESTE")
SENHA_TESTE = os.getenv("ESQUEMA_SENHA_TESTE")

# Pasta de logs
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Arquivo de teste JPG (primeiro da pasta 0)
JPGS_DIR = Path(__file__).parent.parent / "testes" / "redacoes_teste" / "0 - Narração"  # T40
JPGS = sorted(JPGS_DIR.glob("*.jpg"))
assert JPGS, "Nenhum JPG encontrado em testes/redacoes_teste/0 - Narração/"
ARQUIVO_TESTE = JPGS[0]

# Seletores CONFIRMADOS (AGENTS.md)
SELETORES = {
    "login_email": 'input[name="user[email]"]',
    "login_senha": 'input[name="user[password]"]',
    "login_entrar": 'input[name="commit"][value="Entrar"]',
    "identidade_dropdown": '.navbar-right .dropdown-toggle',
    "form_url": "/wordings/new",
    "tema_select": 'select[name="wording[wording_proposal_id]"]',
    "tema_label": 'get_by_label("Informe o tema da redação")',
    "criterio_select": 'select[name="wording[folder_id]"]',
    "anexo_input": 'input[name="wording[pages_attributes][0][file]"]',
    "btn_enviar": 'input[name="commit"][value="Enviar resposta"]',  # NÃO CLICAR
}
@pytest.mark.real
def test_upload_sinal_observacao():
    """Observa o que acontece no DOM/console/rede após anexar JPG."""
    evidencias = {
        "timestamp_inicio": datetime.now().isoformat(),
        "arquivo_testado": str(ARQUIVO_TESTE),
        "tamanho_bytes": ARQUIVO_TESTE.stat().st_size,
        "console_logs": [],
        "network_responses": [],
        "dom_snapshots": [],
        "erros": [],
    }

    def on_console(msg: ConsoleMessage):
        evidencias["console_logs"].append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
            "timestamp": time.time(),
        })

    def on_response(response: Response):
        url = response.url
        if any(kw in url.lower() for kw in ["upload", "file", "page", "attachment", "wording"]):
            evidencias["network_responses"].append({
                "url": url,
                "method": response.request.method,
                "status": response.status,
                "headers": dict(response.headers),
                "timestamp": time.time(),
            })

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()

        page.on("console", on_console)
        page.on("response", on_response)

        try:
            page.goto("https://www.esquemaredacao.com.br/auth/users/sign_in", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            page.fill(SELETORES["login_email"], EMAIL_TESTE)
            page.fill(SELETORES["login_senha"], SENHA_TESTE)
            page.click(SELETORES["login_entrar"])
            page.wait_for_load_state("networkidle")
            # Navegar para /minhas-redacoes após login (conforme login.py)
            page.goto("https://www.esquemaredacao.com.br/minhas-redacoes", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            try:
                page.wait_for_selector(SELETORES["identidade_dropdown"], timeout=5000)
                page.click(SELETORES["identidade_dropdown"])
                page.wait_for_timeout(500)
            except Exception as e:
                evidencias["erros"].append(f"Identidade dropdown: {e}")

            page.goto("https://www.esquemaredacao.com.br/wordings/new", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector(SELETORES["tema_select"], timeout=10000)

            evidencias["dom_snapshots"].append({
                "momento": "antes_anexo",
                "html": page.content(),
                "url": page.url,
                "timestamp": time.time(),
            })

            page.select_option(SELETORES["tema_select"], value="68")
            page.wait_for_timeout(500)

            page.select_option(SELETORES["criterio_select"], value="1")
            page.wait_for_timeout(500)

            page.set_input_files(SELETORES["anexo_input"], str(ARQUIVO_TESTE))

            for i in range(10):
                page.wait_for_timeout(1000)
                evidencias["dom_snapshots"].append({
                    "momento": f"pos_anexo_{i+1}s",
                    "html": page.content(),
                    "url": page.url,
                    "timestamp": time.time(),
                })

            btn = page.locator(SELETORES["btn_enviar"])
            evidencias["btn_enviar_estado"] = {
                "disabled": btn.get_attribute("disabled"),
                "class": btn.get_attribute("class"),
                "value": btn.get_attribute("value"),
            }

            upload_indicators = page.locator(".progress .bar").all()
            evidencias["upload_indicators_encontrados"] = len(upload_indicators)
            for idx, el in enumerate(upload_indicators):
                try:
                    evidencias[f"indicator_{idx}"] = {
                        "tag": el.evaluate("el => el.tagName"),
                        "class": el.get_attribute("class"),
                        "text": el.text_content()[:200] if el.text_content() else "",
                        "visible": el.is_visible(),
                    }
                except Exception:
                    pass

        except Exception as e:
            evidencias["erros"].append(f"Erro durante teste: {type(e).__name__}: {e}")
        finally:
            context.close()
            browser.close()

            evidencias["timestamp_fim"] = datetime.now().isoformat()

            evidencias_path = LOGS_DIR / f"test_upload_sinal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(evidencias_path, "w", encoding="utf-8") as f:
                json.dump(evidencias, f, ensure_ascii=False, indent=2)

            print(f"\n>>> EVIDÊNCIA SALVA EM: {evidencias_path}")
            print(f">>> Console logs capturados: {len(evidencias['console_logs'])}")
            print(f">>> Network responses capturadas: {len(evidencias['network_responses'])}")
            print(f">>> DOM snapshots: {len(evidencias['dom_snapshots'])}")
            print(f">>> Botão 'Enviar resposta' estado: {evidencias.get('btn_enviar_estado', 'N/A')}")
            print(f">>> Indicadores de upload encontrados: {evidencias.get('upload_indicators_encontrados', 0)}")

            assert len(evidencias["dom_snapshots"]) >= 2, "Deve ter snapshots antes e depois do anexo"
            assert ARQUIVO_TESTE.exists(), "Arquivo de teste deve existir"
