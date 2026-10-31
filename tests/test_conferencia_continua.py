# -*- coding: utf-8 -*-
"""Issue #50: a conferência no site não para por senha recusada ou identidade divergente. Sem navegador de verdade."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.excecoes import CaptchaOuBloqueio, IdentidadeDivergente, LoginFalhou
from modulos.dados.planilha_arquivos import Aluno
from modulos.site import conferencia_site as cs


def _conferencias(n):
    return [cs.ConferenciaAluno(Aluno(f"Aluno {i} Teste", f"a{i}@x.example.com", senha="s"), []) for i in range(1, n + 1)]


def _rodar(conferencias, efeitos):
    """``efeitos``: um por aluno, na ordem; uma exceção é levantada, qualquer outra coisa vira a lista lida."""
    it = iter(efeitos)

    def ler_conta(page, cfg, aluno):
        e = next(it)
        if isinstance(e, Exception):
            raise e
        return e

    with patch("playwright.sync_api.sync_playwright", MagicMock()), \
            patch.object(cs, "_ler_conta", side_effect=ler_conta), patch.object(cs, "logout"):
        return cs._ler_no_navegador(Config(), conferencias, lambda *_: None)


def test_senha_recusada_e_identidade_divergente_seguidas_nao_param_a_conferencia():
    conf = _conferencias(5)
    parou = _rodar(conf, [[], LoginFalhou("x"), IdentidadeDivergente("y"), [], []])
    assert parou is False
    assert [c.lista is not None for c in conf] == [True, False, False, True, True]
    assert conf[1].erro and conf[2].erro and not conf[3].erro
    assert [c.aluno.nome for c in cs.contas_com_problema(conf)] == ["Aluno 2 Teste", "Aluno 3 Teste"]


def test_captcha_para_tudo_e_os_seguintes_ficam_nao_tentados():
    conf = _conferencias(4)
    assert _rodar(conf, [[], CaptchaOuBloqueio("captcha")]) is True
    assert "CAPTCHA" in conf[1].erro
    assert conf[2].lista is None and not conf[2].erro  # nao tentado


def test_tres_erros_de_site_seguidos_param_mas_um_login_recusado_no_meio_zera_a_conta():
    conf = _conferencias(6)
    assert _rodar(conf, [RuntimeError("a"), RuntimeError("b"), LoginFalhou("c"), RuntimeError("d"),
                         RuntimeError("e"), []]) is False  # o login recusado provou que o site responde
    conf = _conferencias(6)
    assert _rodar(conf, [RuntimeError("a"), RuntimeError("b"), RuntimeError("c"), [], []]) is True
    assert conf[3].lista is None and not conf[3].erro  # o 4º nem foi tentado
