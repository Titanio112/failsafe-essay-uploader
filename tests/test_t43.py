# -*- coding: utf-8 -*-
"""Testes offline da T43: nomes e arquivos como chegam de verdade
(página 2, cópia do Windows, Excel, Mac, subpasta). Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO, REVISAO_MANUAL
from modulos.base.progresso_relatorio import ENVIADO, Progresso
from modulos.dados.nomes_aprovados import registrar_sugestoes
from modulos.dados.planilha_arquivos import Aluno, carregar_alunos, conciliar, descobrir_arquivos
from modulos.dados.sugestao_temas import carregar_codigos_pasta, registrar_sugestoes_pasta
from modulos.ferramentas.revisao_interativa import desfazer_renomeacoes, estado_travado, renomear

ANA = Aluno(nome="Ana Souza", email="ana@x.com")
BRUNO = Aluno(nome="Bruno Lima", email="bruno@x.com")


def _estados(resultado):
    return {i.arquivo: i.estado for i in resultado.itens if i.arquivo}


# ─── Conciliação ─────────────────────────────────────────────

def test_numero_no_arquivo_numa_pasta_sem_tema_nao_vira_tema():
    """"1 Ana Souza.jpg" numa pasta "3B - X" é página, não o tema 1."""
    resultado = conciliar([ANA], {"3B - X": ["1 Ana Souza.jpg"]}, codigos_site=["1", "000"])
    item = next(i for i in resultado.itens if i.arquivo)
    assert item.estado == REVISAO_MANUAL
    assert "pagina?" in item.observacao


def test_numero_no_arquivo_igual_ao_da_pasta_continua_valendo():
    resultado = conciliar([ANA], {"100 - Tema": ["100 - Ana Souza.jpg"]}, codigos_site=["100"])
    assert _estados(resultado) == {"100 - Ana Souza.jpg": EXATO_UNICO}


@pytest.mark.parametrize("segunda", ["Ana Souza 2.jpg", "Ana Souza (2).jpg"])
def test_pagina_2_ou_copia_manda_as_duas_para_revisao(segunda):
    resultado = conciliar([ANA], {"100 - Tema": ["Ana Souza.jpg", segunda]}, codigos_site=["100"])
    assert set(_estados(resultado).values()) == {REVISAO_MANUAL}
    assert all("mais de um arquivo" in i.observacao for i in resultado.itens if i.arquivo)


def test_so_a_copia_numerada_identifica_o_aluno_mas_vai_para_revisao():
    """T48: sozinho pode ser só a página 2 (a 1ª com o nome errado)."""
    resultado = conciliar([ANA], {"100 - Tema": ["Ana Souza (2).jpg"]}, codigos_site=["100"])
    item = next(i for i in resultado.itens if i.arquivo)
    assert (item.estado, item.aluno) == (REVISAO_MANUAL, ANA)
    assert "numero no fim do nome" in item.observacao


def test_sublinhado_do_celular_separa_palavras():
    resultado = conciliar([ANA], {"100 - Tema": ["100_Ana_Souza.jpg"]}, codigos_site=["100"])
    assert _estados(resultado) == {"100_Ana_Souza.jpg": EXATO_UNICO}


# ─── Descoberta de arquivos ──────────────────────────────────

def test_arquivos_do_sistema_somem_e_subpasta_avisa(tmp_path, capsys):
    tema = tmp_path / "100 - Tema"
    (tema / "Turma A").mkdir(parents=True)
    for nome in ("Ana Souza.jpg", "._Bruno Lima.jpg", "~$rascunho.jpg", "Thumbs.db", "desktop.ini"):
        (tema / nome).write_bytes(b"x")
    (tema / "Turma A" / "Bruno Lima.jpg").write_bytes(b"x")
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    with pytest.warns(UserWarning):
        assert descobrir_arquivos(cfg) == {"100 - Tema": ["Ana Souza.jpg"]}
    saida = capsys.readouterr().out
    assert "Subpasta ignorada: 100 - Tema/Turma A" in saida
    assert "Thumbs" not in saida and "desktop" not in saida


# ─── CSV vindo do Excel / Bloco de Notas ─────────────────────

def _cfg_lista(tmp_path, conteudo: bytes):
    cfg = Config()
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_bytes(conteudo)
    return cfg


def test_lista_salva_pelo_excel_em_cp1252(tmp_path):
    cfg = _cfg_lista(tmp_path, "Nome;Email\nJoão Conceição;joao@x.com\n".encode("cp1252"))
    assert [a.nome for a in carregar_alunos(cfg)] == ["João Conceição"]


def test_lista_com_e_mail_e_linha_sep(tmp_path):
    cfg = _cfg_lista(tmp_path, "sep=;\nNome;E-mail\nAna Souza;ana@x.com\n".encode("utf-8"))
    assert [(a.nome, a.email) for a in carregar_alunos(cfg)] == [("Ana Souza", "ana@x.com")]


def test_acrescentar_sugestao_nao_gruda_na_ultima_linha(tmp_path):
    caminho = tmp_path / "nomes_aprovados.csv"
    caminho.write_text("nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo\nAna;Ana Souza;ana@x.com;sim;x",
                       encoding="utf-8")  # sem quebra no fim (Bloco de Notas)
    resultado = conciliar([ANA, BRUNO], {"100 - T": ["Bruno L.jpg"]}, codigos_site=["100"])
    assert registrar_sugestoes(resultado, [ANA, BRUNO], caminho) == 1
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    assert linhas[1].endswith(";sim;x") and linhas[2].startswith("Bruno L;")

    pastas = tmp_path / "pastas.csv"
    pastas.write_text("pasta;codigo;tema;aprovado;semelhanca\nA;100;;sim;x", encoding="utf-8")
    registrar_sugestoes_pasta([("B", "", "", 0.0)], pastas)
    assert pastas.read_text(encoding="utf-8").splitlines()[2].startswith("B;")


def test_excel_que_tira_os_zeros_do_codigo_nao_troca_o_tema(tmp_path, capsys):
    """"000" virou "0" (outro tema do site): a aprovação é ignorada."""
    caminho = tmp_path / "pastas.csv"
    caminho.write_text("pasta;codigo;tema;aprovado;semelhanca\n"
                       "3B - A;0;000- DISSERTATIVO ARGUMENTATIVO;sim;\n"
                       "3B - B;000;000- DISSERTATIVO ARGUMENTATIVO;sim;\n"
                       "3B - C;100;;sim;\n", encoding="utf-8")
    assert carregar_codigos_pasta(caminho) == {"3B - B": "000", "3B - C": "100"}
    assert "'3B - A' tem codigo 0 mas o tema e 000" in capsys.readouterr().out


# ─── Revisão: renomear e desfazer ────────────────────────────

def test_desfazer_nao_volta_arquivo_ja_enviado(tmp_path):
    (tmp_path / "100 - T").mkdir()
    (tmp_path / "100 - T" / "Ana.jpg").write_bytes(b"x")
    banco, log = tmp_path / "progresso.db", tmp_path / "log.csv"
    assert renomear(tmp_path, "100 - T", "Ana.jpg", ANA, banco, log) == ("Ana Souza.jpg", "")
    with Progresso(banco) as prog:
        prog.marcar(ANA.id, "100 - T/Ana Souza.jpg", ENVIADO, pasta="100")
    saidas = []
    assert desfazer_renomeacoes(log, tmp_path, saidas.append, banco=banco) == 0
    assert (tmp_path / "100 - T" / "Ana Souza.jpg").is_file()
    assert any("ja tem estado ENVIADO" in s for s in saidas)


def test_desfazer_com_log_estranho_nao_quebra(tmp_path):
    log = tmp_path / "log.csv"
    log.write_text("a;b\n1;2\n", encoding="utf-8")
    saidas = []
    assert desfazer_renomeacoes(log, tmp_path, saidas.append) == 0
    assert any("Nada foi desfeito" in s for s in saidas)
    assert desfazer_renomeacoes(tmp_path / "nao_existe.csv", tmp_path, saidas.append) == 0


def test_banco_ilegivel_trava_a_renomeacao(tmp_path):
    banco = tmp_path / "progresso.db"
    banco.write_bytes(b"isto nao e sqlite" * 100)
    assert estado_travado(banco, "100 - T/Ana.jpg").startswith("banco ilegivel")


# ─── main ────────────────────────────────────────────────────

def test_main_pasta_com_modo_teste_e_recusado(capsys):
    import main as main_mod
    assert main_mod.main(["--modo-teste", "--pasta", "qualquer"]) == 2
    assert "--pasta nao vale no --modo-teste" in capsys.readouterr().out


def test_main_lista_sem_colunas_explica(tmp_path, monkeypatch, capsys):
    import main as main_mod
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "Redações plataforma"
    cfg.pasta_raiz.mkdir()
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Aluno;Contato\nAna;ana@x.com\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    assert main_mod.main([]) == 2
    assert "Não consegui ler a lista de alunos" in capsys.readouterr().out
