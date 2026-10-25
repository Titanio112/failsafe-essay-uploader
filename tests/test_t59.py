# -*- coding: utf-8 -*-
"""Testes offline da T59: ao aprovar o tema, a pasta ganha o nome do tema do site."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.progresso_relatorio import ENVIADO, Progresso
from modulos.dados.planilha_arquivos import Aluno
from modulos.dados.sugestao_temas import carregar_codigos_pasta
from modulos.ferramentas.revisao_interativa import (
    desfazer_renomeacoes, nome_pasta_para, pasta_travada, renomear, renomear_pasta, revisar_pastas,
)

TEMA = "53- Impactos da evasão escolar para o Brasil"
TEMAS = [("53", TEMA), ("000", "000- DISSERTATIVO ARGUMENTATIVO")]
NADA = lambda *_: None  # noqa: E731


def _pasta(tmp_path, nome="3-B - impactos da evasao escolar", fotos=("Ana Souza.jpg",)):
    pasta = tmp_path / "redacoes" / nome
    pasta.mkdir(parents=True)
    for f in fotos:
        (pasta / f).write_bytes(f.encode())
    return pasta.parent


def test_nome_da_pasta_vem_do_tema_do_site():
    assert nome_pasta_para("53", TEMA) == "53 - Impactos da evasão escolar para o Brasil"
    assert nome_pasta_para("7", '7- Tema: "a/b"?') == "7 - Tema ab"
    longo = nome_pasta_para("9", "9- " + "palavra " * 30)
    assert len(longo) <= 85 and not longo.endswith(" ")


def test_aprovar_renomeia_a_pasta_e_grava_o_log(tmp_path):
    raiz = _pasta(tmp_path)
    renomeadas = {}
    aprovadas, _ = revisar_pastas(["3-B - impactos da evasao escolar"], TEMAS, tmp_path / "pastas.csv",
                                  entrada=lambda _: "", saida=NADA, pasta_raiz=raiz, banco=tmp_path / "p.db",
                                  log_csv=tmp_path / "log.csv", renomeadas=renomeadas)
    assert aprovadas == 1
    assert renomeadas == {"3-B - impactos da evasao escolar": "53 - Impactos da evasão escolar para o Brasil"}
    assert [p.name for p in raiz.iterdir()] == ["53 - Impactos da evasão escolar para o Brasil"]
    assert not (tmp_path / "pastas.csv").exists()  # o código está no nome: o CSV não é preciso
    assert "3-B - impactos da evasao escolar" in (tmp_path / "log.csv").read_text(encoding="utf-8-sig")


def test_pasta_com_redacao_no_caderno_nao_e_renomeada_e_vai_para_o_csv(tmp_path):
    raiz = _pasta(tmp_path, nome="3_B Evasao")
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar("ana@x.com", "3_B Evasao/Ana Souza.jpg", ENVIADO, pasta="53")
    assert pasta_travada(tmp_path / "p.db", "3_B Evasao") == ENVIADO
    assert pasta_travada(tmp_path / "p.db", "3_B") == ""  # "_" não é curinga
    aprovadas, _ = revisar_pastas(["3_B Evasao"], TEMAS, tmp_path / "pastas.csv", entrada=lambda _: "53",
                                  saida=NADA, pasta_raiz=raiz, banco=tmp_path / "p.db",
                                  log_csv=tmp_path / "log.csv", renomeadas={})
    assert aprovadas == 1
    assert (raiz / "3_B Evasao").is_dir()
    assert carregar_codigos_pasta(tmp_path / "pastas.csv") == {"3_B Evasao": "53"}


def test_nome_ja_existente_nao_e_sobrescrito(tmp_path):
    raiz = _pasta(tmp_path)
    (raiz / "53 - Impactos da evasão escolar para o Brasil").mkdir()
    novo, motivo = renomear_pasta(raiz, "3-B - impactos da evasao escolar", "53", TEMA, None, tmp_path / "l.csv")
    assert novo == "" and "ja existe" in motivo


@pytest.mark.skipif(sys.platform != "win32", reason="só o Windows trava arquivo aberto")
def test_foto_aberta_nao_renomeia_e_vai_para_o_csv(tmp_path):
    raiz = _pasta(tmp_path)
    with open(raiz / "3-B - impactos da evasao escolar" / "Ana Souza.jpg", "rb"):
        revisar_pastas(["3-B - impactos da evasao escolar"], TEMAS, tmp_path / "pastas.csv",
                       entrada=lambda _: "", saida=NADA, pasta_raiz=raiz, log_csv=tmp_path / "log.csv")
    assert (raiz / "3-B - impactos da evasao escolar").is_dir()
    assert carregar_codigos_pasta(tmp_path / "pastas.csv") == {"3-B - impactos da evasao escolar": "53"}


def test_desfazer_volta_o_arquivo_e_depois_a_pasta(tmp_path):
    raiz = _pasta(tmp_path, fotos=("ana.jpg",))
    log = tmp_path / "log.csv"
    nova, _ = renomear_pasta(raiz, "3-B - impactos da evasao escolar", "53", TEMA, None, log)
    novo, _ = renomear(raiz, nova, "ana.jpg", Aluno("Ana Souza", "ana@x.com"), tmp_path / "p.db", log)
    assert (raiz / nova / novo).is_file()
    assert desfazer_renomeacoes(log, raiz, saida=NADA) == 2
    assert (raiz / "3-B - impactos da evasao escolar" / "ana.jpg").is_file()


def test_desfazer_nao_volta_pasta_com_redacao_no_caderno_pelo_nome_novo(tmp_path):
    raiz = _pasta(tmp_path)
    log = tmp_path / "log.csv"
    nova, _ = renomear_pasta(raiz, "3-B - impactos da evasao escolar", "53", TEMA, None, log)
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar("ana@x.com", f"{nova}/Ana Souza.jpg", ENVIADO, pasta="53")
    assert desfazer_renomeacoes(log, raiz, saida=NADA, banco=tmp_path / "p.db") == 0
    assert (raiz / nova).is_dir()
