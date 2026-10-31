# -*- coding: utf-8 -*-
"""Issue #54: cadastrar no alunos.csv, ao fim da Revisão, o aluno que só existia no nome da foto. Dados inventados."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.dados.planilha_arquivos import SENHAS_LIDAS, Aluno
from modulos.ferramentas import cadastro_aluno as cad
from modulos.ferramentas.revisao_interativa import grupos_para_revisar, revisar_nomes


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _turma(tmp_path, cp1252=False):
    pasta = tmp_path / "turma"
    (pasta / "temas" / "100 - Tema").mkdir(parents=True)
    lista = "Nome;Email;Senha\nAna Um;ana@um.example.com;s1\nBia Dois;bia@dois.example.com;s2"  # sem quebra final
    (pasta / "alunos.csv").write_bytes(lista.encode("cp1252" if cp1252 else "utf-8"))
    (pasta / "temas" / "100 - Tema" / "Lia Fernanda G. Castro.jpg").write_bytes(b"x")
    return pasta


def _alunos():
    return [Aluno("Ana Um", "ana@um.example.com", senha="s1"), Aluno("Bia Dois", "bia@dois.example.com", senha="s2")]


def _itens(pasta):
    return [SimpleNamespace(pasta="100 - Tema", arquivo="Lia Fernanda G. Castro.jpg", pessoa="Lia Fernanda G. Castro")]


def test_acrescenta_so_no_fim_com_copia_e_converte_o_excel_para_utf8(tmp_path):
    pasta = _turma(tmp_path, cp1252=True)
    antes = (pasta / "alunos.csv").read_bytes().decode("cp1252")
    copia = cad.acrescentar_aluno(pasta / "alunos.csv", "Lia Fernanda G. Castro", "lia.fernanda@x.example.com", "s3cr3t")
    novo = (pasta / "alunos.csv").read_text(encoding="utf-8")
    assert novo == antes + "\nLia Fernanda G. Castro;lia.fernanda@x.example.com;s3cr3t\n"  # linhas antigas intactas
    assert copia.read_bytes().decode("cp1252") == antes and copia.name.endswith(".bak.csv")
    assert "s3cr3t" in SENHAS_LIDAS  # o log passa a esconder esta senha


def test_recusa_email_repetido_nome_igual_email_invalido_e_senha_vazia():
    alunos = _alunos()
    assert cad.validar_novo("Caio Tres", "caio@x.example.com", "p", alunos) == ""
    assert "e-mail" in cad.validar_novo("Caio", "sem-arroba", "p", alunos)
    assert "senha" in cad.validar_novo("Caio", "caio@x.example.com", "", alunos)
    assert "e-mail" in cad.validar_novo("Caio", "ANA@um.example.com", "p", alunos)  # igual sem olhar maiúscula
    assert "nome" in cad.validar_novo("ana  UM", "outro@x.example.com", "p", alunos)  # homônimo
    assert "nome" in cad.validar_novo("", "outro@x.example.com", "p", alunos)


def test_cadastra_liga_a_foto_ao_aluno_e_deixa_a_lista_para_as_proximas_checagens(tmp_path):
    pasta = _turma(tmp_path)
    alunos = _alunos()
    log = tmp_path / "renomeacoes.csv"
    # n; nome = Enter (usa o do arquivo); e-mail; senha
    r = _resp("s", "", "lia.fernanda@x.example.com", "senhaX")
    feitos, fotos = cad.cadastrar_pulados([("Lia Fernanda G. Castro", _itens(pasta))], alunos, pasta / "alunos.csv",
                                         pasta / "temas", tmp_path / "sem_banco.db", log, r, lambda *_: None)
    assert (feitos, fotos) == (1, 0)  # a foto já tinha o nome exato: ligada sem precisar renomear
    assert [a.nome for a in alunos][-1] == "Lia Fernanda G. Castro" and len(alunos) == 3
    assert (pasta / "temas" / "100 - Tema" / "Lia Fernanda G. Castro.jpg").is_file()  # já tinha o nome certo
    assert (pasta / "alunos.csv").read_text(encoding="utf-8").splitlines()[-1] == \
        "Lia Fernanda G. Castro;lia.fernanda@x.example.com;senhaX"
    assert len((pasta / "alunos.csv").read_text(encoding="utf-8").splitlines()) == 4  # as 3 + a nova (cabeçalho)


def test_nome_digitado_diferente_do_arquivo_renomeia_a_foto_com_log(tmp_path):
    pasta = _turma(tmp_path)
    alunos = _alunos()
    log = tmp_path / "renomeacoes.csv"
    r = _resp("s", "Lia Fernanda Castro", "lia.fernanda@x.example.com", "senhaX")  # o nome que o site mostra
    feitos, fotos = cad.cadastrar_pulados([("Lia Fernanda G. Castro", _itens(pasta))], alunos, pasta / "alunos.csv",
                                         pasta / "temas", tmp_path / "sem_banco.db", log, r, lambda *_: None)
    assert (feitos, fotos) == (1, 1)
    assert (pasta / "temas" / "100 - Tema" / "Lia Fernanda Castro.jpg").is_file()
    assert not (pasta / "temas" / "100 - Tema" / "Lia Fernanda G. Castro.jpg").exists()
    assert log.is_file()  # a renomeação dá para desfazer


def test_nao_quer_cadastrar_pular_ou_dado_invalido_nao_mexe_na_lista(tmp_path):
    pasta = _turma(tmp_path)
    original = (pasta / "alunos.csv").read_bytes()
    alunos = _alunos()
    args = ([("Lia Fernanda G. Castro", _itens(pasta))], alunos, pasta / "alunos.csv", pasta / "temas",
            tmp_path / "sem_banco.db", tmp_path / "log.csv")
    assert cad.cadastrar_pulados(*args, _resp("n"), lambda *_: None) == (0, 0)
    assert cad.cadastrar_pulados(*args, _resp("s", "p"), lambda *_: None) == (0, 0)
    saidas = []
    # e-mail inválido (recusa) e depois o aluno desiste com p
    assert cad.cadastrar_pulados(*args, _resp("s", "Fulana", "sem-arroba", "x", "p"), saidas.append) == (0, 0)
    assert any("e-mail inválido" in s for s in saidas)
    assert (pasta / "alunos.csv").read_bytes() == original and len(alunos) == 2
    assert not list(pasta.glob("alunos.*.bak.csv"))  # nada gravado, nenhuma cópia


def test_revisar_nomes_entrega_os_pulados_para_o_cadastro(tmp_path):
    pasta = _turma(tmp_path)
    alunos = _alunos()
    resultado = SimpleNamespace(itens=_itens(pasta))
    grupos = grupos_para_revisar(resultado, alunos)
    assert [g[0] for g in grupos] == ["Lia Fernanda G. Castro"]
    pulados: list = []
    renomeados, saiu = revisar_nomes(grupos, alunos, pasta / "temas", tmp_path / "x.db", tmp_path / "log.csv",
                                     None, _resp("p"), lambda *_: None, pulados)
    assert (renomeados, saiu) == (0, False) and [n for n, _ in pulados] == ["Lia Fernanda G. Castro"]
