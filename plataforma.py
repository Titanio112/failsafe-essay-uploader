"""Playwright: login, identidade, diagnóstico, upload, envio e logout.

Fase 1: somente a trava de envio está ativa. As rotinas web serão
implementadas na Fase 2 (diagnóstico) e Fase 3 (envio), após autorização.

Referência (scripts antigos, somente leitura, não alterar):
- Login Rails/devise: POST /auth/users/sign_in com authenticity_token
  obtido do form GET; cookies de sessão via requests.Session.
- Após login há seleção de escola (main.py antigo).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config import Config, exigir_envio_real
from planilha_arquivos import Aluno


# ─── Exceções ──────────────────────────────────────────────────

class CaptchaOuBloqueio(RuntimeError):
    """CAPTCHA, 2FA ou bloqueio detectado — parar lote imediatamente."""


class LoginFalhou(RuntimeError):
    """Credenciais inválidas ou página de login não carregou."""


class IdentidadeDivergente(RuntimeError):
    """Nome/e-mail logado não confere com o aluno esperado."""


class UploadNaoConfirmado(RuntimeError):
    """Mensagem de upload aceito não apareceu no tempo esperado."""


class ConfirmacaoInconclusiva(RuntimeError):
    """Não foi possível confirmar envio na lista remota em 120 s."""


# ─── Helpers de domínio ────────────────────────────────────────

DOMINIO_ESPERADO = "www.esquemaredacao.com.br"


def verificar_dominio_autorizado(page: Page) -> None:
    dominio_atual = page.url.split("//")[-1].split("/")[0]
    if dominio_atual != DOMINIO_ESPERADO:
        raise RuntimeError(f"[BLOQUEADO] domínio não autorizado: {dominio_atual}")


# ─── Estruturas ────────────────────────────────────────────────

@dataclass
class ItemListaRedacao:
    """Uma linha da tabela em /minhas-redacoes."""
    data: str
    tema: str
    nota: str
    situacao: str
    botao_texto: str


@dataclass
class TemaCombo:
    """Uma opção do combo 'Informe o tema da redação'."""
    codigo: str
    texto_completo: str


# ─── Login ────────────────────────────────────────────────────

def login(page: Page, email: str, password: str) -> Page:
    """Faz login e retorna a page já em /minhas-redacoes."""

    page.goto(f"https://{DOMINIO_ESPERADO}/auth/users/sign_in")
    page.wait_for_load_state("domcontentloaded")
    verificar_dominio_autorizado(page)

    page.locator('input[name="user[email]"]').fill(email)
    page.locator('input[name="user[password]"]').fill(password)
    page.locator('input[name="commit"]').click()

    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    
    # Navegar para /minhas-redacoes após login
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    return page

    return page


def confirmar_identidade(page: Page, aluno: Aluno) -> bool:
    """Verifica se o nome logado (topo à direita) bate com o aluno esperado."""
    nome_element = page.locator('text=Usuario Testes Ignorar').first
    try:
        nome_element.wait_for(timeout=5000)
    except PWTimeoutError:
        nome_element = page.locator('a[href="#"] >> text=Testes').first
        try:
            nome_element.wait_for(timeout=3000)
        except PWTimeoutError:
            raise IdentidadeDivergente("não encontrou nome do usuário logado no topo")

    from planilha_arquivos import normalizar_nome
    nome_na_tela = normalizar_nome(nome_element.text_content() or "")
    nome_esperado = normalizar_nome(aluno.nome)

    if nome_na_tela != nome_esperado:
        raise IdentidadeDivergente(
            f"nome na tela '{nome_na_tela}' != esperado '{nome_esperado}'"
        )
    return True


def ler_saldo_creditos(page: Page) -> int:
    """Lê o saldo de créditos na página /minhas-redacoes."""
    import re
    texto = page.locator('text=Você tem').first.text_content() or ""
    match = re.search(r"Você tem\s+(\d+)\s+crédito", texto)
    if match:
        return int(match.group(1))
    return 0


def ler_lista_redacoes(page: Page) -> list[ItemListaRedacao]:
    """Lê a tabela de redações em /minhas-redacoes."""
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

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


def contar_linhas_codigo_data(lista: list[ItemListaRedacao], codigo: str, data_hoje: str) -> int:
    """Conta quantas linhas têm o código do tema e a data de hoje."""
    import re
    count = 0
    for item in lista:
        match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
        if match and match.group(1) == codigo and item.data == data_hoje:
            count += 1
    return count


def detectar_ja_enviado(lista: list[ItemListaRedacao], codigo: str) -> Optional[tuple[str, str]]:
    """Verifica se o código já foi enviado (qualquer data). Retorna (data, tema) se encontrado."""
    import re
    for item in lista:
        match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
        if match and match.group(1) == codigo:
            return (item.data, item.tema)
    return None


def ler_lista_redacoes_html(html: str) -> list[ItemListaRedacao]:
    """
    Lê a lista de redações a partir de HTML/texto simulado (para testes offline).
    Espera o mesmo formato que /minhas-redacoes: tabela com colunas data, tema, nota, situação, botão.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, "html.parser")
    itens = []
    
    table = soup.find("table")
    if not table:
        return itens
    
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue
        data = cols[0].get_text(strip=True)
        tema = cols[1].get_text(strip=True)
        nota = cols[2].get_text(strip=True)
        situacao = cols[3].get_text(strip=True)
        botao_texto = cols[4].get_text(strip=True) if len(cols) > 4 else ""
        itens.append(ItemListaRedacao(
            data=data, tema=tema, nota=nota, situacao=situacao, botao_texto=botao_texto
        ))
    return itens


