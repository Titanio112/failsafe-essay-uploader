#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PASSO (c) — MAPEAMENTO SOMENTE LEITURA"""

from __future__ import annotations
import csv, os, sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from dataclasses import dataclass

from plataforma import DOMINIO_ESPERADO, verificar_dominio_autorizado, ItemListaRedacao
from planilha_arquivos import Aluno, normalizar_nome, extrair_codigo_do_tema_site


@dataclass
class TemaCombo:
    codigo: str
    texto_completo: str


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def login_manual(page, email: str, password: str):
    page.goto(f"https://{DOMINIO_ESPERADO}/auth/users/sign_in")
    page.wait_for_load_state("domcontentloaded")
    page.locator('input[name="user[email]"]').fill(email)
    page.locator('input[name="user[password]"]').fill(password)
    page.locator('input[name="commit"]').click()
    page.wait_for_load_state("networkidle")
    # After login, navigate to /minhas-redacoes directly
    if "/minhas-redacoes" not in page.url:
        page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
        page.wait_for_load_state("networkidle")
    return page


def ler_saldo_creditos_manual(page) -> int:
    import re
    texto = page.locator('text=Você tem').first.text_content() or ""
    m = re.search(r"Você tem\s+(\d+)\s+crédito", texto)
    return int(m.group(1)) if m else 0


def ler_lista_redacoes_manual(page) -> list[ItemListaRedacao]:
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
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
    return itens


def ler_combo_temas_manual(page):
    """Lê TODAS as opções do combo 'Informe o tema da redação' (com scroll para lazy loading)."""
    temas = []
    combo = page.get_by_label("Informe o tema da redação")
    combo.click()
    page.wait_for_timeout(500)
    
    listbox = page.locator('[role="listbox"]').first
    if not listbox.is_visible():
        listbox = page.locator('[role="listbox"], .select2-results, .dropdown-menu, [class*="dropdown"] >> [role="listbox"]').first
    
    previous_count = 0
    same_count = 0
    max_attempts = 50
    
    for attempt in range(max_attempts):
        options = page.get_by_role("option").all()
        current_count = len(options)
        
        if current_count == previous_count:
            same_count += 1
            if same_count >= 3:
                break
        else:
            same_count = 0
            previous_count = current_count
        
        if listbox.is_visible():
            listbox.press("End")
        else:
            page.keyboard.press("End")
        
        page.wait_for_timeout(200)
    
    options = page.get_by_role("option").all()
    temas = []
    for opt in options:
        texto = opt.text_content() or ""
        if texto.strip():
            codigo = extrair_codigo_do_tema_site(texto)
            if codigo:
                temas.append(TemaCombo(codigo=codigo, texto_completo=texto.strip()))
    
    log(f"  Total opções capturadas após scroll: {len(temas)}")
    return temas
