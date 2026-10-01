import pathlib

code = '''"""Playwright: login, identidade, diagnóstico, upload, envio e logout.

Fase 2/3: implementação completa após diagnóstico da plataforma.

Referência (scripts antigos, somente leitura, não alterar):
- Login Rails/devise: POST /auth/users/sign_in com authenticity_token
  obtido do form GET; cookies de sessão via requests.Session.
- Após login há seleção de escola (main.py antigo).
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config import Config, exigir_envio_real
from planilha_arquivos import Aluno
from progresso_relatorio import ENVIADO, ENVIANDI, JA_ENVIADO, REVISAO_MANUAL


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


# ─── Estruturas de retorno ────────────────────────────────────

@dataclass
class ItemRemoto:
    """Uma linha da lista remota de redações (Meus pedidos)."""
    data: str
    pacote: str
    valor: str
    situacao: str
    remote_id: str = ""


@dataclass
class ConfirmacaoEnvio:
    inequivoca: bool
    remote_id: str = ""
    resumo_seguro: str = ""


# ─── Login ────────────────────────────────────────────────────

def login(page: Page, email: str, password: str) -> Page:
    """Faz login e retorna a page já em /minhas-redacoes."""
    verificar_dominio_autorizado(page)

    page.goto(f"https://{DOMINIO_ESPERADO}/auth/users/sign_in")
    page.wait_for_load_state("domcontentloaded")

    page.locator('input[name="user[email]"]').fill(email)
    page.locator('input[name="user[password]"]').fill(password)
    page.locator('input[name="commit"]').click()

    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    if "sign_in" in page.url:
        raise LoginFalhou("permaneceu na página de login após submit")

    return page


def confirmar_identidade(page: Page, aluno: Aluno) -> bool:
    """Verifica se o nome logado bate com o aluno esperado."""
    user_dropdown = page.locator('a[href="#"] >> text=BUENO').first
    try:
        user_dropdown.wait_for(timeout=5000)
    except PWTimeoutError:
        user_dropdown = page.locator('nav >> text=ANA').first
        try:
            user_dropdown.wait_for(timeout=3000)
        except PWTimeoutError:
            raise IdentidadeDivergente("não encontrou nome do usuário logado no navbar")

    from planilha_arquivos import normalizar_nome
    nome_na_tela = normalizar_nome(user_dropdown.text_content() or "")
    nome_esperado = normalizar_nome(aluno.nome)

    if nome_na_tela != nome_esperado:
        raise IdentidadeDivergente(
            f"nome na tela '{nome_na_tela}' != esperado '{nome_esperado}'"
        )
    return True


# ─── Navegação ────────────────────────────────────────────────

def abrir_formulario_envio(page: Page) -> Page:
    """Vai para /wordings/new (Enviar redação)."""
    page.click('a:has-text("Enviar redação")')
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    if "wordings/new" not in page.url:
        raise RuntimeError(f"URL inesperada ao abrir formulário: {page.url}")
    return page


def selecionar_tema(page: Page, tema_esperado: str = "000- DISSERTATIVO ARGUMENTATIVO") -> None:
    """Seleciona o tema no combobox."""
    combo = page.get_by_label("Informe o tema da redação")
    combo.click()
    page.get_by_role("option", name=tema_esperado).click()
    page.wait_for_timeout(300)


def selecionar_criterio(page: Page, criterio: str = "ENEM") -> None:
    """Seleciona o critério de avaliação."""
    combo = page.get_by_label("Selecione um critério de avaliação")
    combo.click()
    page.get_by_role("option", name=criterio).click()
    page.wait_for_timeout(300)


# ─── Upload ───────────────────────────────────────────────────

def anexar_arquivo(page: Page, arquivo: Path) -> None:
    """Anexa o arquivo JPG no input de arquivo."""
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(arquivo))
    page.wait_for_timeout(1000)


def aguardar_upload_aceito(page: Page, timeout_segundos: int = 120) -> bool:
    """
    Aguarda a mensagem de upload aceito.
    Na plataforma, após anexar, aparece uma mensagem de sucesso antes de habilitar o botão.
    """
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


# ─── Envio e confirmação ──────────────────────────────────────

def clicar_enviar(page: Page) -> None:
    """Clica no botão final 'Enviar resposta' uma única vez."""
    btn = page.get_by_role("button", name="Enviar resposta")
    btn.click()
    page.wait_for_load_state("networkidle")


def ler_lista_remota(page: Page):
    """Lê a tabela de /meus-pedidos e retorna lista de itens."""
    page.goto(f"https://{DOMINIO_ESPERADO}/meus-pedidos")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    tabela = page.locator("table").first
    try:
        tabela.wait_for(timeout=5000)
    except PWTimeoutError:
        return []

    itens = []
    rows = tabela.locator("tbody tr").all()
    for row in rows:
        cells = row.locator("td").all()
        if len(cells) >= 4:
            itens.append(ItemRemoto(
                data=cells[0].text_content() or "",
                pacote=cells[1].text_content() or "",
                valor=cells[2].text_content() or "",
                situacao=cells[3].text_content() or "",
            ))
    return itens


def detectar_ja_enviado(
    page: Page,
    aluno: Aluno,
    arquivo: Path,
    lista_antes: list,
    progresso,
) -> tuple[bool, Optional[str], bool]:
    """
    Verifica se o arquivo já foi enviado comparando lista antes/depois.
    Retorna (confirmada, remote_id, inconclusiva).
    """
    lista_depois = ler_lista_remota(page)

    novos = [i for i in lista_depois if i not in lista_antes]

    if len(novos) == 1:
        return True, novos[0].pacote, False
    if len(novos) > 1:
        return False, "", True

    for item in lista_antes:
        if arquivo.name in item.pacote or arquivo.stem in item.pacote:
            return True, item.pacote, False

    return False, "", False


def procurar_nova_submissao(
    page: Page,
    aluno: Aluno,
    arquivo: Path,
    snapshot_antes: list,
    timeout_segundos: int = 120,
    poll_segundos: int = 10,
) -> ConfirmacaoEnvio:
    """Polling na lista remota até confirmar envio ou timeout."""
    inicio = time.monotonic()
    while time.monotonic() - inicio < timeout_segundos:
        page.reload()
        page.wait_for_load_state("networkidle")
        lista_atual = ler_lista_remota(page)

        novos = [i for i in lista_atual if i not in snapshot_antes]
        if len(novos) == 1:
            item = novos[0]
            return ConfirmacaoEnvio(
                inequivoca=True,
                remote_id=item.pacote,
                resumo_seguro=f"novo item: {item.pacote} ({item.situacao})"
            )
        elif len(novos) > 1:
            return ConfirmacaoEnvio(
                inequivoca=False,
                resumo_seguro=f"{len(novos)} itens novos simultâneos - ambíguo"
            )
        time.sleep(poll_segundos)

    return ConfirmacaoEnvio(
        inequivoca=False,
        resumo_seguro=f"timeout {timeout_segundos}s sem novo item confirmado"
    )


# ─── Contexto limpo ──────────────────────────────────────────

@contextmanager
def contexto_limpo(playwright, headless: bool = False, slow_mo: int = 500):
    """Context manager para browser + context limpo, com logout garantido."""
    browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
    context = browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}/")
            page.wait_for_load_state("domcontentloaded")
            user_menu = page.locator('a[href="#"] >> text=BUENO').first
            if user_menu.count():
                user_menu.click()
                page.get_by_role("link", name="Sair").click()
                page.wait_for_load_state("networkidle")
        except Exception:
            pass
        context.close()
        browser.close()


# ─── Orquestração Fase 3 ────────────────────────────────────

def processar_item(
    cfg: Config,
    aluno: Aluno,
    arquivo: Path,
    pasta: str,
    *,
    envio_real: bool,
    progresso,
    limite_alunos: int = 1,
    limite_redacoes: int = 1,
) -> None:
    """Processa um item (aluno + arquivo) completo: login -> upload -> envio -> confirmação."""
    exigir_envio_real(envio_real)

    if limite_alunos != 1 or limite_redacoes != 1:
        raise RuntimeError("Fase 3 exige --limite-alunos 1 --limite-redacoes 1")

    if progresso.envios_de(aluno.id) >= cfg.max_envios_por_aluno:
        progresso.marcar(aluno.id, arquivo.name, "PULADO", pasta=pasta,
                         detalhe=f"limite de {cfg.max_envios_por_aluno} envios atingido")
        return

    estado_atual = progresso.obter(aluno.id, arquivo.name)
    if estado_atual and estado_atual["estado"] in (ENVIADO, JA_ENVIADO):
        return

    if estado_atual and estado_atual["estado"] == ENVIANDI:
        progresso.marcar(aluno.id, arquivo.name, REVISAO_MANUAL, pasta=pasta,
                         detalhe="retomada: era ENVIANDO; confirmar na plataforma antes de qualquer ação")
        return

    from config import obter_senha
    senha = obter_senha()

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        with contexto_limpo(p, headless=cfg.headless, slow_mo=cfg.slow_mo_ms) as page:
            login(page, aluno.email, senha)
            try:
                confirmar_identidade(page, aluno)
            except IdentidadeDivergente as e:
                progresso.marcar(aluno.id, arquivo.name, "IDENTIDADE_DIVERGENTE", pasta=pasta,
                                 detalhe=str(e))
                return

            lista_antes = ler_lista_remota(page)

            ja_enviado, remote_id, inconclusivo = detectar_ja_enviado(
                page, aluno, arquivo, lista_antes, progresso
            )
            if ja_enviado:
                progresso.marcar(aluno.id, arquivo.name, JA_ENVIADO, pasta=pasta,
                                 detalhe=f"já constava na lista remota: {remote_id}")
                return
            if inconclusivo:
                progresso.marcar(aluno.id, arquivo.name, REVISAO_MANUAL, pasta=pasta,
                                 detalhe="não foi possível excluir duplicidade na lista remota")
                return

            abrir_formulario_envio(page)
            selecionar_tema(page, cfg.tema)
            selecionar_criterio(page, cfg.estilo_correcao)
            anexar_arquivo(page, arquivo)

            if not aguardar_upload_aceito(page, cfg.upload_timeout_segundos):
                progresso.marcar(aluno.id, arquivo.name, "ERRO_SITE", pasta=pasta,
                                 detalhe="upload não confirmou aceite no tempo limite")
                return

            snapshot_antes = ler_lista_remota(page)
            progresso.marcar(aluno.id, arquivo.name, ENVIANDI, pasta=pasta,
                             detalhe=f"snapshot_antes={len(snapshot_antes)} itens")

            clicar_enviar(page)

            confirmacao = procurar_nova_submissao(
                page, aluno, arquivo, snapshot_antes,
                timeout_segundos=cfg.confirmacao_timeout_segundos,
                poll_segundos=cfg.poll_lista_segundos,
            )

            if confirmacao.inequivoca:
                progresso.marcar(aluno.id, arquivo.name, ENVIADO, pasta=pasta,
                                 detalhe=f"confirmado: {confirmacao.resumo_seguro}")
                progresso.registrar_envio(aluno.id, arquivo.name, cfg.max_envios_por_aluno)
            else:
                progresso.marcar(aluno.id, arquivo.name, REVISAO_MANUAL, pasta=pasta,
                                 detalhe=confirmacao.resumo_seguro)


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
        "Use processar_item() via main.py com Progresso e autorização completa."
    )


def login_permissao(page: Page, email: str, password: str) -> Page:
    """API legada mantida para compatibilidade com scripts de diagnóstico."""
    return login(page, email, password)
'''

pathlib.Path("plataforma.py").write_text(code, encoding="utf-8")
print("plataforma.py atualizado com sucesso")
'''