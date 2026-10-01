import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from config import Config
from planilha_arquivos import carregar_alunos, normalizar_nome, EXATO_UNICO

# Load .env file
load_dotenv()

def main():
    # 1. Setup Config
    cfg = Config()
    # Since we might not have config.ini populated, we'll try to find the spreadsheet in the default root
    if not cfg.planilha:
        # Default common name from config.example.ini
        default_sheet = "Alunos para corrigir redacoes.xlsx"
        cfg.planilha = cfg.pasta_raiz / default_sheet
    
    if not cfg.planilha.exists():
        print(f"Erro: Planilha não encontrada em {cfg.planilha}")
        sys.exit(1)

    # 2. Load and filter students
    try:
        alunos = carregar_alunos(cfg)
    except Exception as e:
        print(f"Erro ao carregar alunos: {e}")
        sys.exit(1)

    # Determine Sala B
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

    # Filter students of that sala and sort alphabetically (normalized)
    alunos_sala = [a for a in alunos if a.sala == sala_escolhida]
    alunos_sala.sort(key=lambda x: normalizar_nome(x.nome))

    # 3. Conciliation logic to find first valid student with JPGs
    # We need to find the mapping of Aluno -> Items in the conciliation process.
    # Since carregar_alunos only returns the list of students, we must perform 
    # the conciliation as would be done in the main app.
    from planilha_arquivos import conciliar, descobrir_arquivos, ResultadoConciliacao
    
    arquivos_por_pasta = descobrir_arquivos(cfg)
    resultado = conciliar(alunos, arquivos_por_pasta)
    validos = resultado.fila_validada()
    
    # Find first student (alphabetically) who has at least one EXATO_UNICO item
    selected_aluno = None
    selected_items = []

    for aluno in alunos_sala:
        # Check if this aluno has any valid items
        items = [i for i in validos if i.aluno and i.aluno.id == aluno.id]
        if items:
            selected_aluno = aluno
            selected_items = items
            break

    if not selected_aluno:
        print("Erro: Nenhum aluno da sala B com correspondência exata e única e JPGs foi encontrado.")
        sys.exit(1)

    # 4. Report student info
    print("\n--- Aluno Selecionado ---")
    print(f"Nome: {selected_aluno.nome}")
    email = selected_aluno.email
    masked_email = email[:3] + "..." + email.split('@')[-1] if email else "N/A"
    print(f"Email: {masked_email}")
    print(f"Sala: {selected_aluno.sala}")
    print("Arquivos JPG:")
    for item in selected_items:
        print(f"  {item.pasta}/{item.arquivo}")
    print("-----------------------\n")

    # 5. Login Diagnostic
    print("Iniciando diagnóstico de login...")
    from plataforma import login_permissao
    from playwright.sync_api import sync_playwright
    
    # Use credentials from .env
    email_env = os.getenv('ESQUEMA_EMAIL_TESTE')
    senha_env = os.getenv('ESQUEMA_SENHA_PADRAO')
    
    if not email_env or not senha_env:
        print("Erro: Credenciais não encontradas no .env")
        sys.exit(1)

    try:
        # Run login diagnostic with Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=250)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to login page first
            page.goto("https://www.esquemaredacao.com.br/auth/users/sign_in")
            
            # login_permissao returns the page after login
            res_login = login_permissao(page, email_env, senha_env)
            
            out_dir = Path("diagnosticos")
            out_dir.mkdir(exist_ok=True)
            out_file = out_dir / "saida_diagnostico.txt"
            
            # Save the result as string
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(str(res_login.url))
                
            print(f"Sucesso: Diagnóstico salvo em {out_file}")
            
            # Wait for login to complete and capture result
            page.wait_for_load_state("networkidle")
            print(f"URL após login: {page.url}")
            
            # Check if still on login page (login failed) or redirected
            if "sign_in" in page.url:
                print("AVISO: Ainda na página de login - credenciais podem ser inválidas")
                # Get page content for diagnosis
                content = page.content()
                with open(out_dir / "pagina_login.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"HTML da página salvo em {out_dir / 'pagina_login.html'}")
            else:
                print("Login aparente bem-sucedido!")
            
            # Close browser
            browser.close()
    except Exception as e:
        print(f"Falha no diagnóstico de login: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
