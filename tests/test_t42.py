# -*- coding: utf-8 -*-
"""Testes offline da T42: ensaio com redações reais na conta de teste.
Sem navegador. A RAIZ é temporária (conftest)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.base.progresso_relatorio import ENVIADO, Progresso
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import fluxo_envio_producao as fep
from modulos.envio.ensaio import montar_lote_ensaio

TESTE = Aluno(nome=NOME_CONTA_TESTE, email="teste@teste.com")
ANA = Aluno(nome="ANA LALARA LARILI DOS LARITO", email="ana@escola.com")
BIA = Aluno(nome="BEATRIZ LANETO", email="bia@escola.com")


def _real(tmp_path):
    """Duas pastas reais (000 e 100), duas alunas em cada."""
    arquivos = {"3B - Aporofobia": [], "100 - Filiacao": []}
    for pasta in arquivos:
        (tmp_path / pasta).mkdir()
        for aluno in (ANA, BIA):
            (tmp_path / pasta / f"{aluno.nome}.JPG").write_bytes(str(tmp_path / pasta / f"{aluno.nome}.JPG").encode())
            arquivos[pasta].append(f"{aluno.nome}.JPG")
    return conciliar([ANA, BIA], arquivos, codigos_site=["000", "100"],
                     codigos_pasta={"3B - Aporofobia": "000"})


def test_amostra_vai_toda_para_a_conta_de_teste_alternando_pastas(tmp_path):
    lotes = montar_lote_ensaio(_real(tmp_path), tmp_path, TESTE, quantidade=3)
    assert [l.aluno for l in lotes] == [TESTE]
    itens = lotes[0].itens
    assert [(i.pasta, i.codigo) for i in itens] == [
        ("100 - Filiacao", "100"), ("3B - Aporofobia", "000"), ("100 - Filiacao", "100")]
    assert all(i.chave_progresso.startswith("ensaio/") for i in itens)
    # contagem do dia (T35): 2 no tema 100, 1 no 000
    assert [i.total_mesmo_tema for i in itens] == [2, 1, 2]


def test_ja_enviado_no_ensaio_nao_volta_e_total_soma_o_caderno(tmp_path):
    with Progresso(":memory:") as prog:
        prog.marcar(TESTE.id, "ensaio/100 - Filiacao/ANA LALARA LARILI DOS LARITO.JPG", ENVIADO, pasta="100")
        itens = montar_lote_ensaio(_real(tmp_path), tmp_path, TESTE, prog, quantidade=1)[0].itens
        assert [i.arquivo for i in itens] == ["BEATRIZ LANETO.JPG"]
        assert itens[0].total_mesmo_tema == 2  # 1 já hoje no caderno + 1 agora
        # o registro do aluno real nunca é usado
        assert prog.obter(ANA.id, "100 - Filiacao/ANA LALARA LARILI DOS LARITO.JPG") is None


def test_sem_fila_validada_nao_monta_nada(tmp_path):
    (tmp_path / "3B - Sem tema").mkdir()
    resultado = conciliar([ANA], {"3B - Sem tema": [f"{ANA.nome}.JPG"]}, codigos_site=["000"])
    assert montar_lote_ensaio(resultado, tmp_path, TESTE) == []


@pytest.fixture
def navegador_falso():
    with patch.object(fep, "sync_playwright") as pw, \
         patch.object(fep, "obter_senha", return_value="s") as senha, \
         patch.object(fep, "verificar_dominio_autorizado"), \
         patch.object(fep, "login") as login, \
         patch.object(fep, "confirmar_identidade") as identidade, \
         patch.object(fep, "logout"), \
         patch.object(fep, "enviar_item", return_value=ENVIADO) as enviar:
        pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
        yield {"senha": senha, "login": login, "identidade": identidade, "enviar": enviar}


def _main_ensaio(tmp_path, monkeypatch):
    import main as main_mod
    pasta = tmp_path / "Redações plataforma"
    for nome_pasta in ("3B - Aporofobia", "100 - Filiacao"):
        (pasta / nome_pasta).mkdir(parents=True)
        (pasta / nome_pasta / f"{ANA.nome}.JPG").write_bytes(str(pasta / nome_pasta / f"{ANA.nome}.JPG").encode())
    cfg = Config()
    cfg.turma = "Turma"  # M3: o main exige turma (aqui os caminhos já vêm prontos)
    cfg.pasta_raiz = pasta
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text(f"Nome;Email\n{ANA.nome};{ANA.email}\n", encoding="utf-8")
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    (config_mod.RAIZ / "dados").mkdir(parents=True, exist_ok=True)
    (config_mod.RAIZ / "dados" / "temas_site.csv").write_text(
        "codigo,texto\n000,000- DISSERTATIVO\n100,100- Filiacao\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ESQUEMA_EMAIL_TESTE", TESTE.email)
    monkeypatch.setattr(main_mod, "TEMAS_SITE_CSV", config_mod.RAIZ / "dados" / "temas_site.csv")
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    return main_mod


def test_main_ensaio_sem_envio_real_so_mostra(tmp_path, monkeypatch, capsys, navegador_falso):
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    assert main_mod.main(["--ensaio", "2"]) == 0
    saida = capsys.readouterr().out
    assert "── Ensaio na conta de teste " in saida
    assert "tema 100: 100 - Filiacao/ANA LALARA LARILI DOS LARITO.JPG" in saida
    assert "python main.py --ensaio 2 --envio-real" in saida
    assert navegador_falso["login"].call_count == 0


def test_main_ensaio_envia_so_na_conta_de_teste_com_producao_bloqueada(tmp_path, monkeypatch, navegador_falso):
    assert config_mod.PRODUCAO_BLOQUEADA is True
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    with patch("builtins.input", return_value="ENVIAR TESTE"):
        assert main_mod.main(["--ensaio", "--envio-real"]) == 0
    navegador_falso["senha"].assert_called_once_with("ESQUEMA_SENHA_TESTE")
    assert {c.args[2] for c in navegador_falso["login"].call_args_list} == {TESTE.email}
    assert {c.args[1].email for c in navegador_falso["identidade"].call_args_list} == {TESTE.email}
    assert len(navegador_falso["enviar"].call_args_list) == 1  # só a pasta com código: 100


def test_main_ensaio_com_enviar_de_producao_nao_envia(tmp_path, monkeypatch, navegador_falso):
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    with patch("builtins.input", return_value="ENVIAR"):
        assert main_mod.main(["--ensaio", "--envio-real"]) == 2
    assert navegador_falso["login"].call_count == 0


def test_main_ensaio_recusa_email_de_aluno_como_conta_de_teste(tmp_path, monkeypatch, navegador_falso, capsys):
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    monkeypatch.setenv("ESQUEMA_EMAIL_TESTE", ANA.email.upper())
    assert main_mod.main(["--ensaio", "--envio-real"]) == 2
    assert "e-mail de um aluno da lista" in capsys.readouterr().out
    assert navegador_falso["login"].call_count == 0


def test_producao_sem_ensaio_continua_bloqueada(tmp_path, monkeypatch, navegador_falso, capsys):
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    assert main_mod.main(["--envio-real"]) == 2
    assert "[BLOQUEADO] Envio para alunos reais desativado" in capsys.readouterr().out
    assert navegador_falso["login"].call_count == 0


@pytest.mark.parametrize("extra", [["--modo-teste"], ["--revisar"], ["--analise-remota"]])
def test_ensaio_nao_combina(extra, tmp_path, monkeypatch, navegador_falso):
    main_mod = _main_ensaio(tmp_path, monkeypatch)
    assert main_mod.main(["--ensaio", *extra]) == 2
