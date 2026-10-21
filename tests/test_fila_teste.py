# -*- coding: utf-8 -*-
"""Testes offline da montagem da fila do modo teste (T21)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.fila_teste import montar_fila_teste


def _criar(raiz: Path, arquivos: dict[str, list[str]]) -> dict[str, list[str]]:
    for pasta, nomes in arquivos.items():
        (raiz / pasta).mkdir(parents=True, exist_ok=True)
        for nome in nomes:
            (raiz / pasta / nome).write_bytes(b"jpg-falso")
    return arquivos


def test_layout_da_pasta_de_teste(tmp_path):
    """Mesmo layout de testes/redacoes_teste: 0 (5), 00 (2), 000 (1)."""
    arquivos = _criar(tmp_path, {
        "0": ["01Usuario Testes Ignorar.jpg", "02Usuario Testes .jpg",
              "03Usuario Testes Ignorar.jpg", "04Usuario Testes Ignorar.jpg",
              "05Usuario Testes Ignorar.jpg"],
        "00": ["004Usuario Ignorar.jpg", "005Usuario Ignorar.jpg"],
        "000": ["0001Usuario Testes Ignorar.jpg"],
    })

    fila, ignorados = montar_fila_teste(tmp_path, arquivos)

    assert [(i.codigo, i.arquivo) for i in fila] == [
        ("0", "01Usuario Testes Ignorar.jpg"),
        ("00", "004Usuario Ignorar.jpg"),
        ("000", "0001Usuario Testes Ignorar.jpg"),
    ]
    assert fila[0].caminho == tmp_path / "0" / "01Usuario Testes Ignorar.jpg"
    # 4 extras do tema 0 + 1 extra do tema 00 ficam fora
    assert len(ignorados) == 5
    assert all("repetido" in motivo for _, motivo in ignorados)


def test_pasta_sem_codigo_fica_fora(tmp_path):
    arquivos = _criar(tmp_path, {"3B Turma": ["redacao.jpg"], "1 - Carta": ["a.jpg"]})

    fila, ignorados = montar_fila_teste(tmp_path, arquivos)

    assert [i.codigo for i in fila] == ["1"]
    assert ignorados == [("3B Turma/redacao.jpg", "sem codigo de tema (revisao manual)")]


def test_arquivo_inexistente_fica_fora_e_proximo_do_codigo_entra(tmp_path):
    arquivos = _criar(tmp_path, {"0": ["b.jpg"]})
    arquivos = {"0": ["a.jpg", "b.jpg"]}  # a.jpg não existe no disco

    fila, ignorados = montar_fila_teste(tmp_path, arquivos)

    assert [i.arquivo for i in fila] == ["b.jpg"]
    assert ignorados == [("0/a.jpg", "arquivo nao encontrado")]


def test_codigos_sao_strings_distintas(tmp_path):
    arquivos = _criar(tmp_path, {"0": ["x.jpg"], "00": ["y.jpg"], "000": ["z.jpg"]})

    fila, ignorados = montar_fila_teste(tmp_path, arquivos)

    assert [i.codigo for i in fila] == ["0", "00", "000"]
    assert ignorados == []
