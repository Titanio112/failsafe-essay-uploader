# -*- coding: utf-8 -*-
"""Issue #34: primeiro uso guiado. RAIZ temporária (conftest); sem navegador, sem site."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.turma import PASTA_GUIA, listar_escolas, listar_turmas, raiz_redacoes
from modulos.dados.planilha_arquivos import carregar_alunos, descobrir_pastas
from modulos.ferramentas.assistente_inicial import executar_assistente


def _rodar(*respostas):
    it = iter(respostas)
    return executar_assistente(lambda _: next(it))


def test_sim_sim_cria_duas_escolas_com_um_leiame_por_escola_e_a_pasta_guia():
    assert _rodar("sim", "sim", "2", "Escola A", "2", "1A", "1B", "Escola B", "1", "2A")
    raiz = raiz_redacoes()
    assert listar_escolas() == ["Escola A", "Escola B"]
    assert listar_turmas("Escola A") == ["1A", "1B"] and listar_turmas("Escola B") == ["2A"]
    assert sorted(p.relative_to(raiz).as_posix() for p in raiz.rglob("LEIA-ME.md")) == ["Escola A/LEIA-ME.md",
                                                                                         "Escola B/LEIA-ME.md"]
    assert (raiz / "Escola A" / "1B" / "temas" / PASTA_GUIA).is_dir()
    assert (raiz / "Escola B" / "2A" / "alunos.csv").read_text(encoding="utf-8") == "Nome;Email;Senha\n"


def test_nao_cria_so_a_escola_de_exemplo_sem_senha():
    assert _rodar("s", "n")
    assert listar_escolas() == ["Escola Teste"]
    pasta = raiz_redacoes() / "Escola Teste" / "Turma Exemplo"
    assert (pasta / "temas" / PASTA_GUIA).is_dir()
    from modulos.base.config import Config
    from modulos.base.turma import aplicar_turma
    cfg = Config()
    aplicar_turma(cfg, "Escola Teste", "Turma Exemplo")
    assert [a.senha for a in carregar_alunos(cfg)] == [""]  # sem senha: nunca entra no site
    assert descobrir_pastas(cfg) == []  # a pasta-guia não conta como tema


def test_nome_repetido_ou_invalido_pergunta_de_novo():
    assert _rodar("sim", "sim", "2", "Escola A", "1", "1A", "../x", "escola a", "Escola B", "1", "1A")
    assert listar_escolas() == ["Escola A", "Escola B"]


def test_nao_na_primeira_vez_ou_cancelar_nao_cria_nada():
    assert not _rodar("nao")
    assert not _rodar("sim", "sim", "2", "Escola A", "")  # Enter em vez do nº de turmas
    assert not raiz_redacoes().exists() or not list(raiz_redacoes().iterdir())
