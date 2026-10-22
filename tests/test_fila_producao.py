# -*- coding: utf-8 -*-
"""Testes offline da montagem do lote de produção (T24). Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.estados import EXATO_UNICO, SUGESTAO_FUZZY, AMBIGUO
from modulos.envio.fila_producao import montar_lote_producao
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.base.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, REVISAO_MANUAL, ERRO

ANA = Aluno(nome="Ana Lalara", email="ana@escola.com")
BRUNO = Aluno(nome="Bruno Silva", email="bruno@escola.com")


def _item(raiz: Path, aluno, pasta, arquivo, codigo, estado=EXATO_UNICO, criar=True):
    if criar:
        (raiz / pasta).mkdir(parents=True, exist_ok=True)
        (raiz / pasta / arquivo).write_bytes(str(raiz / pasta / arquivo).encode())
    return ItemConciliacao(pasta=pasta, arquivo=arquivo, pessoa=aluno.nome if aluno else "",
                           estado=estado, aluno=aluno, codigo_tema=codigo)


@pytest.fixture
def progresso(tmp_path):
    prog = Progresso(tmp_path / "progresso.db")
    yield prog
    prog.close()


def test_so_exato_unico_entra_com_chave_pasta_arquivo(tmp_path):
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[
        _item(raiz, ANA, "1 - Carta", "Ana Lalara - Red.jpg", "1"),
        _item(raiz, BRUNO, "1 - Carta", "Bruno - Red.jpg", "1", estado=SUGESTAO_FUZZY),
        _item(raiz, None, "1 - Carta", "Fulano - Red.jpg", "1", estado=AMBIGUO),
    ])

    lotes, ignorados = montar_lote_producao(resultado, raiz)

    assert [(lote.aluno.nome, [i.chave_progresso for i in lote.itens]) for lote in lotes] == [
        ("Ana Lalara", ["1 - Carta/Ana Lalara - Red.jpg"]),
    ]
    item = lotes[0].itens[0]
    assert item.codigo == "1"
    assert item.caminho == raiz / "1 - Carta" / "Ana Lalara - Red.jpg"
    assert ignorados == []


@pytest.mark.parametrize("estado_banco", [ENVIADO, JA_ENVIADO, REVISAO_MANUAL])
def test_nao_reenvia_o_que_o_banco_ja_registrou(tmp_path, progresso, estado_banco):
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[_item(raiz, ANA, "1 - Carta", "a.jpg", "1")])
    progresso.marcar(ANA.id, "1 - Carta/a.jpg", estado_banco, pasta="1")

    lotes, ignorados = montar_lote_producao(resultado, raiz, progresso)

    assert lotes == []
    assert ignorados == [("1 - Carta/a.jpg", f"ja registrado como {estado_banco}")]


def test_erro_anterior_pode_tentar_de_novo(tmp_path, progresso):
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[_item(raiz, ANA, "1 - Carta", "a.jpg", "1")])
    progresso.marcar(ANA.id, "1 - Carta/a.jpg", ERRO, pasta="1")

    lotes, _ = montar_lote_producao(resultado, raiz, progresso)

    assert [i.arquivo for i in lotes[0].itens] == ["a.jpg"]


def test_sem_limite_de_redacoes_por_aluno(tmp_path):
    """Antônio, 22/10: não há limite por aluno (antes eram 4 por execução)."""
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[
        _item(raiz, ANA, f"{n} - Tema", "a.jpg", str(n)) for n in range(1, 7)
    ])

    lotes, ignorados = montar_lote_producao(resultado, raiz)

    assert [i.codigo for i in lotes[0].itens] == ["1", "2", "3", "4", "5", "6"]
    assert ignorados == []


def test_codigo_repetido_arquivo_inexistente_e_sem_codigo_ficam_fora(tmp_path):
    """T35: mesmo código em pasta diferente agora ENTRA (tema genérico);
    repetido na MESMA pasta fica fora."""
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[
        _item(raiz, ANA, "1 - Carta", "a.jpg", "1"),
        _item(raiz, ANA, "1 - Carta", "b.jpg", "1"),
        _item(raiz, ANA, "2 - Tema", "c.jpg", "2", criar=False),
        _item(raiz, ANA, "Sem codigo", "d.jpg", ""),
    ])

    lotes, ignorados = montar_lote_producao(resultado, raiz)

    assert [i.chave_progresso for i in lotes[0].itens] == ["1 - Carta/a.jpg"]
    assert sorted(ignorados) == sorted([
        ("1 - Carta/b.jpg", "codigo 1 repetido para o aluno na mesma pasta (revisao manual)"),
        ("2 - Tema/c.jpg", "arquivo nao encontrado"),
        ("Sem codigo/d.jpg", "sem codigo de tema (revisao manual)"),
    ])


def test_limite_de_alunos_e_de_redacoes(tmp_path):
    raiz = tmp_path / "pend"
    resultado = ResultadoConciliacao(itens=[
        _item(raiz, ANA, "1 - A", "a1.jpg", "1"),
        _item(raiz, ANA, "2 - A", "a2.jpg", "2"),
        _item(raiz, BRUNO, "1 - B", "b1.jpg", "1"),
        _item(raiz, BRUNO, "2 - B", "b2.jpg", "2"),
    ])

    lotes, _ = montar_lote_producao(resultado, raiz, limite_alunos=1)
    assert [(lote.aluno.nome, len(lote.itens)) for lote in lotes] == [("Ana Lalara", 2)]

    lotes, _ = montar_lote_producao(resultado, raiz, limite_redacoes=3)
    assert [(lote.aluno.nome, len(lote.itens)) for lote in lotes] == [("Ana Lalara", 2), ("Bruno Silva", 1)]

    lotes, _ = montar_lote_producao(resultado, raiz, limite_alunos=1, limite_redacoes=1)
    assert [(lote.aluno.nome, len(lote.itens)) for lote in lotes] == [("Ana Lalara", 1)]
