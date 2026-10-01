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