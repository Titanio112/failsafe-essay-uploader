# -*- coding: utf-8 -*-
"""Testes offline do fluxo de produção (T24): sem navegador, sem login, sem envio.

Playwright, login, identidade e o envio de cada item são mocks (autospec).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO
from modulos.base.excecoes import CaptchaOuBloqueio, LoginFalhou
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.base.progresso_relatorio import Progresso, ENVIADO, ERRO, REVISAO_MANUAL

# M3: cada aluno entra com a senha dele (alunos.csv)
ANA = Aluno(nome="Ana Lalara", email="ana@escola.com", senha="senha-da-ana")
BRUNO = Aluno(nome="Bruno Silva", email="bruno@escola.com", senha="senha-do-bruno")


@pytest.fixture(autouse=True)
def producao_liberada_so_no_teste(monkeypatch):
    """Estes testes exercitam o fluxo com mocks; a trava de 22/10 tem testes
    próprios em tests/test_t29.py."""
    from modulos.base import config as config_mod
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)


@pytest.fixture
def cfg(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "pend"
    cfg.arquivo_nomes_aprovados = tmp_path / "nomes_aprovados.csv"
    cfg.arquivo_pastas_aprovadas = tmp_path / "pastas_aprovadas.csv"
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.headless = True
    cfg.slow_mo_ms = 0
    cfg.turma = "Turma"  # M3: o main exige turma (aqui os caminhos já vêm prontos)
    return cfg


@pytest.fixture
def resultado(cfg):
    """Ana: temas 1 e 2; Bruno: tema 1."""
    itens = []
    for aluno, pasta, arquivo, codigo in [
        (ANA, "1 - Carta", "Ana Lalara - Red.jpg", "1"),
        (ANA, "2 - Tema", "Ana Lalara - Red.jpg", "2"),
        (BRUNO, "1 - Carta", "Bruno Silva - Red.jpg", "1"),
    ]:
        (cfg.pasta_raiz / pasta).mkdir(parents=True, exist_ok=True)
        (cfg.pasta_raiz / pasta / arquivo).write_bytes(str(cfg.pasta_raiz / pasta / arquivo).encode())
        itens.append(ItemConciliacao(pasta=pasta, arquivo=arquivo, pessoa=aluno.nome,
                                     estado=EXATO_UNICO, aluno=aluno, codigo_tema=codigo))
    return ResultadoConciliacao(itens=itens)


@pytest.fixture
def progresso(tmp_path):
    prog = Progresso(tmp_path / "progresso.db")
    yield prog
    prog.close()


@pytest.fixture
def mocks():
    with patch("modulos.envio.fluxo_envio_producao.sync_playwright") as mock_pw, \
         patch("builtins.input", return_value="ENVIAR") as mock_input, \
         patch("modulos.envio.fluxo_envio_producao.obter_senha", return_value="senha-falsa"), \
         patch("modulos.envio.fluxo_envio_producao.time.sleep") as mock_sleep, \
         patch("modulos.envio.fluxo_envio_producao.verificar_dominio_autorizado", autospec=True), \
         patch("modulos.envio.fluxo_envio_producao.login", autospec=True) as mock_login, \
         patch("modulos.envio.fluxo_envio_producao.confirmar_identidade", autospec=True) as mock_ident, \
         patch("modulos.envio.fluxo_envio_producao.logout", autospec=True), \
         patch("modulos.envio.fluxo_envio_producao.enviar_item", autospec=True) as mock_enviar:
        mock_browser = MagicMock()
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_enviar.return_value = ENVIADO
        yield {
            "browser": mock_browser, "input": mock_input, "sleep": mock_sleep,
            "login": mock_login, "ident": mock_ident, "enviar": mock_enviar,
        }


def _enviados(mocks):
    """[(aluno_id, chave)] na ordem em que enviar_item foi chamado."""
    return [(c.args[1], c.args[2].chave_progresso) for c in mocks["enviar"].call_args_list]


def _executar(cfg, resultado, progresso=None, **kw):
    from modulos.envio.fluxo_envio_producao import executar_envio_producao
    return executar_envio_producao(cfg, resultado, progresso, **kw)


def test_lote_inteiro_enviado_uma_confirmacao_um_contexto_por_aluno(cfg, resultado, mocks):
    assert _executar(cfg, resultado) == 0

    assert mocks["input"].call_count == 1
    assert mocks["browser"].new_context.call_count == 2
    assert [c.args[2] for c in mocks["login"].call_args_list] == [ANA.email, BRUNO.email]
    assert _enviados(mocks) == [
        (ANA.id, "1 - Carta/Ana Lalara - Red.jpg"),
        (ANA.id, "2 - Tema/Ana Lalara - Red.jpg"),
        (BRUNO.id, "1 - Carta/Bruno Silva - Red.jpg"),
    ]
    # Pausa entre envios do mesmo aluno e entre alunos (P7)
    assert mocks["sleep"].call_count == 2


@pytest.mark.parametrize("texto", ["enviar", "ENVIAR TESTE", "", "sim"])
def test_confirmacao_diferente_de_ENVIAR_cancela_sem_login(cfg, resultado, mocks, texto):
    mocks["input"].return_value = texto

    assert _executar(cfg, resultado) == 2

    assert mocks["login"].call_count == 0
    assert mocks["enviar"].call_count == 0


def test_login_falha_marca_erro_do_aluno_e_segue(cfg, resultado, progresso, mocks):
    mocks["login"].side_effect = [LoginFalhou("senha"), None]

    assert _executar(cfg, resultado, progresso) == 1

    for chave in ("1 - Carta/Ana Lalara - Red.jpg", "2 - Tema/Ana Lalara - Red.jpg"):
        assert progresso.obter(ANA.id, chave)["estado"] == ERRO
    assert _enviados(mocks) == [(BRUNO.id, "1 - Carta/Bruno Silva - Red.jpg")]


def test_identidade_divergente_nao_envia_nada_do_aluno(cfg, resultado, mocks):
    from modulos.base.excecoes import IdentidadeDivergente
    mocks["ident"].side_effect = [IdentidadeDivergente("outro nome"), True]

    _executar(cfg, resultado)

    assert [aluno for aluno, _ in _enviados(mocks)] == [BRUNO.id]


def test_erro_em_item_para_o_aluno_e_segue_para_o_proximo(cfg, resultado, mocks):
    mocks["enviar"].side_effect = [ERRO, ENVIADO]

    assert _executar(cfg, resultado) == 1

    # 2º item da Ana nem é tentado; Bruno é processado
    assert _enviados(mocks) == [
        (ANA.id, "1 - Carta/Ana Lalara - Red.jpg"),
        (BRUNO.id, "1 - Carta/Bruno Silva - Red.jpg"),
    ]


def test_revisao_manual_para_a_execucao_inteira(cfg, resultado, mocks):
    mocks["enviar"].side_effect = [REVISAO_MANUAL]

    assert _executar(cfg, resultado) == 1

    assert _enviados(mocks) == [(ANA.id, "1 - Carta/Ana Lalara - Red.jpg")]
    assert mocks["login"].call_count == 1


def test_captcha_no_login_para_a_execucao_inteira(cfg, resultado, progresso, mocks):
    mocks["login"].side_effect = CaptchaOuBloqueio("captcha")

    assert _executar(cfg, resultado, progresso) == 1

    assert mocks["login"].call_count == 1
    assert mocks["enviar"].call_count == 0
    assert progresso.obter(BRUNO.id, "1 - Carta/Bruno Silva - Red.jpg") is None


def test_nada_para_enviar_nao_pede_confirmacao(cfg, mocks):
    assert _executar(cfg, ResultadoConciliacao(itens=[])) == 0

    assert mocks["input"].call_count == 0
    assert mocks["login"].call_count == 0


def test_limites_chegam_ao_lote(cfg, resultado, mocks):
    assert _executar(cfg, resultado, limite_alunos=1, limite_redacoes=1) == 0

    assert _enviados(mocks) == [(ANA.id, "1 - Carta/Ana Lalara - Red.jpg")]


# ---- Ligação com o CLI (main.py) ----

def test_main_envio_real_chama_fluxo_de_producao(cfg, resultado, tmp_path, monkeypatch):
    """--envio-real com CSV de códigos e planilha -> executar_envio_producao com os limites."""
    from openpyxl import Workbook
    import main as main_mod

    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["nome", "email"])
    ws.append([ANA.nome, ANA.email])
    cfg.planilha = tmp_path / "alunos.xlsx"
    wb.save(cfg.planilha)
    cfg.aba_planilha = "Alunos"
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "progresso.db"

    (tmp_path / "dados").mkdir()
    (tmp_path / "dados" / "temas_site.csv").write_text("codigo,texto\n1,1- Carta\n2,2- Tema\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    chamado = {}

    def fluxo_falso(cfg_, resultado_, progresso_, limite_alunos=None, limite_redacoes=None):
        chamado["fila"] = [i.chave for i in resultado_.fila_validada()]
        chamado["limites"] = (limite_alunos, limite_redacoes)
        return 0
    monkeypatch.setattr(main_mod, "executar_envio_producao", fluxo_falso)

    assert main_mod.main(["--envio-real", "--limite-alunos", "1", "--limite-redacoes", "2"]) == 0

    assert chamado["limites"] == (1, 2)
    assert chamado["fila"] == ["1 - Carta/Ana Lalara - Red.jpg", "2 - Tema/Ana Lalara - Red.jpg"]


def test_main_sem_envio_real_nao_chama_fluxo_de_producao(cfg, resultado, tmp_path, monkeypatch):
    import main as main_mod
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["nome", "email"])
    ws.append([ANA.nome, ANA.email])
    cfg.planilha = tmp_path / "alunos.xlsx"
    wb.save(cfg.planilha)
    cfg.aba_planilha = "Alunos"
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "progresso.db"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)

    def nao_pode(*a, **k):
        raise AssertionError("dry-run chamou o fluxo de producao")
    monkeypatch.setattr(main_mod, "executar_envio_producao", nao_pode)

    assert main_mod.main([]) == 0