def verificar_duplicidade(lista_redacoes: list[ItemListaRedacao], codigo_tema: str) -> tuple[str, Optional[str]]:
    """
    Verifica duplicidade conforme AGENTS.md:
    - Mesmo código em qualquer data → JA_ENVIADO com mensagem [DUPLICADA]
    - Lista sem dados suficientes (tema/data) → REVISAO_MANUAL
    - Código sempre string ('0' ≠ '00' ≠ '000')
    
    Returns: (estado, mensagem_ou_data)
      - ('JA_ENVIADO', data_envio) se já enviado
      - ('REVISAO_MANUAL', None) se lista ilegível
      - ('OK', None) se pode prosseguir
    """
    import re
    
    if not lista_redacoes:
        return "REVISAO_MANUAL", None
    
    tem_dados_suficientes = False
    for item in lista_redacoes:
        # Verificar se tem tema e data válidos
        if item.tema and item.data:
            tem_dados_suficientes = True
            match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema.strip())
            if match:
                codigo_item = match.group(1)
                if codigo_item == codigo_tema:
                    # Mesmo código encontrado → JA_ENVIADO
                    return "JA_ENVIADO", item.data
    
    if not tem_dados_suficientes:
        return "REVISAO_MANUAL", None
    
    return "OK", None
# ─── Navegação formulário ────────────────────────────────────

def abrir_formulario_envio(page: Page) -> Page:
    """Vai para /wordings/new (Enviar redação)."""
    page.click('a:has-text("Enviar redação")')
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    if "wordings/new" not in page.url:
        raise RuntimeError(f"URL inesperada ao abrir formulário: {page.url}")
    return page


def ler_combo_temas(page: Page) -> list[TemaCombo]:
    """Lê as opções do combo 'Informe o tema da redação'."""
    combo = page.get_by_label("Informe o tema da redação")
    combo.click()
    page.wait_for_timeout(300)
    
    temas = []
    options = page.get_by_role("option").all()
    for opt in options:
        texto = opt.text_content() or ""
        if texto.strip():
            from planilha_arquivos import extrair_codigo_do_tema_site
            codigo = extrair_codigo_do_tema_site(texto)
            if codigo:
                temas.append(TemaCombo(codigo=codigo, texto_completo=texto.strip()))
    return temas


def selecionar_tema_por_codigo(page: Page, codigo: str, codigos_site: list[str] = None) -> bool:
    """Seleciona a opção do combo cujo código seja exatamente igual.
    
    Se codigos_site for fornecido, valida:
    - Código repetido no combo -> REVISAO_MANUAL (não seleciona, levanta RuntimeError)
    - Código inexistente no combo -> REVISAO_MANUAL (não seleciona, levanta RuntimeError)
    """
    # Validar duplicidade no combo se lista fornecida
    if codigos_site is not None:
        from collections import Counter
        contador = Counter(codigos_site)
        if contador[codigo] > 1:
            raise RuntimeError(f"Código '{codigo}' aparece {contador[codigo]}x no combo → SIMULADO/REVISAO_MANUAL")
        if codigo not in codigos_site:
            raise RuntimeError(f"Código '{codigo}' não existe no combo → REVISAO_MANUAL")
    
    temas = ler_combo_temas(page)
    for tema in temas:
        if tema.codigo == codigo:
            combo = page.get_by_label("Informe o tema da redação")
            combo.select_option(label=tema.texto_completo)
            page.wait_for_timeout(300)
            return True
    return False


