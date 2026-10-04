"""Login e confirmação de identidade."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config import Config
from planilha_arquivos import Aluno
from excecoes import CaptchaOuBloqueio, LoginFalhou, IdentidadeDivergente


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


def confirmar_identidade(page: Page, aluno: Aluno) -> bool:
    """Confirma se o aluno logado corresponde ao esperado.
    
    Retorna True se confirmado, levanta IdentidadeDivergente se não."""
    page.goto("https://www.esquemaredacao.com.br/alunos/minhas-redacoes", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Tentar ler nome/e-mail da página
    # Seletor pode variar — usar fallback
    try:
        nome_logado = page.locator(".usuario-nome, .user-name, [data-testid=user-name]").first.inner_text(timeout=5000)
    except PWTimeoutError:
        nome_logado = ""

    if aluno.nome.lower() not in nome_logado.lower() and aluno.email.lower() not in nome_logado.lower():
        raise IdentidadeDivergente(f"Identidade não confere. Esperado: {aluno.nome} ({aluno.email}). Encontrado: {nome_logado}")
    
    return True