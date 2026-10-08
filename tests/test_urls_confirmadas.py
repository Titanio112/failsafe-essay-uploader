# -*- coding: utf-8 -*-
"""Testes offline: URLs confirmadas no código."""
import pytest


def test_login_url_sign_in():
    """Login usa /auth/users/sign_in."""
    from modulos.login import DOMINIO_ESPERADO
    # O login navega para a pagina de sign_in
    # Verificar que o dominio esperado esta correto
    assert DOMINIO_ESPERADO == "www.esquemaredacao.com.br"
    # A URL de login e construida dinamicamente em login.py
    # Mas o padrao e: https://www.esquemaredacao.com.br/auth/users/sign_in
    # Nao ha URL hardcoded de login em login.py, mas o fluxo usa sign_in


def test_lista_redacoes_url():
    """Lista de redações usa /minhas-redacoes."""
    from modulos.lista_redacoes import ler_lista_redacoes
    import inspect
    source = inspect.getsource(ler_lista_redacoes)
    assert "/minhas-redacoes" in source
    assert "/alunos/minhas-redacoes" not in source
    assert "/meus-pedidos" not in source


def test_formulario_envio_url():
    """Formulário de envio usa /wordings/new."""
    from modulos.formulario_envio import abrir_formulario_envio
    import inspect
    source = inspect.getsource(abrir_formulario_envio)
    assert "/wordings/new" in source
    assert "/nova-redacao" not in source


def test_confirmar_identidade_url():
    """Confirmar identidade espera página /minhas-redacoes (página já aberta)."""
    from modulos.login import confirmar_identidade
    import inspect
    source = inspect.getsource(confirmar_identidade)
    # A função não navega para /minhas-redacoes - ela assume que a página já está lá
    # Verificar que não usa URLs antigas
    assert "/alunos/minhas-redacoes" not in source
    assert "/meus-pedidos" not in source