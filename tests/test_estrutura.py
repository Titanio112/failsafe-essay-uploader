# -*- coding: utf-8 -*-
"""Issue #35: adicionar e renomear escolas e turmas (menu 13). RAIZ temporária; sem site."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.trava import trava_de_envio
from modulos.base.turma import PASTA_GUIA, listar_escolas, listar_turmas, raiz_redacoes
from modulos.ferramentas import estrutura
from modulos.ferramentas.assistente_inicial import executar_assistente


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _base():
    executar_assistente(_resp("s", "s", "2", "Escola A", "2", "1A", "1B", "Escola B", "1", "2A"))


def _caderno():
    banco = config_mod.RAIZ / "relatorios" / "progresso.db"
    banco.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(banco)
    con.execute("CREATE TABLE progresso (aluno_id TEXT, turma TEXT NOT NULL DEFAULT '')")
    con.executemany("INSERT INTO progresso VALUES (?, ?)", [("a", "Escola A/1A"), ("b", "Escola A/1B"),
                                                           ("c", "Escola B/2A"), ("d", "")])
    con.commit()
    con.close()
    return banco


def _turmas_do_caderno(banco):
    con = sqlite3.connect(banco)
    try:
        return sorted(r[0] for r in con.execute("SELECT turma FROM progresso"))
    finally:
        con.close()


def test_adicionar_escola_e_turma():
    _base()
    assert estrutura.adicionar_turma(_resp("1", "1C"), lambda *_: None)  # 1 = Escola A
    assert listar_turmas("Escola A") == ["1A", "1B", "1C"]
    assert (raiz_redacoes() / "Escola A" / "1C" / "temas" / PASTA_GUIA).is_dir()
    assert estrutura.adicionar_escola(_resp("Escola C", "1", "3A"), lambda *_: None)
    assert listar_escolas() == ["Escola A", "Escola B", "Escola C"]
    assert (raiz_redacoes() / "Escola C" / "LEIA-ME.md").is_file()


def test_renomear_turma_leva_o_caderno_e_so_ele():
    _base()
    banco = _caderno()
    assert estrutura.renomear_turma(_resp("1", "1", "1Z", "s"), lambda *_: None)  # Escola A, turma 1A
    assert listar_turmas("Escola A") == ["1B", "1Z"]
    assert _turmas_do_caderno(banco) == ["", "Escola A/1B", "Escola A/1Z", "Escola B/2A"]
    assert list((banco.parent / "copias").glob("progresso_*.db"))  # cópia antes


def test_renomear_escola_leva_turmas_caderno_e_arquivo_morto():
    _base()
    banco = _caderno()
    morto = config_mod.RAIZ / "Arquivo morto" / "Escola A" / "1A"
    morto.mkdir(parents=True)
    assert estrutura.renomear_escola(_resp("1", "Colegio A", "s"), lambda *_: None)
    assert listar_escolas() == ["Colegio A", "Escola B"]
    assert _turmas_do_caderno(banco) == ["", "Colegio A/1A", "Colegio A/1B", "Escola B/2A"]
    assert (config_mod.RAIZ / "Arquivo morto" / "Colegio A" / "1A").is_dir()


def test_nome_repetido_cancelar_ou_nao_nao_mudam_nada():
    _base()
    banco = _caderno()
    assert not estrutura.renomear_turma(_resp("1", "1", "1B", "1A"), lambda *_: None)  # 1B existe; Enter... esgota
    assert listar_turmas("Escola A") == ["1A", "1B"]
    assert not estrutura.renomear_turma(_resp("1", "1", "1Z", "n"), lambda *_: None)
    assert listar_turmas("Escola A") == ["1A", "1B"] and _turmas_do_caderno(banco)[1] == "Escola A/1A"


def test_envio_rodando_recusa_renomear():
    _base()
    banco = _caderno()
    with trava_de_envio(banco.parent / "envio.trava"):
        assert not estrutura.renomear_turma(_resp("1", "1", "1Z", "s"), lambda *_: None)
    assert listar_turmas("Escola A") == ["1A", "1B"]
