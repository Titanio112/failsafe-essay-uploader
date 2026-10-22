"""Login e confirmação de identidade."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from modulos.config import Config
from modulos.planilha_arquivos import Aluno
from modulos.excecoes import CaptchaOuBloqueio, LoginFalhou, IdentidadeDivergente


DOMINIO_ESPERADO = "www.esquemaredacao.com.br"


def verificar_dominio_autorizado(page: Page) -> None:
    dominio_atual = page.url.split("/")[2] if len(page.url.split("/")) > 2 else ""
    if DOMINIO_ESPERADO not in dominio_atual:
        raise CaptchaOuBloqueio(f"Domínio inesperado: {dominio_atual}. Esperado: {DOMINIO_ESPERADO}")


def login(page: Page, cfg: Config, email: str, senha: str) -> None:
    """Faz login na plataforma e navega para /minhas-redacoes."""
    page.goto(f"https://{DOMINIO_ESPERADO}/auth/users/sign_in", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Preencher formulário
    page.fill('input[name="user[email]"]', email)
    page.fill('input[name="user[password]"]', senha)
    page.click('input[name="commit"]')

    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Navegar para /minhas-redacoes após login (confirmado na Fase 2)
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Critério de sucesso: NÃO está em sign_in E existe saldo OU menu do usuário
    if "sign_in" in page.url:
        raise LoginFalhou(f"Permaneceu na página de login: {page.url}")
    
    # Verificar saldo ("Você tem N crédito(s)") ou menu do usuário
    from playwright.sync_api import Locator
    saldo_locator = page.locator('text=Você tem').first
    usuario_locator = page.locator('a[href="#"] >> text=Testes').first
    try:
        saldo_locator.wait_for(timeout=5000)
    except PWTimeoutError:
        try:
            usuario_locator.wait_for(timeout=3000)
        except PWTimeoutError:
            raise LoginFalhou(f"Login incerto — sem saldo visível e sem menu do usuário. URL: {page.url}")


def nomes_compativeis(no_site: str, na_lista: str) -> bool:
    """Nomes já normalizados. Iguais, ou um contido no outro com a mesma
    1ª palavra e ao menos 2 palavras no menor (site pode abreviar:
    "ana lalara" x "ana lalara larili dos larito") (T27)."""
    if no_site == na_lista:
        return True
    a, b = no_site.split(), na_lista.split()
    if min(len(a), len(b)) < 2 or a[0] != b[0]:
        return False
    return set(a) <= set(b) or set(b) <= set(a)


def confirmar_identidade(page: Page, aluno: Aluno, modo_teste: bool = False) -> bool:
    """Confirma se o aluno logado corresponde ao esperado.

    Retorna True se confirmado, levanta IdentidadeDivergente se não.
    Fail-closed: se elemento não existir ou texto vier vazio, NÃO aceita vazio."""
    from modulos.planilha_arquivos import mascarar_email
    from modulos.normalizacao import normalizar_nome

    # Esperar elemento do menu do usuário (topo da página) - até 10s
    # HTML real: <a class="dropdown-toggle" ...>Usuario Testes Ignorar <i class="fa fa-caret-down"></i></a>
    # Tentar seletor específico do dropdown primeiro
    dropdown_locator = page.locator(".navbar-right .dropdown-toggle").first
    encontrado = False
    texto_visivel = ""
    qtd_casados = 0

    try:
        dropdown_locator.wait_for(state="visible", timeout=10000)
        texto_visivel = (dropdown_locator.text_content() or "").strip()
        # O texto inclui o ícone, limpar
        if texto_visivel:
            encontrado = True
            qtd_casados = 1
    except PWTimeoutError:
        # Fallback 1: buscar por texto do nome do aluno em qualquer lugar
        nome_locator = page.locator(f"text={aluno.nome}").first
        try:
            nome_locator.wait_for(state="visible", timeout=5000)
            encontrado = True
            qtd_casados = nome_locator.count()
            texto_visivel = (nome_locator.text_content() or "").strip()
        except PWTimeoutError:
            # Fallback 2: seletor genérico "Testes"
            fallback_locator = page.locator("a[href='#'] >> text=Testes").first
            try:
                fallback_locator.wait_for(state="visible", timeout=3000)
                encontrado = True
                qtd_casados = fallback_locator.count()
                texto_visivel = (fallback_locator.text_content() or "").strip()
            except PWTimeoutError:
                pass

    if not encontrado or not texto_visivel:
        # Diagnóstico seguro (sem e-mail, sem senha)
        url_sem_query = page.url.split("?")[0]
        diagnostico = (
            f"URL: {url_sem_query} | "
            f"elemento_encontrado: {encontrado} | "
            f"qtd_casados: {qtd_casados} | "
            f"texto_menu: '{texto_visivel}'"
        )
        email_mascarado = mascarar_email(aluno.email)
        raise IdentidadeDivergente(
            f"Identidade não confere. Esperado: {aluno.nome} ({email_mascarado}). "
            f"Encontrado: VAZIO. Diagnóstico: {diagnostico}"
        )

    # Comparação normalizada (acentos, maiúsculas, pontuação)
    nome_normalizado = normalizar_nome(texto_visivel)
    esperado_normalizado = normalizar_nome(aluno.nome)

    if not nomes_compativeis(nome_normalizado, esperado_normalizado):
        url_sem_query = page.url.split("?")[0]
        diagnostico = (
            f"URL: {url_sem_query} | "
            f"elemento_encontrado: {encontrado} | "
            f"qtd_casados: {qtd_casados} | "
            f"texto_menu: '{texto_visivel}'"
        )
        email_mascarado = mascarar_email(aluno.email)
        raise IdentidadeDivergente(
            f"Identidade não confere. Esperado: {aluno.nome} ({email_mascarado}). "
            f"Encontrado (normalizado): '{nome_normalizado}' != '{esperado_normalizado}'. "
            f"Diagnóstico: {diagnostico}"
        )

    # Em modo teste, salvar snapshot HTML se identidade falhou (aqui passou)
    if modo_teste:
        try:
            from datetime import datetime
            from pathlib import Path
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            diag_dir = Path("diagnosticos")
            diag_dir.mkdir(exist_ok=True)
            (diag_dir / f"identidade_{ts}.html").write_text(page.content(), encoding="utf-8")
        except Exception:
            pass  # snapshot é best-effort, não quebrar o fluxo

    return True