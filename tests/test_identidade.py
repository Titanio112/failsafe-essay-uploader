"""Testes de identidade (confirmar_identidade) - página simulada.

Cobrem:
- nome encontrado -> ok
- acentos/maiúsculas -> ok
- elemento ausente -> IdentidadeDivergente com diagnóstico
- texto vazio -> IdentidadeDivergente
- e-mail mascarado na mensagem
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from modulos.dados.planilha_arquivos import Aluno
from modulos.base.excecoes import IdentidadeDivergente


def test_confirmar_identidade_sucesso():
    """confirmar_identidade deve retornar True quando o nome bate (seletor dropdown)."""
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade
    from unittest.mock import MagicMock

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Mock do dropdown (.navbar-right .dropdown-toggle) - PRIMEIRA TENTATIVA
    dropdown_locator_mock = MagicMock()
    dropdown_locator_mock.first.wait_for = MagicMock()
    dropdown_locator_mock.first.text_content.return_value = "Usuario Testes Ignorar "

    # Fallback 1: page.locator("text=...") - não deve ser chamado
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for = MagicMock()
    nome_locator_mock.first.count.return_value = 1
    nome_locator_mock.first.text_content.return_value = "Usuario Testes Ignorar"

    # Fallback 2: page.locator("a[href='#'] >> text=Testes") - não deve ser chamado
    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 0

    def locator_side_effect(selector):
        if ".navbar-right .dropdown-toggle" in selector:
            return dropdown_locator_mock
        elif selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    # Mock verificar_dominio_autorizado
    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        result = confirmar_identidade(page, aluno, modo_teste=True)
        assert result is True
        # Verificar que wait_for foi chamado no dropdown com state="visible" e timeout=10000
        dropdown_locator_mock.first.wait_for.assert_called_with(state="visible", timeout=10000)
    finally:
        login_module.verificar_dominio_autorizado = original_verificar
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 0

    def locator_side_effect(selector):
        if ".navbar-right .dropdown-toggle" in selector:
            return dropdown_locator_mock
        elif selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    # Mock verificar_dominio_autorizado
    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        result = confirmar_identidade(page, aluno, modo_teste=True)
        assert result is True
        # Verificar que wait_for foi chamado no dropdown com state="visible" e timeout=10000
        dropdown_locator_mock.first.wait_for.assert_called_with(state="visible", timeout=10000)
    finally:
        login_module.verificar_dominio_autorizado = original_verificar

def test_confirmar_identidade_acentos_maiusculas():
    """confirmar_identidade deve normalizar acentos e maiúsculas."""
    from unittest.mock import MagicMock
    from playwright.sync_api import TimeoutError as PWTimeoutError
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Dropdown locator - timeout para cair no fallback
    dropdown_locator_mock = MagicMock()
    dropdown_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    dropdown_locator_mock.first.count.return_value = 0
    dropdown_locator_mock.first.text_content.return_value = ""

    # Nome na tela tem acento diferente: "USUÁRIO TESTES IGNORAR" vs "Usuario Testes Ignorar"
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for = MagicMock()
    nome_locator_mock.first.count.return_value = 1
    nome_locator_mock.first.text_content.return_value = "USUÁRIO TESTES IGNORAR"

    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 0
    fallback_locator_mock.first.text_content.return_value = ""

    def locator_side_effect(selector):
        if ".navbar-right .dropdown-toggle" in selector:
            return dropdown_locator_mock
        elif selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        result = confirmar_identidade(page, aluno, modo_teste=True)
        assert result is True
    finally:
        login_module.verificar_dominio_autorizado = original_verificar


def test_confirmar_identidade_elemento_ausente():
    """confirmar_identidade deve levantar IdentidadeDivergente com diagnóstico quando elemento não existe."""
    from unittest.mock import MagicMock
    from playwright.sync_api import TimeoutError as PWTimeoutError
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Ambos locators dão timeout
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    nome_locator_mock.first.count.return_value = 0
    nome_locator_mock.first.text_content.return_value = ""

    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    fallback_locator_mock.first.count.return_value = 0
    fallback_locator_mock.first.text_content.return_value = ""

    def locator_side_effect(selector):
        if selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        with pytest.raises(IdentidadeDivergente) as exc_info:
            confirmar_identidade(page, aluno, modo_teste=False)

        msg = str(exc_info.value).lower()
        assert "identidade não confere" in msg
        assert "encontrado: vazio" in msg
        assert "url:" in msg
        assert "elemento_encontrado: false" in msg
        assert "qtd_casados: 0" in msg
        assert "te***@esquema.com" in msg  # e-mail mascarado
    finally:
        login_module.verificar_dominio_autorizado = original_verificar


def test_confirmar_identidade_texto_vazio():
    """confirmar_identidade deve levantar IdentidadeDivergente quando texto vem vazio."""
    from unittest.mock import MagicMock
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Locator encontrado mas texto vazio
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for = MagicMock()
    nome_locator_mock.first.count.return_value = 1
    nome_locator_mock.first.text_content.return_value = ""  # vazio

    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 0
    fallback_locator_mock.first.text_content.return_value = ""

    def locator_side_effect(selector):
        if selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        with pytest.raises(IdentidadeDivergente) as exc_info:
            confirmar_identidade(page, aluno, modo_teste=False)

        msg = str(exc_info.value).lower()
        assert "identidade não confere" in msg
        assert "encontrado: vazio" in msg
        assert "te***@esquema.com" in msg  # e-mail mascarado
    finally:
        login_module.verificar_dominio_autorizado = original_verificar
def test_confirmar_identidade_fallback():
    """confirmar_identidade deve usar fallback (a[href='#'] >> text=Testes) quando seletor principal falha."""
    from unittest.mock import MagicMock
    from playwright.sync_api import TimeoutError as PWTimeoutError
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Dropdown locator - timeout
    dropdown_locator_mock = MagicMock()
    dropdown_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    dropdown_locator_mock.first.count.return_value = 0
    dropdown_locator_mock.first.text_content.return_value = ""

    # Principal (text=) dá timeout
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    nome_locator_mock.first.count.return_value = 0
    nome_locator_mock.first.text_content.return_value = ""

    # Fallback (a[href='#'] >> text=Testes) encontra
    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 1
    fallback_locator_mock.first.text_content.return_value = "Usuario Testes Ignorar"

    def locator_side_effect(selector):
        if ".navbar-right .dropdown-toggle" in selector:
            return dropdown_locator_mock
        elif selector.startswith("text="):
            return nome_locator_mock
        elif "a[href='#']" in selector and "Testes" in selector:
            return fallback_locator_mock
        return MagicMock()

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        result = confirmar_identidade(page, aluno, modo_teste=True)
        assert result is True
        fallback_locator_mock.first.wait_for.assert_called_with(state="visible", timeout=3000)
    finally:
        login_module.verificar_dominio_autorizado = original_verificar


def test_confirmar_identidade_nome_diferente():
    """confirmar_identidade deve levantar IdentidadeDivergente quando nome normalizado não bate."""
    from unittest.mock import MagicMock
    from playwright.sync_api import TimeoutError as PWTimeoutError
    import modulos.site.login as login_module
    from modulos.site.login import confirmar_identidade
    import pytest
    from modulos.base.excecoes import IdentidadeDivergente

    page = MagicMock()
    page.url = "https://www.esquemaredacao.com.br/minhas-redacoes"
    page.goto = MagicMock()
    page.wait_for_load_state = MagicMock()

    # Dropdown locator - timeout para cair no fallback
    dropdown_locator_mock = MagicMock()
    dropdown_locator_mock.first.wait_for.side_effect = PWTimeoutError("timeout")
    dropdown_locator_mock.first.count.return_value = 0
    dropdown_locator_mock.first.text_content.return_value = ""

    # Nome diferente
    nome_locator_mock = MagicMock()
    nome_locator_mock.first.wait_for = MagicMock()
    nome_locator_mock.first.count.return_value = 1
    nome_locator_mock.first.text_content.return_value = "Outro Usuario Qualquer"

    fallback_locator_mock = MagicMock()
    fallback_locator_mock.first.wait_for = MagicMock()
    fallback_locator_mock.first.count.return_value = 0
    fallback_locator_mock.first.text_content.return_value = ""

    def locator_side_effect(selector):
        if ".navbar-right .dropdown-toggle" in selector:
            return dropdown_locator_mock
        elif selector.startswith("text="):
            return nome_locator_mock
        return fallback_locator_mock

    page.locator.side_effect = locator_side_effect

    aluno = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")

    original_verificar = login_module.verificar_dominio_autorizado
    login_module.verificar_dominio_autorizado = MagicMock()

    try:
        with pytest.raises(IdentidadeDivergente) as exc_info:
            confirmar_identidade(page, aluno, modo_teste=False)

        msg = str(exc_info.value).lower()
        assert "identidade não confere" in msg
        assert "encontrado (normalizado): 'outro usuario qualquer'" in msg
        assert "te***@esquema.com" in msg  # e-mail mascarado
    finally:
        login_module.verificar_dominio_autorizado = original_verificar



def test_mascarar_email():
    """Teste unitário da função mascarar_email."""
    from modulos.dados.planilha_arquivos import mascarar_email

    assert mascarar_email("teste@esquema.com") == "te***@esquema.com"
    assert mascarar_email("a@b.com") == "a***@b.com"
    assert mascarar_email("longeremail@domain.org") == "lo***@domain.org"
    assert mascarar_email("") == "***"
    assert mascarar_email("sem-arroba") == "***"
    assert mascarar_email("@domain.com") == "***@domain.com"
