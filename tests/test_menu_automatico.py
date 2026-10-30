# -*- coding: utf-8 -*-
"""Menu sem comandos: "n" cria escola/turma na própria escolha e a turma sem temas oferece lê-los. RAIZ temporária."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.turma import aplicar_turma, listar_escolas, listar_turmas
from modulos.ferramentas import menu
from modulos.ferramentas.assistente_inicial import executar_assistente

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _base():
    executar_assistente(_resp("s", "2", "2", "Escola A", "1", "1A", "Escola B", "1", "2A"))


def test_n_na_escolha_de_escola_cria_escola_e_volta_para_a_lista():
    _base()
    # n -> e (nova escola) -> nome, 1 turma, nome; volta à lista (3 escolas): escolhe a 3ª, turma 1, usa
    r = _resp("n", "e", "Escola C", "1", "3A", "3", "1", "s")
    assert menu.escolher_turma(r, lambda *_: None) == ("Escola C", "3A")
    assert listar_escolas() == ["Escola A", "Escola B", "Escola C"]


def test_n_nova_turma_numa_escola_existente():
    _base()
    r = _resp("n", "t", "1", "1B", "1", "2", "s")  # n, t, Escola A, nome; depois Escola A, 2ª turma
    assert menu.escolher_turma(r, lambda *_: None) == ("Escola A", "1B")
    assert listar_turmas("Escola A") == ["1A", "1B"] and listar_turmas("Escola B") == ["2A"]


def test_n_cancelado_nao_cria_nada_e_volta_a_pedir_a_escola():
    _base()
    r = _resp("n", "", "n", "e", "", "")  # n + Enter; n, e, nome vazio; Enter = cancelar a escolha
    assert menu.escolher_turma(r, lambda *_: None) is None
    assert listar_escolas() == ["Escola A", "Escola B"]


def test_turma_sem_lista_de_temas_oferece_ler_e_so_chama_o_mesmo_caminho_do_menu_9():
    _base()
    chamadas = []
    assert menu.oferecer_temas(("Escola A", "1A"), lambda argv: chamadas.append(argv) or 0, _resp("s"), lambda *_: None)
    assert chamadas == [["--analise-remota", "--escola", "Escola A", "--turma", "1A"]]  # o ANALISAR é do main
    chamadas.clear()
    assert not menu.oferecer_temas(("Escola A", "1A"), lambda argv: chamadas.append(argv) or 0, _resp("n"),
                                   lambda *_: None)
    assert chamadas == []


def test_turma_com_lista_de_temas_nao_pergunta_nada():
    _base()
    cfg = config_mod.carregar_config()
    aplicar_turma(cfg, "Escola A", "1A")
    cfg.temas_site.parent.mkdir(parents=True, exist_ok=True)
    cfg.temas_site.write_text("codigo,texto,data_leitura,conta_mascarada\n", encoding="utf-8")

    def nao_pergunta(_):
        raise AssertionError("perguntou")
    assert not menu.oferecer_temas(("Escola A", "1A"), lambda argv: 0, nao_pergunta, lambda *_: None)


def test_atalhos_do_windows_rodam_de_qualquer_pasta_e_nao_valem_copiados():
    bat = (RAIZ_PROJETO / "AutoReda.bat").read_bytes()
    assert b"\r\n" in bat and bat.isascii()
    texto = bat.decode("ascii")
    assert 'cd /d "%~dp0"' in texto  # entra na pasta do projeto, não importa de onde foi aberto
    assert 'if not exist "main.py"' in texto  # cópia solta (ex.: Área de Trabalho) avisa em vez de falhar calada
    criador = (RAIZ_PROJETO / "Criar atalho AutoReda.bat").read_bytes()
    assert criador.isascii() and b"AutoReda.lnk" in criador and b"WorkingDirectory" in criador
