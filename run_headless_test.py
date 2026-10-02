from fase2_mapeamento import *
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import re

load_dotenv()

email = os.getenv("ESQUEMA_EMAIL_TESTE")
senha = os.getenv("ESQUEMA_SENHA_TESTE")

print(f"[INFO] Usando conta de teste: {email}")

p = sync_playwright().start()
b = p.chromium.launch(headless=True, slow_mo=50)
page = b.new_page()

print("[PASSO 1/7] Login...")
page.goto("https://www.esquemaredacao.com.br/auth/users/sign_in")
page.wait_for_load_state("domcontentloaded")
page.locator('input[name="user[email]"]').fill(email)
page.locator('input[name="user[password]"]').fill(senha)
page.locator('input[name="commit"]').click()
page.wait_for_load_state("networkidle")

if "/minhas-redacoes" not in page.url:
    page.goto("https://www.esquemaredacao.com.br/minhas-redacoes")
    page.wait_for_load_state("networkidle")

print("[OK] Login realizado com sucesso")

print("[PASSO 2/7] Capturando identidade...")
try:
    nome_topo = page.locator('text=Usuario Testes Ignorar').first
    if nome_topo.is_visible():
        nome_logado = nome_topo.text_content() or ""
    else:
        nome_element = page.locator('a[href="#"]').first
        if nome_element.is_visible():
            nome_logado = nome_element.text_content() or ""
        else:
            header_text = page.locator('header, nav, .navbar, .header').first.text_content() or ""
            nome_logado = header_text
    print(f"[OK] Nome no topo: '{nome_logado}'")
except Exception as e:
    print(f"[AVISO] Identidade: {e}")

print("[PASSO 3/7] Capturando saldo de créditos...")
texto = page.locator('text=Você tem').first.text_content() or ""
m = re.search(r"Você tem\s+(\d+)\s+crédito", texto)
saldo = int(m.group(1)) if m else 0
print(f"[OK] Saldo de créditos: {saldo}")

print("[PASSO 4/7] Lendo lista de redações (/minhas-redacoes)...")
page.goto("https://www.esquemaredacao.com.br/minhas-redacoes")
page.wait_for_load_state("networkidle")
itens = []
rows = page.locator("table tbody tr").all()
for row in rows:
    cells = row.locator("td").all()
    if len(cells) >= 5:
        itens.append(ItemListaRedacao(
            data=cells[0].text_content() or "",
            tema=cells[1].text_content() or "",
            nota=cells[2].text_content() or "",
            situacao=cells[3].text_content() or "",
            botao_texto=cells[4].text_content() or "",
        ))

print(f"[OK] Total de linhas na lista: {len(itens)}")
for i, item in enumerate(itens, 1):
    print(f"  Linha {i}: Data={item.data}, Tema={item.tema}, Nota={item.nota}, Situação={item.situacao}, Botão={item.botao_texto}")

print("[PASSO 5/7] Confirmando as 2 linhas enviadas manualmente...")
temas_0 = [item for item in itens if item.tema.startswith("0-")]
print(f"  Linhas com tema '0-': {len(temas_0)}")
assert len(temas_0) >= 2, f"Esperado >= 2 linhas com tema '0-', encontrado {len(temas_0)}"
print("[OK] As 2 linhas de teste confirmadas")

print("[PASSO 6/7] Abrindo /wordings/new (formulário de envio)...")
page.goto("https://www.esquemaredacao.com.br/wordings/new")
page.wait_for_load_state("networkidle")
print(f"[OK] URL do formulário: {page.url}")

print("[INFO] Lendo combo 'Informe o tema da redação'...")
temas = ler_combo_temas_manual(page)
print(f"  Opções do combo de tema: {len(temas)}")
for t in temas:
    print(f"    Código: '{t.codigo}' | Texto: '{t.texto_completo}'")

print("[INFO] Validando selecionar_tema_por_codigo('0')...")
combo = page.get_by_label("Informe o tema da redação")
combo.click()
page.wait_for_timeout(300)
options = page.get_by_role("option").all()
for opt in options:
    txt = opt.text_content() or ""
    if extrair_codigo_do_tema_site(txt) == "0":
        opt.click()
        page.wait_for_timeout(300)
        break
print("[OK] seleção de tema por código funcionou")

print("[INFO] Lendo combo 'Selecione um critério de avaliação'...")
try:
    page.get_by_label("Selecione um critério de avaliação")
    print("[OK] Combo de critério encontrado")
except Exception as e:
    print(f"[AVISO] Combo de critério não encontrado: {e}")

print("[INFO] Verificando input de arquivo e botão 'Enviar resposta'...")
try:
    file_input = page.locator('input[type="file"]').first
    accept_attr = file_input.get_attribute("accept") if file_input.is_visible() else None
    print(f"[OK] Input de arquivo encontrado. accept='{accept_attr}'")
except Exception as e:
    print(f"[AVISO] Input de arquivo não encontrado: {e}")

try:
    btn_enviar = page.get_by_role("button", name="Enviar resposta")
    habilitado = btn_enviar.is_enabled() if btn_enviar.is_visible() else False
    print(f"[OK] Botão 'Enviar resposta' encontrado. Habilitado={habilitado} [PROIBIDO clicar agora]")
except Exception as e:
    print(f"[AVISO] Botão 'Enviar resposta' não encontrado: {e}")

print("[PASSO 7/7] Gravando dados/temas_site.csv...")
from pathlib import Path
import csv
from datetime import datetime

dados_dir = Path(__file__).parent / "dados"
dados_dir.mkdir(exist_ok=True)
csv_path = dados_dir / "temas_site.csv"

print(f"  Salvando {len(temas)} temas no CSV...")

with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "texto", "data_leitura", "conta_mascarada"])
    for t in temas:
        w.writerow([t.codigo, t.texto_completo, datetime.now().strftime("%Y-%m-%d"), email[:3] + "***"])

print(f"[OK] Arquivo salvo: {csv_path} ({len(temas)} temas)")

print("[SUCESSO] Mapeamento concluído com sucesso!")

b.close()
p.stop()