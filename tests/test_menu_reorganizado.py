# -*- coding: utf-8 -*-
"""Issue #53: menu em Preparar / Enviar / Manutenção / Ferramentas e Enviar travado até a conferência de hoje."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import relogio
from modulos.base.turma import raiz_redacoes
from modulos.ferramentas import menu
from modulos.ferramentas.assistente_inicial import executar_assistente
from modulos.site import conferencia_site as cs

TURMA = ("Escola A", "1A")
DA_TURMA = ["--escola", "Escola A", "--turma", "1A"]


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _base():
    executar_assistente(_resp("s", "2", "2", "Escola A", "1", "1A", "Escola B", "1", "2A"))


def _conferencia(resultados, turma="Escola A/1A", dia=None):
    """Relatório de conferência no site (como o gravar_csv escreve) na pasta relatorios da turma 1A."""
    pasta = raiz_redacoes() / "Escola A" / "1A" / "relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    dia = dia or relogio.agora().strftime("%Y%m%d")
    with open(pasta / f"conferencia_site_{dia}_100000.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cs.COLUNAS_CSV)
        for i, r in enumerate(resultados):
            w.writerow([f"Aluno {i}", "100 - Tema", f"Aluno {i}.jpg", "100", r, 0, "", "", turma])


def _menu_texto(turma=TURMA):
    saidas = []
    menu.mostrar_menu(saidas.append, turma)
    return "\n".join(saidas)


def test_grupos_e_ordem_do_menu_e_toda_tecla_tem_uma_acao():
    grupos = []
    for grupo, *_ in menu.OPCOES:
        if grupo not in grupos:
            grupos.append(grupo)
    assert grupos == ["Preparar", "Enviar", "Manutenção", "Ferramentas"]
    teclas = [t for _, t, *_ in menu.OPCOES]
    assert teclas == [str(i) for i in range(1, len(teclas) + 1)]  # 1..13, sem buraco nem repetição
    nomes = {t: n for _, t, _, n, _ in menu.OPCOES}
    assert nomes["3"] == "Conferir contas no site" and nomes["4"] == "Enviar para os alunos"
    assert menu.ACAO_DA_TECLA["3"] == "5" and menu.ACAO_DA_TECLA["13"] == "T"
    assert not any("Ensaio" in n or "Modo teste" in n for _, _, _, n, _ in menu.OPCOES)  # saíram do menu principal


def test_preparacao_concluida_so_com_a_conferencia_de_hoje_completa_da_mesma_turma():
    _base()
    pasta = raiz_redacoes() / "Escola A" / "1A" / "relatorios"
    assert cs.preparacao_concluida(pasta, "Escola A/1A")[0] is False  # nenhuma conferência
    _conferencia([cs.NO_SITE, cs.FORA_DO_SITE], dia="20200101")
    assert "hoje" in cs.preparacao_concluida(pasta, "Escola A/1A")[1]  # de outro dia
    _conferencia([cs.NO_SITE, cs.FORA_DO_SITE, cs.OUTRO_TEMA])
    assert cs.preparacao_concluida(pasta, "Escola A/1A") == (True, "")
    assert cs.preparacao_concluida(pasta, "Escola B/2A")[0] is False  # relatório de outra turma
    _conferencia([cs.NO_SITE, cs.NAO_CONFERIDO])
    ok, motivo = cs.preparacao_concluida(pasta, "Escola A/1A")
    assert not ok and "1 redação" in motivo
    _conferencia([cs.NO_SITE, cs.NAO_TENTADO])
    assert cs.preparacao_concluida(pasta, "Escola A/1A")[0] is False
    _conferencia([])
    assert cs.preparacao_concluida(pasta, "Escola A/1A")[0] is False


def test_menu_sem_preparar_mostra_enviar_travado_e_com_a_conferencia_de_hoje_libera(monkeypatch):
    _base()
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    travado = _menu_texto()
    assert travado.count("falta conferir as contas no site hoje") == 2  # Enviar e Enviar as que faltam, com o motivo
    assert "Enviar para os alunos" in travado and "Enviar as que faltam" in travado
    _conferencia([cs.NO_SITE, cs.FORA_DO_SITE])
    assert "bloqueado" not in _menu_texto()
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)  # a trava da produção continua valendo por cima
    assert "só a conta de teste envia" in _menu_texto()


def test_enviar_recusa_sem_preparar_e_so_abre_depois_nao_apenas_na_cor(monkeypatch):
    _base()
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    chamadas, saidas = [], []
    r = _resp("4", "", "5", "", "0")  # Enviar e Enviar as que faltam, os dois recusados
    menu.executar_menu(lambda argv: chamadas.append(argv) or 0, r, saidas.append, turma=TURMA)
    assert chamadas == [] and "Enviar bloqueado" in "\n".join(saidas)
    _conferencia([cs.NO_SITE, cs.FORA_DO_SITE])
    chamadas.clear()
    r = _resp("5", "", "0")
    menu.executar_menu(lambda argv: chamadas.append(argv) or 0, r, saidas.append, turma=TURMA)
    assert chamadas == [["--enviar-faltantes"] + DA_TURMA]


def test_testes_ficam_num_submenu_das_ferramentas_e_o_modo_teste_nao_leva_turma():
    chamadas = []
    # 13 Testes > 1 Ensaio (3 redações, só mostrar) ; 13 > 2 Modo teste (só conferir) ; 13 > Enter (volta)
    r = _resp("13", "1", "3", "n", "", "13", "2", "", "", "13", "", "", "0")
    menu.executar_menu(lambda argv: chamadas.append(argv) or 0, r, lambda *_: None, turma=TURMA)
    assert chamadas == [["--ensaio", "3"] + DA_TURMA, ["--modo-teste"]]


def test_manutencao_aponta_para_as_mesmas_acoes_de_antes():
    for tecla, esperado in (("6", ["--resolver"]), ("7", ["--analise-remota"]), ("10", ["--arquivar"]),
                            ("12", ["--preparar"]), ("1", []), ("2", ["--revisar"]), ("3", ["--conferir-site"])):
        assert menu.argumentos_da_opcao(menu.ACAO_DA_TECLA[tecla], _resp(), saida=lambda *_: None) == esperado
