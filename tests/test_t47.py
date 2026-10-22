# -*- coding: utf-8 -*-
"""Testes offline da T47: cópia de segurança do caderno, lista "o que
precisa de você" no fim do envio e menu principal. Sem navegador."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.base.copia_seguranca import copiar_caderno
from modulos.base.progresso_relatorio import ENVIADO, ERRO, REVISAO_MANUAL, Progresso
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import fluxo_envio_producao as fep
from modulos.envio.fila_producao import LoteAluno
from modulos.envio.fila_teste import ItemFilaTeste
from modulos.ferramentas import menu

TESTE = Aluno(NOME_CONTA_TESTE, "teste@teste.com")


# ─── Cópia do caderno ────────────────────────────────────────

def test_copia_tem_o_conteudo_e_guarda_so_as_ultimas(tmp_path):
    with Progresso(tmp_path / "progresso.db") as prog:
        prog.marcar("ana@x.com", "100/Ana.JPG", ENVIADO, pasta="100")
        copias = [copiar_caderno(prog.con, tmp_path / "copias", manter=3) for _ in range(5)]
    restantes = sorted((tmp_path / "copias").glob("progresso_*.db"))
    assert len(restantes) == 3 and restantes[-1] == copias[-1]
    con = sqlite3.connect(copias[-1])
    assert con.execute("SELECT estado FROM progresso").fetchone() == (ENVIADO,)
    con.close()


@pytest.fixture
def navegador_falso():
    with patch.object(fep, "sync_playwright") as pw, \
         patch.object(fep, "obter_senha", return_value="s"), \
         patch.object(fep, "verificar_dominio_autorizado"), patch.object(fep, "login"), \
         patch.object(fep, "confirmar_identidade"), patch.object(fep, "logout"), \
         patch.object(fep, "enviar_item", return_value=ENVIADO) as enviar:
        pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
        yield {"pw": pw, "enviar": enviar}


def _cenario(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    (tmp_path / "100 - T").mkdir()
    (tmp_path / "100 - T" / f"{TESTE.nome}.jpg").write_bytes(b"foto")
    return cfg, conciliar([TESTE], {"100 - T": [f"{TESTE.nome}.jpg"]}, codigos_site=["100"])


def test_envio_guarda_copia_antes_de_abrir_o_navegador(tmp_path, navegador_falso, capsys):
    cfg, resultado = _cenario(tmp_path)
    with Progresso(tmp_path / "p.db") as prog, patch("builtins.input", return_value="ENVIAR TESTE"):
        assert fep.executar_envio_producao(cfg, resultado, prog, conta_teste=TESTE.email) == 0
    assert len(list((cfg.pasta_relatorios / "copias").glob("progresso_*.db"))) == 1
    assert "Copia de seguranca do caderno" in capsys.readouterr().out


def test_sem_copia_nao_envia(tmp_path, navegador_falso, capsys):
    cfg, resultado = _cenario(tmp_path)
    with Progresso(tmp_path / "p.db") as prog, patch("builtins.input", return_value="ENVIAR TESTE"), \
         patch.object(fep, "copiar_caderno", side_effect=OSError("disco cheio")):
        assert fep.executar_envio_producao(cfg, resultado, prog, conta_teste=TESTE.email) == 2
    assert navegador_falso["pw"].call_count == 0
    assert "Nada foi enviado" in capsys.readouterr().out


# ─── O que precisa de você ───────────────────────────────────

def test_lista_do_que_precisa_de_voce(tmp_path, capsys):
    ana, bia = Aluno("Ana", "ana@x.com"), Aluno("Bia", "bia@x.com")
    lotes = [LoteAluno(ana, [ItemFilaTeste("100 - T", "Ana.JPG", "100", Path("x"), "100 - T/Ana.JPG"),
                             ItemFilaTeste("000 - G", "Ana.JPG", "000", Path("x"), "000 - G/Ana.JPG")]),
             LoteAluno(bia, [ItemFilaTeste("100 - T", "Bia.JPG", "100", Path("x"), "100 - T/Bia.JPG")])]
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ana.id, "100 - T/Ana.JPG", REVISAO_MANUAL, pasta="100", detalhe="Confirmacao inconclusiva")
        prog.marcar(ana.id, "000 - G/Ana.JPG", ERRO, pasta="000", detalhe="Upload nao aceito")
        assert fep.mostrar_o_que_precisa_de_voce(lotes, prog) == 3  # + Bia não tentada
    saida = capsys.readouterr().out
    assert "REVISAO_MANUAL (1): abra o site NA CONTA DESTE ALUNO" in saida
    assert "Ana - tema 100 - 100 - T/Ana.JPG: Confirmacao inconclusiva" in saida
    assert "ERRO (1): nada foi enviado" in saida
    assert "1 redacao(oes) nao chegaram a ser tentadas" in saida


def test_tudo_enviado_nao_mostra_a_lista(tmp_path, capsys):
    ana = Aluno("Ana", "ana@x.com")
    lotes = [LoteAluno(ana, [ItemFilaTeste("100 - T", "Ana.JPG", "100", Path("x"), "100 - T/Ana.JPG")])]
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ana.id, "100 - T/Ana.JPG", ENVIADO, pasta="100")
        assert fep.mostrar_o_que_precisa_de_voce(lotes, prog) == 0
    assert "precisa de voce" not in capsys.readouterr().out


# ─── Menu ────────────────────────────────────────────────────

def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


@pytest.mark.parametrize("respostas, argumentos", [
    (["1"], []),
    (["2"], ["--revisar"]),
    (["3", "", "n"], ["--ensaio", "3"]),
    (["3", "5", "s"], ["--ensaio", "5", "--envio-real"]),
    (["4", "n"], ["--modo-teste"]),
    (["4", "s"], ["--modo-teste", "--envio-real"]),
    (["6"], ["--analise-remota"]),
    (["8"], ["--preparar"]),
])
def test_cada_opcao_vira_os_argumentos_do_main(respostas, argumentos):
    entrada = _respostas(*respostas[1:])
    assert menu.argumentos_da_opcao(respostas[0], entrada, saida=lambda *_: None) == argumentos


def test_producao_bloqueada_nao_chama_o_main():
    saidas = []
    assert menu.argumentos_da_opcao("5", _respostas(), saida=saidas.append) is None
    assert any("BLOQUEADO" in s for s in saidas)


def test_desfazer_lista_os_logs_e_escolhe(tmp_path):
    (tmp_path / "renomeacoes_20261022_100000.csv").write_text("x", encoding="utf-8")
    (tmp_path / "renomeacoes_20261023_100000.csv").write_text("x", encoding="utf-8")
    args = menu.argumentos_da_opcao("7", _respostas("1"), tmp_path, saida=lambda *_: None)
    assert args == ["--desfazer-renomeacao", str(tmp_path / "renomeacoes_20261023_100000.csv")]


def test_menu_roda_o_main_volta_e_sai():
    chamadas = []
    def main_falso(argv):
        chamadas.append(argv)
        if argv == ["--revisar"]:
            raise RuntimeError("quebrou")
        return 0
    saidas = []
    assert menu.executar_menu(main_falso, _respostas("1", "", "2", "", "0"), saidas.append) == 0
    assert chamadas == [[], ["--revisar"]]
    assert any("Erro inesperado: RuntimeError: quebrou" in s for s in saidas)


def test_menu_sem_entrada_fecha():
    assert menu.executar_menu(lambda argv: 0, lambda _p: (_ for _ in ()).throw(EOFError())) == 0
