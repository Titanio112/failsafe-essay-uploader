"""Playwright: login, identidade, diagnóstico, upload, envio e logout.

Fase 1: somente a trava de envio está ativa. As rotinas web serão
implementadas na Fase 2 (diagnóstico) e Fase 3 (envio), após autorização.

Referência (scripts antigos, somente leitura, não alterar):
- Login Rails/devise: POST /auth/users/sign_in com authenticity_token
  obtido do form GET; cookies de sessão via requests.Session.
- Após login há seleção de escola (main.py antigo).
"""

from __future__ import annotations


def verificar_dominio_autorizado(page):
    dominio_esperado = "www.esquemaredacao.com.br"
    dominio_atual = page.url.split("//")[-1].split("/")[0]
    if dominio_atual != dominio_esperado:
        raise RuntimeError(f"[BLOQUEADO] domínio não autorizado: {dominio_atual}")

from pathlib import Path

from config import Config, exigir_envio_real
from planilha_arquivos import Aluno


def enviar_redacao(
    cfg: Config,
    aluno: Aluno,
    arquivo: Path,
    *,
    envio_real: bool = False,
) -> None:
    """Envia uma redação. Na Fase 1 sempre bloqueado sem ``envio_real``.

    Mesmo com a flag, a implementação real só existe a partir da Fase 3
    e exige as confirmações orquestradas por ``main.py``.
    """
    exigir_envio_real(envio_real)
    raise NotImplementedError(
        "Envio real será implementado na Fase 3, após o diagnóstico da Fase 2."
    )


def login_permissao(page, email, password):
    """Login na página USUÁRIO, usando os seletores formais esperados"""
    # Confirma domínio
    verificar_dominio_autorizado(page)
    # Acesse o formulário
    locator_form = page.locator("form#new_user")
    assert locator_form.count() == 1, "form não encontrado"
    # Preenche email
    email_input = page.locator("#user_email")
    assert email_input.count() == 1, "campo de e-mail inesperado"
    email_input.fill(email)
    # Preenche senha
    senha_input = page.locator("#user_password")
    assert senha_input.count() == 1, "campo de senha inesperado"
    senha_input.fill(password)
    # Envia
    submit_btn = page.locator('input[type="submit"][value="Entrar"]')
    assert submit_btn.count() == 1, "botão Entrar não encontrado"
    submit_btn.click()
    return page
