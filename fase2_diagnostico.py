#!/usr/bin/env python3
"""
Fase 2 - Diagnóstico completo de login e navegação na plataforma.

Regras:
- headless=False, slow_mo=500
- Login com aluno de teste (primeiro da Sala B com JPG, EXATO_UNICO)
- Não anexar arquivo, não clicar no botão final de envio
- Gravar saída sanitizada em diagnosticos/saida_diagnostico.txt
"""

import os
import sys
import re
import time
from pathlib import Path
from dotenv import load_dotenv

from config import Config, obter_senha
from planilha_arquivos import carregar_alunos, normalizar_nome, descobrir_arquivos, conciliar
from playwright.sync_api import sync_playwright


def mascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return "N/A"
    return email[:3] + "..." + email.split("@")[-1]


def sanitizar_saida(texto: str, email: str) -> str:
    """Remove senha e mascara e-mail da saída."""
    if not texto:
        return texto
    # Mascarar email
    if email and "@" in email:
        texto = texto.replace(email, mascarar_email(email))
    return texto


def log_step(msg: str, out_file):
    """Log step to both console and file."""
    print(msg)
    with open(out_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def log_ok(msg: str, out_file):
    log_step(f"[OK] {msg}", out_file)


def log_erro(msg: str, out_file):
    log_step(f"[ERRO] {msg}", out_file)


def main():
    load_dotenv()
    
    # Verificar senha
    senha = os.environ.get("ESQUEMA_SENHA_PADRAO")
    if not senha or len(senha) == 0:
        print("ERRO: ESQUEMA_SENHA_PADRAO não definida ou vazia")
        sys.exit(1)
    print(f"Senha OK: {len(senha)} caracteres")
    
    # Carregar configuração
    cfg = Config()
    if not cfg.planilha:
        default_sheet = "Alunos para corrigir redacoes.xlsx"
        cfg.planilha = cfg.pasta_raiz / default_sheet
    
    if not cfg.planilha.exists():
        print(f"Erro: Planilha não encontrada em {cfg.planilha}")
        sys.exit(1)
    
    # Carregar alunos
    try:
        alunos = carregar_alunos(cfg)
    except Exception as e:
        print(f"Erro ao carregar alunos: {e}")
        sys.exit(1)
    
    # Encontrar Sala B ou 3B
    salas = sorted(list(set(a.sala for a in alunos if a.sala)))
    print(f"Salas encontradas: {', '.join(salas)}")
    
    sala_escolhida = None
    for s in salas:
        if s.strip().upper() in ["B", "3B"]:
            sala_escolhida = s
            break
    
    if not sala_escolhida:
        print("Erro: Sala B (ou 3B) não encontrada.")
        sys.exit(1)
    
    print(f"Sala selecionada: {sala_escolhida}")
    
    # Filtrar alunos da sala
    alunos_sala = [a for a in alunos if a.sala == sala_escolhida]
    alunos_sala.sort(key=lambda x: normalizar_nome(x.nome))
    
    # Conciliar arquivos
    arquivos_por_pasta = descobrir_arquivos(cfg)
    resultado = conciliar(alunos, arquivos_por_pasta)
    validos = resultado.fila_validada()
    
    # Encontrar primeiro aluno com EXATO_UNICO
    selected_aluno = None
    selected_items = []
    
    for aluno in alunos_sala:
        items = [i for i in validos if i.aluno and i.aluno.id == aluno.id and i.estado == "EXATO_UNICO"]
        if items:
            selected_aluno = aluno
            selected_items = items
            break
    
    if not selected_aluno:
        print("Erro: Nenhum aluno da sala B com correspondência exata e única e JPGs foi encontrado.")
        sys.exit(1)
    
    # Preparar arquivo de saída
    out_dir = Path("diagnosticos")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "saida_diagnostico.txt"
    
    # Limpar arquivo anterior
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("")
    
    email_env = selected_aluno.email
    nome_esperado = selected_aluno.nome
    
    log_step(f"=== FASE 2 - DIAGNÓSTICO COMPLETO ===", out_file)
    log_step(f"Aluno: {nome_esperado}", out_file)
    log_step(f"Email: {mascarar_email(email_env)}", out_file)
    log_step(f"Sala: {selected_aluno.sala}", out_file)
    log_step(f"Arquivos JPG: {[f'{i.pasta}/{i.arquivo}' for i in selected_items]}", out_file)
    log_step(f"", out_file)

    # Iniciar Playwright
    log_step(f"Iniciando Playwright...", out_file)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()

            # Passo 1: Acessar página de login
            log_step(f"[PASSO 1] Acessando página de login...", out_file)
            page.goto("https://www.esquemaredacao.com.br/auth/users/sign_in")
            log_ok(f"Página de login carregada: {page.url}", out_file)

            # Passo 2: Preencher email
            log_step(f"[PASSO 2] Preenchendo email...", out_file)
            page.fill('input[name="user[email]"]', email_env)
            log_ok(f"Email preenchido", out_file)

            # Passo 3: Preencher senha
            log_step(f"[PASSO 3] Preenchendo senha...", out_file)
            page.fill('input[name="user[password]"]', senha)
            log_ok(f"Senha preenchida", out_file)

            # Passo 4: Clicar no botão de login
            log_step(f"[PASSO 4] Clicando no botão de login...", out_file)
            page.click('input[name="commit"], button[type="submit"]')
            page.wait_for_load_state("networkidle")
            log_ok(f"Login submetido. URL atual: {page.url}", out_file)

            # Passo 5: Verificar se logou com sucesso
            log_step(f"[PASSO 5] Verificando login...", out_file)
            if "sign_in" in page.url:
                log_erro(f"Falha no login - ainda na página de sign_in", out_file)
                page.screenshot(path=str(out_dir / "pagina_login_falha.png"))
                log_step(f"Screenshot salvo: pagina_login_falha.png", out_file)
            else:
                log_ok(f"Login realizado com sucesso. URL: {page.url}", out_file)
                log_step(f"Título da página: {page.title()}", out_file)

                # Passo 6: Navegar para "Enviar redação"
                log_step(f"[PASSO 6] Procurando link 'Enviar redação'...", out_file)
                # Tentar vários seletores possíveis
                enviar_redacao_found = False
                for selector in [
                    'a:has-text("Enviar redação")',
                    'a:has-text("Enviar Redação")',
                    'a[href*="enviar"]',
                    'a[href*="redacao"]',
                    'button:has-text("Enviar redação")',
                    'button:has-text("Enviar Redação")',
                ]:
                    try:
                        page.wait_for_selector(selector, timeout=3000)
                        page.click(selector)
                        page.wait_for_load_state("networkidle")
                        log_ok(f"Clicou em 'Enviar redação' via {selector}. URL: {page.url}", out_file)
                        enviar_redacao_found = True
                        break
                    except:
                        continue
                
                if not enviar_redacao_found:
                    log_erro(f"Não encontrou link 'Enviar redação'. HTML salvo.", out_file)
                    html = page.content()
                    with open(out_dir / "pagina_pos_login.html", "w", encoding="utf-8") as f:
                        f.write(html)
                else:
                    # Passo 7: Selecionar "000 dissertação"
                    log_step(f"[PASSO 7] Selecionando '000 dissertação'...", out_file)
                    try:
                        page.wait_for_selector('select[name*="tipo"], select[id*="tipo"]', timeout=5000)
                        page.select_option('select[name*="tipo"], select[id*="tipo"]', label="000 dissertação")
                        log_ok(f"'000 dissertação' selecionado", out_file)
                    except Exception as e:
                        log_erro(f"Erro ao selecionar '000 dissertação': {e}", out_file)

                    # Passo 8: Selecionar "ENEM"
                    log_step(f"[PASSO 8] Selecionando 'ENEM'...", out_file)
                    try:
                        page.wait_for_selector('select[name*="modalidade"], select[id*="modalidade"]', timeout=5000)
                        page.select_option('select[name*="modalidade"], select[id*="modalidade"]', label="ENEM")
                        log_ok(f"'ENEM' selecionado", out_file)
                    except Exception as e:
                        log_erro(f"Erro ao selecionar 'ENEM': {e}", out_file)

                    # Passo 9: Verificar botão de anexar arquivo (não clicar)
                    log_step(f"[PASSO 9] Verificando área de upload de arquivo...", out_file)
                    try:
                        page.wait_for_selector('input[type="file"]', timeout=5000)
                        log_ok(f"Input de arquivo encontrado (não anexado conforme regra)", out_file)
                    except Exception as e:
                        log_erro(f"Input de arquivo não encontrado: {e}", out_file)

                    # Passo 10: Verificar botão final de envio (não clicar)
                    log_step(f"[PASSO 10] Verificando botão final de envio...", out_file)
                    try:
                        for selector in [
                            'button:has-text("Enviar")',
                            'input[type="submit"][value*="Enviar"]',
                            'button[type="submit"]:has-text("Enviar")',
                        ]:
                            try:
                                page.wait_for_selector(selector, timeout=3000)
                                log_ok(f"Botão de envio encontrado via {selector} (não clicado conforme regra)", out_file)
                                break
                            except:
                                continue
                    except Exception as e:
                        log_erro(f"Botão de envio não encontrado: {e}", out_file)

                    log_step(f"=== DIAGNÓSTICO CONCLUÍDO ===", out_file)

            # Fechar navegador
            log_step(f"Fechando navegador...", out_file)
            browser.close()
            log_ok(f"Navegador fechado", out_file)

    except Exception as e:
        log_erro(f"Erro durante diagnóstico: {e}", out_file)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()