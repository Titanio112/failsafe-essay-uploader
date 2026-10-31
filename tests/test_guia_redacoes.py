# -*- coding: utf-8 -*-
"""Issue #51: turma sem redações avisa e explica onde colocá-las. RAIZ temporária (conftest); sem site."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.turma import PASTA_GUIA, pasta_da_turma
from modulos.ferramentas import guia_redacoes as guia
from modulos.ferramentas import menu
from modulos.ferramentas.assistente_inicial import executar_assistente


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _base():
    executar_assistente(_resp("s", "2", "2", "Escola A", "1", "1A", "Escola B", "1", "2A"))


def _foto(escola, turma, pasta, nome="Ana Souza.jpg"):
    d = pasta_da_turma(escola, turma) / "temas" / pasta
    d.mkdir(parents=True, exist_ok=True)
    (d / nome).write_bytes(b"x")


def test_conta_so_jpg_em_pastas_de_tema_sem_a_guia_nem_enviadas():
    _base()
    assert guia.contar_redacoes("Escola A", "1A") == 0  # só a pasta-guia, vazia
    _foto("Escola A", "1A", PASTA_GUIA)
    _foto("Escola A", "1A", "ENVIADA - 100 - Tema")
    _foto("Escola A", "1A", "100 - Tema", "leia.txt")
    assert guia.contar_redacoes("Escola A", "1A") == 0
    _foto("Escola A", "1A", "100 - Tema", "Ana.JPG")
    _foto("Escola A", "1A", "101 - Outro", "Bia.jpeg")
    assert guia.contar_redacoes("Escola A", "1A") == 2
    assert guia.contar_redacoes("Escola B", "2A") == 0  # outra turma não entra na conta


def test_com_fotos_nao_pergunta_nada():
    _base()
    _foto("Escola A", "1A", "100 - Tema")

    def nao_pergunta(_):
        raise AssertionError("perguntou")
    assert guia.avisar_se_sem_redacoes("Escola A", "1A", nao_pergunta, lambda *_: None) == 1


def test_sem_fotos_continuar_para_o_menu_nao_mostra_a_explicacao():
    _base()
    saidas = []
    assert guia.avisar_se_sem_redacoes("Escola A", "1A", _resp("c"), saidas.append) == 0
    texto = "\n".join(saidas)
    assert "Não encontrei redações" in texto and "├──" not in texto


def test_explicacao_desenha_a_arvore_e_o_caminho_e_depois_acha_as_fotos():
    _base()
    saidas = []

    def entrada(pergunta):
        if "já colocou" in pergunta:
            _foto("Escola A", "1A", "100 - Tema")  # a pessoa colocou a foto antes de responder
            return "s"
        return "e"
    assert guia.avisar_se_sem_redacoes("Escola A", "1A", entrada, saidas.append) == 1
    texto = "\n".join(saidas)
    assert "├──" in texto and "└──" in texto and "Escola A" in texto and "1A" in texto
    assert "temas" in texto and "Encontrei 1 foto" in texto


def test_ja_coloquei_mas_nao_achou_avisa_e_deixa_tentar_de_novo_ou_continuar():
    _base()
    saidas = []
    assert guia.avisar_se_sem_redacoes("Escola A", "1A", _resp("e", "s", "t", "s", "c"), saidas.append) == 0
    assert "\n".join(saidas).count("Ainda não encontrei") == 2
    assert guia.avisar_se_sem_redacoes("Escola A", "1A", _resp("e", "n"), lambda *_: None) == 0  # "ainda não": volta ao menu


def test_menu_ao_abrir_turma_vazia_faz_a_pergunta_e_depois_a_dos_temas(monkeypatch, tmp_path):
    from modulos.dados import conciliacao_completa
    monkeypatch.setattr(conciliacao_completa, "TEMAS_SITE_CSV", tmp_path / "nao_existe.csv")
    _base()
    chamadas = []
    menu.verificar_turma_ao_abrir(("Escola A", "1A"), lambda argv: chamadas.append(argv) or 0,
                                  _resp("c", "s"), lambda *_: None)
    assert chamadas == [["--analise-remota", "--escola", "Escola A", "--turma", "1A"]]


def test_erro_ao_olhar_a_pasta_nao_derruba_o_menu(monkeypatch, tmp_path):
    from modulos.dados import conciliacao_completa
    monkeypatch.setattr(conciliacao_completa, "TEMAS_SITE_CSV", tmp_path / "nao_existe.csv")
    saidas = []
    menu.verificar_turma_ao_abrir(("Escola Que Nao Existe", "X"), lambda argv: 0, _resp("n"), saidas.append)
    assert any("Não consegui olhar a pasta" in s for s in saidas)
