# -*- coding: utf-8 -*-
"""Testes offline: salas nunca existiram no projeto (T23). Sem navegador."""

from __future__ import annotations

import dataclasses
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config, _ler_ini
from modulos.base.estados import EXATO_UNICO
from modulos.dados.planilha_arquivos import (
    Aluno,
    ItemConciliacao,
    ResultadoConciliacao,
    carregar_alunos,
)
from modulos.base.progresso_relatorio import gerar_fila_dry_run, gerar_relatorio_conciliacao

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def test_codigo_nao_menciona_sala():
    """Nenhum .py de modulos/ nem o main.py usa a palavra "sala"."""
    padrao = re.compile(r"\bsalas?\b", re.IGNORECASE)
    achados = []
    for arquivo in sorted((RAIZ_PROJETO / "modulos").rglob("*.py")) + [RAIZ_PROJETO / "main.py"]:
        for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
            if padrao.search(linha):
                achados.append(f"{arquivo.name}:{n}: {linha.strip()}")
    assert achados == []


def test_aluno_so_tem_nome_email_creditos():
    assert [f.name for f in dataclasses.fields(Aluno)] == ["nome", "email", "creditos"]


def test_config_ini_com_secao_planilha_nao_quebra(tmp_path):
    """Antes da T23: AttributeError 'Config' object has no attribute 'coluna_sala'."""
    ini = tmp_path / "config.ini"
    ini.write_text("[planilha]\naba = Alunos\ncoluna_nome = nome\n", encoding="utf-8")

    cfg = _ler_ini(ini)

    assert cfg.aba_planilha == "Alunos"
    assert not hasattr(cfg, "coluna_sala")


def test_planilha_com_coluna_extra_e_lida_e_coluna_ignorada(tmp_path):
    """Uma planilha real com colunas a mais (qualquer nome) continua sendo lida."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["nome", "email", "sala", "turno"])
    ws.append(["Ana Lalara", "ana@escola.com", "A", "manhã"])
    ws.append(["Bruno Silva", "bruno@escola.com", "", ""])
    caminho = tmp_path / "alunos.xlsx"
    wb.save(caminho)

    cfg = Config()
    cfg.planilha = caminho
    cfg.aba_planilha = "Alunos"

    alunos = carregar_alunos(cfg)

    assert alunos == [
        Aluno(nome="Ana Lalara", email="ana@escola.com"),
        Aluno(nome="Bruno Silva", email="bruno@escola.com"),
    ]


def test_relatorios_sem_sala(tmp_path):
    aluno = Aluno(nome="Ana Lalara", email="ana@escola.com")
    resultado = ResultadoConciliacao(itens=[
        ItemConciliacao(pasta="0", arquivo="Ana Lalara - Red.jpg", pessoa="Ana Lalara",
                        estado=EXATO_UNICO, aluno=aluno),
    ])

    csv_txt = gerar_relatorio_conciliacao(resultado, tmp_path / "r.csv").read_text(encoding="utf-8-sig")
    fila_txt = gerar_fila_dry_run(resultado, tmp_path / "f.txt").read_text(encoding="utf-8")

    assert "sala" not in csv_txt.splitlines()[0].split(",")
    linha_fila = fila_txt.splitlines()[-1]
    assert linha_fila.startswith("Ana Lalara <")
    assert "<- 0/Ana Lalara - Red.jpg" in linha_fila