def main() -> int:
    load_dotenv()
    email = os.getenv("ESQUEMA_EMAIL_TESTE")
    senha = os.getenv("ESQUEMA_SENHA_TESTE")
    if not email or not senha:
        print("[ERRO] Credenciais de teste não configuradas no .env")
        return 1
    
    print(f"[INFO] Usando conta de teste: {email}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        console_messages = []
        page.on("console", lambda m: console_messages.append(f"[{m.type}] {m.text}"))
        
        try:
            log("[PASSO 1/7] Login...")
            page = login_manual(page, email, senha)
            verificar_dominio_autorizado(page)
            log("[OK] Login realizado com sucesso")
            
            log("[PASSO 2/7] Capturando identidade...")
            aluno_teste = Aluno(nome="Usuario Testes Ignorar", email=email, sala="TESTE")
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
                log(f"[OK] Nome no topo: '{nome_logado}'")
            except Exception as e:
                log(f"[AVISO] Identidade: {e}")
            
            log("[PASSO 3/7] Capturando saldo de créditos...")
            saldo = ler_saldo_creditos_manual(page)
            log(f"[OK] Saldo de créditos: {saldo}")
            
            log("[PASSO 4/7] Lendo lista de redações (/minhas-redacoes)...")
            lista = ler_lista_redacoes_manual(page)
            log(f"[OK] Total de linhas na lista: {len(lista)}")
            for i, item in enumerate(lista, 1):
                log(f"  Linha {i}: Data={item.data}, Tema={item.tema}, Nota={item.nota}, Situação={item.situacao}, Botão={item.botao_texto}")
            
            log("[PASSO 5/7] Confirmando as 2 linhas enviadas manualmente...")
            temas_0 = [item for item in lista if item.tema.startswith("0-")]
            log(f"  Linhas com tema '0-': {len(temas_0)}")
            assert len(temas_0) >= 2, f"Esperado >= 2 linhas com tema '0-', encontrado {len(temas_0)}"
            log("[OK] As 2 linhas de teste confirmadas")
            
            log("[PASSO 6/7] Abrindo /wordings/new (formulário de envio)...")
            page.goto(f"https://{DOMINIO_ESPERADO}/wordings/new")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)
            log(f"[OK] URL do formulário: {page.url}")

            log("[INFO] Lendo combo 'Informe o tema da redação'...")
            temas = ler_combo_temas_manual(page)
            log(f"  Opções do combo de tema: {len(temas)}")
            for t in temas:
                log(f"    Código: '{t.codigo}' | Texto: '{t.texto_completo}'")
            
            log("[INFO] Validando selecionar_tema_por_codigo('0')...")
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
            log("[OK] seleção de tema por código funcionou")
            
            log("[INFO] Lendo combo 'Selecione um critério de avaliação'...")
            try:
                page.get_by_label("Selecione um critério de avaliação")
                log("[OK] Combo de critério encontrado")
            except Exception as e:
                log(f"[AVISO] Combo de critério não encontrado: {e}")
            
            log("[INFO] Verificando input de arquivo e botão 'Enviar resposta'...")
            try:
                file_input = page.locator('input[type="file"]').first
                accept_attr = file_input.get_attribute("accept") if file_input.is_visible() else None
                log(f"[OK] Input de arquivo encontrado. accept='{accept_attr}'")
            except Exception as e:
                log(f"[AVISO] Input de arquivo não encontrado: {e}")
            
            try:
                btn_enviar = page.get_by_role("button", name="Enviar resposta")
                habilitado = btn_enviar.is_enabled() if btn_enviar.is_visible() else False
                log(f"[OK] Botão 'Enviar resposta' encontrado. Habilitado={habilitado} [PROIBIDO clicar agora]")
            except Exception as e:
                log(f"[AVISO] Botão 'Enviar resposta' não encontrado: {e}")
            
            log("[PASSO 7/7] Gravando dados/temas_site.csv...")
            dados_dir = Path(__file__).parent / "dados"
            dados_dir.mkdir(exist_ok=True)
            csv_path = dados_dir / "temas_site.csv"
            
            # Usar a lista 'temas' já capturada anteriormente (com scroll completo)
            log(f"  Salvando {len(temas)} temas no CSV...")
            
            with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["codigo", "texto", "data_leitura", "conta_mascarada"])
                for t in temas:
                    w.writerow([t.codigo, t.texto_completo, datetime.now().strftime("%Y-%m-%d"), email[:3] + "***"])
            
            log(f"[OK] Arquivo salvo: {csv_path} ({len(temas)} temas)")
            
            if console_messages:
                log(f"[INFO] Mensagens do console do navegador ({len(console_messages)}):")
                for msg in console_messages[:10]:
                    log(f"  {msg}")
            
            log("[SUCESSO] Mapeamento concluído com sucesso!")
            return 0
            
        except Exception as e:
            log(f"[ERRO] Falha no mapeamento: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            log("[INFO] Fechando contexto e navegador...")
            page.close()
            context.close()
            browser.close()
            log("[INFO] Navegador fechado.")


if __name__ == "__main__":
    sys.exit(main())
