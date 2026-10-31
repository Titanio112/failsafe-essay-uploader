# -*- coding: utf-8 -*-
"""Issue #52: o menu encadeia as etapas de Preparar e não manda ninguém digitar "python main.py ..."."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import pendencias, tela
from modulos.base.turma import raiz_redacoes
from modulos.ferramentas import menu

TURMA = ("Escola A", "1A")
DA_TURMA = ["--escola", "Escola A", "--turma", "1A"]


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _main_que_anota(chamadas, pendente=None):
    def main(argv):
        chamadas.append(argv)
        if pendente is not None and argv[:1] == []:
            pendencias.revisao_pendente = pendente.pop(0)
        return 0
    return main


def test_conferir_com_pendencias_oferece_a_revisao_e_depois_conferir_de_novo():
    chamadas = []
    pendencias.revisao_pendente = True

    def main(argv):
        chamadas.append(argv)
        if "--revisar" not in argv:
            pendencias.revisao_pendente = False  # a 2ª conferência já não acha pendência
        return 0
    menu.proximo_passo([], TURMA, main, _resp("s", "s", "n"), lambda *_: None)
    assert chamadas == [["--revisar"] + DA_TURMA, DA_TURMA]  # Revisão, depois Conferir de novo; "n" pára na conta


def test_conferir_sem_pendencias_oferece_as_contas_no_site():
    chamadas = []
    pendencias.revisao_pendente = False
    menu.proximo_passo([], TURMA, _main_que_anota(chamadas), _resp("s"), lambda *_: None)
    assert chamadas == [["--conferir-site"] + DA_TURMA]  # o CONFERIR é do próprio main


def test_responder_n_nao_chama_nada_e_etapas_de_fora_do_preparar_nao_oferecem_nada():
    chamadas = []
    pendencias.revisao_pendente = True
    menu.proximo_passo([], TURMA, _main_que_anota(chamadas), _resp("n"), lambda *_: None)
    menu.proximo_passo(["--conferir-site"], TURMA, _main_que_anota(chamadas), _resp(), lambda *_: None)
    menu.proximo_passo(["--analise-remota"], TURMA, _main_que_anota(chamadas), _resp(), lambda *_: None)
    assert chamadas == []


def test_erro_no_passo_seguinte_nao_derruba_o_menu():
    pendencias.revisao_pendente = False
    saidas = []

    def main(argv):
        raise RuntimeError("falhou")
    menu.proximo_passo([], TURMA, main, _resp("s"), saidas.append)
    assert any("Erro inesperado" in s for s in saidas)


def test_dentro_do_menu_a_dica_de_comando_some_e_depois_volta():
    visto = []

    def main(argv):
        tela.comando("python main.py --revisar", "x", visto.append)
        return 0
    assert tela.DICAS_DE_COMANDO is True
    tela.comando("python main.py --revisar", "x", visto.append)  # fora do menu: aparece
    assert len(visto) == 1
    menu.executar_menu(main, _resp("1", "", "0"), lambda *_: None, turma=TURMA)  # a opção 1 chama o main
    assert len(visto) == 1 and tela.DICAS_DE_COMANDO is True  # dentro do menu nada saiu; o estado voltou
    tela.comando("python main.py", "força", visto.append, sempre=True)
    assert len(visto) == 2


def _turma_com_foto(turma, pasta_tema):
    pasta = raiz_redacoes() / "Escola Um" / turma
    (pasta / "temas" / pasta_tema).mkdir(parents=True)
    (pasta / "alunos.csv").write_text("Nome;Email;Senha\nAna Um;ana@um.example.com;s1\n", encoding="utf-8")
    (pasta / "temas" / pasta_tema / "Ana Um.jpg").write_bytes(turma.encode())


def test_main_marca_pendencia_de_revisao_so_quando_ha_pasta_sem_codigo(monkeypatch):
    import main as main_mod
    temas = config_mod.RAIZ / "dados" / "temas_site.csv"
    temas.parent.mkdir(exist_ok=True)
    temas.write_text("codigo,texto\n100,100- Tema\n", encoding="utf-8")
    monkeypatch.setattr(main_mod, "TEMAS_SITE_CSV", temas)
    _turma_com_foto("3A", "Tema sem codigo")
    _turma_com_foto("3B", "100 - Tema")
    pendencias.revisao_pendente = False
    assert main_mod.main(["--escola", "Escola Um", "--turma", "3A"]) == 0
    assert pendencias.revisao_pendente is True
    assert main_mod.main(["--escola", "Escola Um", "--turma", "3B"]) == 0
    assert pendencias.revisao_pendente is False
