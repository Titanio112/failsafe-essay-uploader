# -*- coding: utf-8 -*-
"""Testes offline da T26: lista de alunos em CSV, nomes aprovados por humano,
sugestão de código de tema. Sem navegador, sem dados reais."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config, RAIZ
from modulos.base.estados import EXATO_UNICO
from modulos.dados.nomes_aprovados import carregar_nomes_aprovados, registrar_sugestoes
from modulos.dados.planilha_arquivos import Aluno, PlanilhaError, carregar_alunos, conciliar
from modulos.dados.sugestao_temas import sugerir_codigos

ANA = Aluno(nome="Ana Lalara Larili dos Larito", email="ana@escola.com")
ANA_M = Aluno(nome="Ana Lalara Larisa", email="anam@escola.com")
ISA = Aluno(nome="Isabela Laruli Lapera", email="isa@escola.com")
ALUNOS = [ANA, ANA_M, ISA]


def _csv(caminho: Path, linhas: list[list[str]], sep: str = ";") -> Path:
    caminho.write_text("﻿" + "\n".join(sep.join(l) for l in linhas) + "\n", encoding="utf-8")
    return caminho


# ---- R1: lista de alunos em CSV ----

@pytest.mark.raiz_real
def test_padrao_e_dados_alunos_csv():
    assert Config().planilha == RAIZ / "dados" / "dados_alunos.csv"


@pytest.mark.parametrize("sep", [";", ","])
def test_csv_com_senha_le_nome_email_e_ignora_senha(tmp_path, sep):
    cfg = Config()
    cfg.planilha = _csv(tmp_path / "dados_alunos.csv", [
        ["Nome", "Email", "Senha"],
        ["Ana Lalara Larili dos Larito", "ana@escola.com", "segredo123"],
        ["", "sem-nome@escola.com", "x"],
        ["Isabela Laruli Lapera", "isa@escola.com", ""],
    ], sep)

    with pytest.warns(UserWarning, match="Senha"):
        alunos = carregar_alunos(cfg)

    assert alunos == [ANA, ISA]
    assert "segredo123" not in repr(alunos)


def test_csv_sem_colunas_obrigatorias_da_erro_claro(tmp_path):
    cfg = Config()
    cfg.planilha = _csv(tmp_path / "x.csv", [["Aluno", "Contato"], ["Ana", "a@x.com"]])
    with pytest.raises(PlanilhaError, match="Colunas encontradas"):
        carregar_alunos(cfg)


# ---- R2: nomes aprovados por humano ----

def _arquivos():
    return {"100 - Filiacao": ["Ana Lalara Larili.JPG", "Ana Lalara.JPG", "Isabela Larulii.JPG",
                               "Isabela em branco.JPG"]}


def test_sem_aprovacao_nome_curto_nao_entra_na_fila():
    resultado = conciliar(ALUNOS, _arquivos(), codigos_site=set())
    assert resultado.fila_validada() == []


def test_sugestoes_gravadas_sem_aprovar_nada(tmp_path):
    caminho = tmp_path / "nomes_aprovados.csv"
    resultado = conciliar(ALUNOS, _arquivos(), codigos_site=set())

    novas = registrar_sugestoes(resultado, ALUNOS, caminho)

    linhas = list(csv.DictReader(open(caminho, encoding="utf-8-sig"), delimiter=";"))
    por_nome = {}
    for linha in linhas:
        por_nome.setdefault(linha["nome_no_arquivo"], []).append(linha)
    assert novas == len(linhas)
    assert all(linha["aprovado"] == "" for linha in linhas)
    # "Ana Lalara Larili" cabe só na Ana Lalara Larili dos Larito
    assert [(l["aluno_email"], l["motivo"]) for l in por_nome["Ana Lalara Larili"]] == [("ana@escola.com", "nome parcial")]
    # "Ana Lalara" cabe nas duas -> as duas sugeridas, humano escolhe
    assert {l["aluno_email"] for l in por_nome["Ana Lalara"]} == {"ana@escola.com", "anam@escola.com"}
    # Erro de digitação -> sugestão por semelhança
    assert por_nome["Isabela Larulii"][0]["aluno_email"] == "isa@escola.com"
    assert por_nome["Isabela Larulii"][0]["motivo"].startswith("parecido")

    # Folha "em branco" nunca vira sugestão
    assert not any("branco" in nome.lower() for nome in por_nome)
    # Rodar de novo não duplica nem apaga
    assert registrar_sugestoes(resultado, ALUNOS, caminho) == 0
    assert len(list(csv.DictReader(open(caminho, encoding="utf-8-sig"), delimiter=";"))) == len(linhas)


def test_nome_aprovado_entra_na_fila_como_exato(tmp_path):
    caminho = _csv(tmp_path / "nomes_aprovados.csv", [
        ["nome_no_arquivo", "aluno_nome", "aluno_email", "aprovado", "motivo"],
        ["Ana Lalara Larili", ANA.nome, ANA.email, "sim", "nome parcial"],
        ["Isabela Larulii", ISA.nome, ISA.email, "", "parecido 90%"],
    ])

    aprovados = carregar_nomes_aprovados(caminho, ALUNOS)
    resultado = conciliar(ALUNOS, _arquivos(), codigos_site=set(), nomes_aprovados=aprovados)
    estados = {i.arquivo: (i.estado, i.aluno.email if i.aluno else None) for i in resultado.itens if i.arquivo}

    assert estados["Ana Lalara Larili.JPG"] == (EXATO_UNICO, ANA.email)
    assert estados["Isabela Larulii.JPG"][0] != EXATO_UNICO  # sugerido, mas não aprovado
    assert [i.arquivo for i in resultado.fila_validada()] == ["Ana Lalara Larili.JPG"]


def test_aprovacao_com_email_fora_da_lista_ou_em_conflito_e_ignorada(tmp_path):
    caminho = _csv(tmp_path / "nomes_aprovados.csv", [
        ["nome_no_arquivo", "aluno_nome", "aluno_email", "aprovado", "motivo"],
        ["Fulano", "Fulano", "fulano@fora.com", "sim", ""],
        ["Ana Lalara", ANA.nome, ANA.email, "sim", ""],
        ["Ana Lalara", ANA_M.nome, ANA_M.email, "sim", ""],
    ])

    with pytest.warns(UserWarning):
        aprovados = carregar_nomes_aprovados(caminho, ALUNOS)

    assert aprovados == {}


# ---- R3: sugestão de código para pasta sem código ----

TEMAS = [
    ("100", "100- Impactos da invisibilidade de filiação para os cidadãos brasileiros"),
    ("9", "9- Expectativa de vida e a inversão da pirâmide etária"),
]


def test_sugere_codigo_so_para_pasta_sem_codigo():
    sugestoes = sugerir_codigos([
        "3B - Impacatos da Invisibilidade da filiação para o cidadão brasileiro",
        "100 - Ja tem codigo",
        "3B - Tema que nao existe no site",
    ], TEMAS)

    assert [(p[:12], c) for p, c, _, _ in sugestoes] == [("3B - Impacat", "100"), ("3B - Tema qu", "")]
    assert sugestoes[0][3] >= 85
