# -*- coding: utf-8 -*-
"""Teste estático: roda pyflakes e falha se houver 'undefined name' ou 'referenced before assignment'."""
import subprocess
import sys


def test_pyflakes_no_undefined():
    """pyflakes não deve reportar undefined name nem referenced before assignment."""
    # T39: main.py + todos os módulos (modulos/ e subpastas) + todos os testes.
    # A lista antiga citava arquivos da raiz que não existem mais (config.py,
    # login.py...), então o pyflakes não checava nenhum módulo de verdade.
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    todos = ([str(raiz / "main.py")]
             + sorted(str(p) for p in (raiz / "modulos").rglob("*.py"))
             + sorted(str(p) for p in (raiz / "tests").glob("*.py")))
    assert len(todos) > 40, todos  # nunca checar "nada" em silêncio

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