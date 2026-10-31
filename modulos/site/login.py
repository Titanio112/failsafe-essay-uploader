"""Login e confirmação de identidade."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno
from modulos.base.excecoes import CaptchaOuBloqueio, LoginFalhou, IdentidadeDivergente


DOMINIO_ESPERADO = "www.esquemaredacao.com.br"


def verificar_dominio_autorizado(page: Page) -> None:
    """T44: o host tem de ser EXATAMENTE o do site (não basta conter)."""
    from urllib.parse import urlparse
    dominio_atual = urlparse(page.url).hostname or ""
    if dominio_atual != DOMINIO_ESPERADO:
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
    saldo_locator = page.locator('text=Você tem').first
    usuario_locator = page.locator('a[href="#"] >> text=Testes').first
    try:
        saldo_locator.wait_for(timeout=5000)
    except PWTimeoutError:
        try:
            usuario_locator.wait_for(timeout=3000)
        except PWTimeoutError:
            raise LoginFalhou(f"Login incerto — sem saldo visível e sem menu do usuário. URL: {page.url}")


def confirmar_identidade(page: Page, aluno: Aluno, modo_teste: bool = False) -> bool:
    """Confirma se o aluno logado corresponde ao esperado.

    Retorna True se confirmado, levanta IdentidadeDivergente se não.
    M3: só o menu do usuário (``.navbar-right .dropdown-toggle``), exatamente
    UM elemento com texto, e o nome igual ao da planilha depois de
    ``normalizar_nome`` (sem tolerar nome abreviado; sem procurar o nome no
    resto da página). Se o site abrevia, a planilha leva o nome do site."""
    from modulos.dados.planilha_arquivos import mascarar_email
    from modulos.dados.normalizacao import normalizar_nome

    # HTML real: <a class="dropdown-toggle" ...>Usuario Testes Ignorar <i class="fa fa-caret-down"></i></a>
    menu = page.locator(".navbar-right .dropdown-toggle")
    texto_visivel = ""
    qtd_casados = 0
    try:
        menu.first.wait_for(state="visible", timeout=10000)
        qtd_casados = menu.count()
        if qtd_casados == 1:
            texto_visivel = (menu.first.text_content() or "").strip()
    except PWTimeoutError:
        pass

    nome_normalizado = normalizar_nome(texto_visivel)
    esperado_normalizado = normalizar_nome(aluno.nome)
    if qtd_casados != 1 or not nome_normalizado or nome_normalizado != esperado_normalizado:
        # Diagnóstico seguro (sem e-mail, sem senha)
        diagnostico = (
            f"URL: {page.url.split('?')[0]} | "
            f"elemento_encontrado: {qtd_casados > 0} | "
            f"qtd_casados: {qtd_casados} | "
            f"texto_menu: '{texto_visivel}'"
        )
        encontrado = (f" (normalizado): '{nome_normalizado}' != '{esperado_normalizado}'" if nome_normalizado
                      else ": VAZIO")
        raise IdentidadeDivergente(
            f"Identidade não confere. Esperado: {aluno.nome} ({mascarar_email(aluno.email)}). "
            f"Encontrado{encontrado}. Diagnóstico: {diagnostico}"
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