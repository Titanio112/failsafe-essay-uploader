"""Testes de identidade (confirmar_identidade) - página simulada.

M3: só o menu do usuário (``.navbar-right .dropdown-toggle``), exatamente
um elemento, nome igual ao da planilha depois de normalizar. Os fallbacks
``text=<nome>`` e ``a[href='#'] >> text=Testes`` saíram.

Cobrem:
- nome igual -> ok; acentos/maiúsculas/espaços -> ok
- elemento ausente, texto vazio, mais de um, abreviado, diferente -> IdentidadeDivergente
- nunca procura o nome em outro lugar da página
- e-mail mascarado na mensagem
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError as PWTimeoutError

from modulos.base.excecoes import IdentidadeDivergente
from modulos.dados.planilha_arquivos import Aluno
from modulos.site.login import confirmar_identidade

MENU = ".navbar-right .dropdown-toggle"
ALUNO = Aluno(nome="Usuario Testes Ignorar", email="teste@esquema.com")


def _pagina(texto="", quantos=1, timeout=False):
    """Página falsa: ``locator`` só responde ao seletor do menu."""
    page = MagicMock(url="https://www.esquemaredacao.com.br/minhas-redacoes?x=1")
    menu = MagicMock()
    menu.count.return_value = quantos
    menu.first.text_content.return_value = texto
    if timeout:
        menu.first.wait_for.side_effect = PWTimeoutError("timeout")

    def locator(seletor):
        assert seletor == MENU, f"procurou fora do menu: {seletor}"
        return menu
    page.locator.side_effect = locator
    return page, menu


@pytest.mark.parametrize("texto", ["Usuario Testes Ignorar ", "USUÁRIO  testes ignorar"])
def test_nome_igual_confere(texto):
    page, menu = _pagina(texto)
    assert confirmar_identidade(page, ALUNO) is True
    menu.first.wait_for.assert_called_with(state="visible", timeout=10000)


@pytest.mark.parametrize("pagina_kw, trecho", [
    ({"timeout": True, "quantos": 0}, "encontrado: vazio"),         # elemento ausente
    ({"texto": "   "}, "encontrado: vazio"),                         # texto vazio
    ({"texto": "Usuario Testes Ignorar", "quantos": 2}, "qtd_casados: 2"),  # mais de um menu
    ({"texto": "Usuario Testes"}, "'usuario testes' != 'usuario testes ignorar'"),  # abreviado
    ({"texto": "Outro Usuario Qualquer"}, "'outro usuario qualquer' != 'usuario testes ignorar'"),
])
def test_identidade_que_nao_confere_e_erro(pagina_kw, trecho):
    page, _ = _pagina(**pagina_kw)
    with pytest.raises(IdentidadeDivergente) as exc_info:
        confirmar_identidade(page, ALUNO)
    msg = str(exc_info.value).lower()
    assert "identidade não confere" in msg
    assert trecho in msg
    assert "url: https://www.esquemaredacao.com.br/minhas-redacoes |" in msg  # sem a query
    assert "te***@esquema.com" in msg  # e-mail mascarado
    assert "teste@esquema.com" not in msg


def test_elemento_ausente_tem_diagnostico():
    page, _ = _pagina(timeout=True, quantos=0)
    with pytest.raises(IdentidadeDivergente) as exc_info:
        confirmar_identidade(page, ALUNO)
    msg = str(exc_info.value).lower()
    assert "elemento_encontrado: false" in msg
    assert "qtd_casados: 0" in msg
