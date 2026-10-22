# -*- coding: utf-8 -*-
"""Testes offline da T40: o modo teste usa o mesmo caminho da produção
(aprovações, tema genérico, revisão, contagem), só com a conta de teste.
Sem navegador. A RAIZ é temporária (conftest)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.config import NOME_CONTA_TESTE, Config, configurar_modo_teste
from modulos.base.progresso_relatorio import ENVIADO
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import fluxo_envio_producao as fep

TESTE = Aluno(nome=NOME_CONTA_TESTE, email="teste@teste.com")
ANA = Aluno(nome="ANA LALARA LARILI DOS LARITO", email="ana@escola.com")


def test_modo_teste_usa_pasta_e_aprovacoes_proprias():
    cfg = Config()
    configurar_modo_teste(cfg)
    assert cfg.pasta_raiz == config_mod.RAIZ / "testes" / "redacoes_teste"
    assert cfg.arquivo_pastas_aprovadas.name == "pastas_aprovadas_teste.csv"
    assert cfg.arquivo_nomes_aprovados.name == "nomes_aprovados_teste.csv"
    assert cfg.arquivo_pastas_aprovadas != Config().arquivo_pastas_aprovadas


@pytest.fixture
def navegador_falso():
    with patch.object(fep, "sync_playwright") as pw, \
         patch.object(fep, "obter_senha", return_value="s") as senha, \
         patch.object(fep, "verificar_dominio_autorizado"), \
         patch.object(fep, "login") as login, \
         patch.object(fep, "confirmar_identidade"), \
         patch.object(fep, "logout"), \
         patch.object(fep, "enviar_item", return_value=ENVIADO) as enviar:
        pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
        yield {"senha": senha, "login": login, "enviar": enviar}


def _resultado(tmp_path, aluno, pastas=("000 - Generico",)):
    arquivos = {}
    for pasta in pastas:
        (tmp_path / pasta).mkdir(parents=True, exist_ok=True)
        (tmp_path / pasta / f"{aluno.nome}.jpg").write_bytes(b"x")
        arquivos[pasta] = [f"{aluno.nome}.jpg"]
    return conciliar([aluno], arquivos, codigos_site=["000"])


def test_conta_de_teste_envia_mesmo_com_producao_bloqueada(tmp_path, navegador_falso):
    """A trava de produção é para alunos reais; a conta de teste passa."""
    assert config_mod.PRODUCAO_BLOQUEADA is True
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    with patch("builtins.input", return_value="ENVIAR TESTE") as entrada:
        assert fep.executar_envio_producao(cfg, _resultado(tmp_path, TESTE), conta_teste=TESTE.email) == 0
    assert "ENVIAR TESTE" in entrada.call_args.args[0]
    navegador_falso["senha"].assert_called_once_with("ESQUEMA_SENHA_TESTE")
    assert navegador_falso["login"].call_args.args[2] == TESTE.email


def test_lote_de_teste_com_aluno_real_nao_envia(tmp_path, navegador_falso, capsys):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    with patch("builtins.input", side_effect=AssertionError("pediu confirmação")):
        assert fep.executar_envio_producao(cfg, _resultado(tmp_path, ANA), conta_teste=TESTE.email) == 2
    assert navegador_falso["login"].call_count == 0
    assert "nao e a conta de teste" in capsys.readouterr().out


def test_enviar_sem_teste_nao_vale_para_a_conta_de_teste(tmp_path, navegador_falso):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    with patch("builtins.input", return_value="ENVIAR"):
        assert fep.executar_envio_producao(cfg, _resultado(tmp_path, TESTE), conta_teste=TESTE.email) == 2
    assert navegador_falso["login"].call_count == 0


def test_duas_pastas_genericas_da_conta_de_teste_entram_no_lote(tmp_path, navegador_falso):
    """O que o Antônio vai testar: duas redações no tema 000 no mesmo dia."""
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    resultado = conciliar([TESTE], {"Aporofobia": [f"{TESTE.nome}.jpg"], "Discriminacao": [f"{TESTE.nome}.jpg"]},
                          codigos_site=["000"], codigos_pasta={"Aporofobia": "000", "Discriminacao": "000"})
    for pasta in ("Aporofobia", "Discriminacao"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / f"{TESTE.nome}.jpg").write_bytes(b"x")
    with patch("builtins.input", return_value="ENVIAR TESTE"):
        assert fep.executar_envio_producao(cfg, resultado, conta_teste=TESTE.email) == 0
    itens = [c.args[2] for c in navegador_falso["enviar"].call_args_list]
    assert [(i.codigo, i.total_mesmo_tema) for i in itens] == [("000", 2), ("000", 2)]


# ─── main ────────────────────────────────────────────────────

def _main_modo_teste(tmp_path, monkeypatch):
    import main as main_mod
    pasta = config_mod.RAIZ / "testes" / "redacoes_teste" / "Efeitos da aporofobia"
    pasta.mkdir(parents=True)
    (pasta / f"{NOME_CONTA_TESTE}.jpg").write_bytes(b"x")
    (tmp_path / "dados").mkdir()
    (tmp_path / "dados" / "temas_site.csv").write_text(
        "codigo,texto\n000,000- DISSERTATIVO ARGUMENTATIVO\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ESQUEMA_EMAIL_TESTE", "teste@teste.com")
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: Config())
    return main_mod


def test_main_modo_teste_dry_run_sugere_revisar_do_modo_teste(tmp_path, monkeypatch, capsys):
    main_mod = _main_modo_teste(tmp_path, monkeypatch)
    assert main_mod.main(["--modo-teste"]) == 0
    saida = capsys.readouterr().out
    assert "python main.py --modo-teste --revisar" in saida
    assert (config_mod.RAIZ / "testes" / "pastas_aprovadas_teste.csv").is_file()
    assert not (config_mod.RAIZ / "dados" / "pastas_aprovadas.csv").exists()  # o real não é tocado


def test_main_modo_teste_revisar_g_e_depois_tem_fila(tmp_path, monkeypatch, capsys):
    main_mod = _main_modo_teste(tmp_path, monkeypatch)
    respostas = iter(["g"])
    monkeypatch.setattr("builtins.input", lambda _p: next(respostas))
    assert main_mod.main(["--modo-teste", "--revisar"]) == 0
    capsys.readouterr()

    assert main_mod.main(["--modo-teste"]) == 0
    assert "Exatos unicos (fila real): 1" in capsys.readouterr().out
