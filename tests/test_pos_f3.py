# -*- coding: utf-8 -*-
"""Testes offline da arrumação pós-F3 (T22). Sem navegador, sem login."""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


# ---- R1: RAIZ é a raiz do projeto, não modulos/ ----

@pytest.mark.raiz_real
def test_raiz_e_a_pasta_do_projeto():
    from modulos.config import RAIZ
    assert RAIZ == RAIZ_PROJETO
    assert (RAIZ / "main.py").is_file()


@pytest.mark.raiz_real
def test_caminhos_padrao_ficam_na_raiz():
    from modulos.config import Config
    cfg = Config()
    assert cfg.banco_progresso == RAIZ_PROJETO / "relatorios" / "progresso.db"
    assert cfg.pasta_relatorios == RAIZ_PROJETO / "relatorios"
    assert cfg.pasta_raiz == RAIZ_PROJETO / "Redações plataforma"  # T38


# ---- R2: sem fallback por value no combo de temas ----

def test_selecao_pelo_texto_falha_nao_tenta_value():
    from modulos import formulario_envio

    page = MagicMock()
    page.get_by_label.return_value.select_option.side_effect = Exception("sem opcao")
    with patch.object(formulario_envio, "ler_combo_temas", return_value=[("0", "0- Narração")]):
        assert formulario_envio.selecionar_tema_por_codigo(page, "0") is False

    # Nenhuma seleção por value no select do tema
    page.locator.return_value.first.select_option.assert_not_called()


def test_codigo_ausente_no_combo_nao_seleciona_nada():
    from modulos import formulario_envio

    page = MagicMock()
    with patch.object(formulario_envio, "ler_combo_temas", return_value=[("00", "00- Carta")]):
        assert formulario_envio.selecionar_tema_por_codigo(page, "0") is False

    page.get_by_label.return_value.select_option.assert_not_called()
    page.locator.return_value.first.select_option.assert_not_called()


# ---- R3: imports internos sempre com prefixo modulos. ----

MODULOS_INTERNOS = {p.stem for p in (RAIZ_PROJETO / "modulos").glob("*.py")} - {"__init__"}


def test_nenhum_import_interno_sem_prefixo_modulos():
    """Pega `from lista_redacoes import ...` (T18E) e `from progresso_relatorio ...` (T22),
    inclusive dentro de funções e do bloco __main__."""
    problemas = []
    for arquivo in sorted((RAIZ_PROJETO / "modulos").glob("*.py")) + [RAIZ_PROJETO / "main.py"]:
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            if isinstance(no, ast.ImportFrom) and no.level == 0 and no.module in MODULOS_INTERNOS:
                problemas.append(f"{arquivo.name}:{no.lineno} from {no.module}")
            if isinstance(no, ast.Import):
                for alias in no.names:
                    if alias.name in MODULOS_INTERNOS:
                        problemas.append(f"{arquivo.name}:{no.lineno} import {alias.name}")
    assert problemas == []