def selecionar_criterio(page: Page, criterio: str = "ENEM") -> None:
    """Seleciona o critério de avaliação."""
    combo = page.get_by_label("Selecione um critério de avaliação")
    combo.click()
    page.get_by_role("option", name=criterio).click()
    page.wait_for_timeout(300)


# ─── Upload ──────────────────────────────────────────────────

def anexar_arquivo(page: Page, arquivo: Path) -> None:
    """Anexa o arquivo JPG no input de arquivo."""
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(arquivo))
    page.wait_for_timeout(1000)


def aguardar_upload_aceito(page: Page, timeout_segundos: int = 120) -> bool:
    """
    Aguarda o botão 'Enviar resposta' ficar habilitado (upload aceito).
    """
    import time
    inicio = time.monotonic()
    while time.monotonic() - inicio < timeout_segundos:
        try:
            btn = page.get_by_role("button", name="Enviar resposta")
            if btn.is_enabled():
                return True
        except PWTimeoutError:
            pass
        page.wait_for_timeout(2000)
    return False


def clicar_enviar(page: Page) -> None:
    """Clica no botão final 'Enviar resposta' uma única vez."""
    btn = page.get_by_role("button", name="Enviar resposta")
    btn.click()
    page.wait_for_load_state("networkidle")


# ─── Verificação pós-envio ───────────────────────────────────

def aguardar_confirmacao(
    page: Page,
    codigo: str,
    data_hoje: str,
    contagem_antes: int,
    saldo_antes: int,
    timeout_segundos: int = 120,
    poll_segundos: int = 5,
) -> tuple[bool, str]:
    """
    Polling em /minhas-redacoes até confirmar envio ou timeout.
    Retorna (sucesso, detalhe).
    """
    import time
    inicio = time.monotonic()
    tentativa = 0
    
    while time.monotonic() - inicio < timeout_segundos:
        tentativa += 1
        page.wait_for_timeout(poll_segundos * 1000)
        page.reload()
        page.wait_for_load_state("networkidle")
        
        lista = ler_lista_redacoes(page)
        contagem_depois = contar_linhas_codigo_data(lista, codigo, data_hoje)
        saldo_depois = ler_saldo_creditos(page)
        
        # Log da tentativa
        detalhe = f"Tentativa {tentativa}: contagem={contagem_depois} (antes={contagem_antes}), saldo={saldo_depois} (antes={saldo_antes})"
        print(detalhe)
        
        if contagem_depois == contagem_antes + 1:
            # Verifica se a nova linha está "Pendente"
            for item in lista:
                import re
                match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
                if match and match.group(1) == codigo and item.data == data_hoje:
                    if item.situacao == "Pendente":
                        if saldo_depois == saldo_antes - 1:
                            return True, f"{detalhe} → ENVIADO (Pendente, saldo -1)"
                        else:
                            return False, f"{detalhe} → REVISAO_MANUAL (saldo não caiu 1)"
                    elif item.situacao == "Processando arquivo":
                        # Ainda processando, continua o polling
                        continue
                    else:
                        return False, f"{detalhe} → REVISAO_MANUAL (estado='{item.situacao}')"
        
        elif contagem_depois > contagem_antes + 1:
            return False, f"{detalhe} → REVISAO_MANUAL (contagem subiu mais que 1)"
    
    return False, f"Timeout {timeout_segundos}s: contagem não subiu ou linha não chegou a Pendente"


# ─── API legada ──────────────────────────────────────────────

def enviar_redacao(
    cfg: Config,
    aluno: Aluno,
    arquivo: Path,
    *,
    envio_real: bool = False,
) -> None:
    """API legada mantida para compatibilidade com testes."""
    exigir_envio_real(envio_real)
    raise NotImplementedError(
        "Use as funções de Fase 3 via main.py com Progresso e autorização completa."
    )


def logout(page: Page) -> None:
    """Faz logout clicando no dropdown do usuário e no link 'Sair'."""
    # Dropdown do usuário no topo direito
    user_dropdown = page.get_by_role("button", name="Usuario Testes Ignorar")
    user_dropdown.click()
    page.wait_for_timeout(200)
    
    # Link "Sair" no dropdown
    page.get_by_role("link", name="Sair").click()
    page.wait_for_load_state("networkidle")
    
    # Verificar que voltou para a página de login ou home
    if "sign_in" not in page.url and "login" not in page.url:
        # Se foi para home, navegar para login
        page.goto(f"https://{DOMINIO_ESPERADO}/auth/users/sign_in")
        page.wait_for_load_state("networkidle")


def login_permissao(page: Page, email: str, password: str) -> Page:
    """API legada mantida para compatibilidade com scripts de diagnóstico."""
    return login(page, email, password)