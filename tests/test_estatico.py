# -*- coding: utf-8 -*-
"""Teste estático: roda pyflakes e falha se houver 'undefined name' ou 'referenced before assignment'."""
import subprocess
import sys


def test_pyflakes_no_undefined():
    """pyflakes não deve reportar undefined name nem referenced before assignment."""
    # Módulos do projeto (raiz)
    modulos_raiz = [
        "main.py", "config.py", "estados.py", "normalizacao.py",
        "descoberta_arquivos.py", "conciliacao.py", "planilha_arquivos.py",
        "excecoes.py", "login.py", "lista_redacoes.py", "formulario_envio.py",
        "confirmacao.py", "progresso.py", "relatorios.py",
        "logging_config.py", "progresso_relatorio.py", "tabelas.py",
        "fluxo_dryrun.py", "fluxo_envio_teste.py", "fluxo_analise_remota.py",
    ]
    # Módulos de testes
    modulos_tests = [
        "tests/test_essenciais.py", "tests/test_identidade.py",
        "tests/test_imports_reais.py", "tests/test_login_criterio.py",
        "tests/test_urls_confirmadas.py", "tests/test_estatico.py",
    ]
    todos = modulos_raiz + modulos_tests

    resultado = subprocess.run(
        [sys.executable, "-m", "pyflakes"] + todos,
        capture_output=True,
        text=True,
    )

    # Filtrar apenas erros graves: undefined name / referenced before assignment
    erros_graves = []
    for linha in resultado.stdout.split("\n"):
        if "undefined name" in linha or "referenced before" in linha or "used before" in linha:
            erros_graves.append(linha.strip())

    if erros_graves:
        msg = "pyflakes encontrou erros graves (undefined/referenced before):\n" + "\n".join(erros_graves)
        assert False, msg

    # Se pyflakes retornar código != 0 mas sem erros graves, são apenas warnings (unused import, etc.)
    # Isso é aceitável - não falha o teste
    assert True