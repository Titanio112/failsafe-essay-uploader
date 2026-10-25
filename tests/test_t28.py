# -*- coding: utf-8 -*-
"""Testes offline da T28: --pasta e código de tema aprovado por pasta.
Sem navegador, sem dados reais."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO, SEM_CODIGO
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.dados.sugestao_temas import carregar_codigos_pasta, registrar_sugestoes_pasta, sugerir_codigos

ANA = Aluno(nome="Ana Lalara", email="ana@escola.com")
TEMAS = [("100", "100- Impactos da invisibilidade de filiação para os cidadãos brasileiros"),
         ("9", "9- Expectativa de vida")]
PASTA = "3B - Impacatos da Invisibilidade da filiação para o cidadão brasileiro"


def _ler(caminho):
    return list(csv.DictReader(open(caminho, encoding="utf-8-sig"), delimiter=";"))


def test_pasta_sem_codigo_nao_entra_sem_aprovacao():
    resultado = conciliar([ANA], {PASTA: ["Ana Lalara.JPG"]}, codigos_site=["100"])
    assert [i.estado for i in resultado.itens if i.arquivo] == [SEM_CODIGO]


def test_pasta_aprovada_entra_com_o_codigo_e_mantem_o_nome_real():
    resultado = conciliar([ANA], {PASTA: ["Ana Lalara.JPG"]}, codigos_site=["100"],
                          codigos_pasta={PASTA: "100"})
    item = resultado.fila_validada()[0]
    assert (item.estado, item.codigo_tema, item.pasta) == (EXATO_UNICO, "100", PASTA)


def test_aprovacao_nao_sobrescreve_pasta_que_ja_tem_codigo():
    resultado = conciliar([ANA], {"9 - Tema": ["Ana Lalara.JPG"]}, codigos_site=["9", "100"],
                          codigos_pasta={"9 - Tema": "100"})
    assert resultado.fila_validada()[0].codigo_tema == "9"


def test_sugestoes_de_pasta_gravadas_e_aprovacao_lida(tmp_path):
    caminho = tmp_path / "pastas_aprovadas.csv"
    sugestoes = sugerir_codigos([PASTA, "3B - Efeitos da aporofobia"], TEMAS)

    assert registrar_sugestoes_pasta(sugestoes, caminho) == 2
    assert registrar_sugestoes_pasta(sugestoes, caminho) == 0  # não duplica
    linhas = _ler(caminho)
    assert [(l["pasta"][:12], l["codigo"], l["aprovado"]) for l in linhas] == [
        ("3B - Efeitos", "", ""), ("3B - Impacat", "100", "")]
    assert carregar_codigos_pasta(caminho) == {}  # nada aprovado sozinho

    # O Antônio aprova a de filiação e digita à mão o código da outra
    # (bug 010: código digitado à mão só vale com o nome do tema escrito)
    linhas[0]["codigo"], linhas[0]["aprovado"] = "77", "sim"
    linhas[1]["aprovado"] = "SIM"
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    assert carregar_codigos_pasta(caminho) == {PASTA: "100"}

    linhas[0]["tema"] = "77- Tema digitado"
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)
    assert carregar_codigos_pasta(caminho) == {"3B - Efeitos da aporofobia": "77", PASTA: "100"}


def test_main_pasta_inexistente_da_erro_claro(tmp_path, monkeypatch, capsys):
    import main as main_mod
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: Config())
    assert main_mod.main(["--pasta", str(tmp_path / "nao_existe")]) == 2
    assert "nao encontrada" in capsys.readouterr().out


def test_main_dry_run_com_pasta_e_pasta_aprovada(tmp_path, monkeypatch, capsys):
    """--pasta lê as redações onde estão; pasta aprovada entra na fila."""
    import main as main_mod
    redacoes = tmp_path / "Redações plataforma"
    (redacoes / PASTA).mkdir(parents=True)
    (redacoes / PASTA / "Ana Lalara.JPG").write_bytes(b"x")
    cfg = Config()
    cfg.planilha = tmp_path / "dados_alunos.csv"
    cfg.planilha.write_text("Nome;Email\nAna Lalara;ana@escola.com\n", encoding="utf-8")
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "p.db"
    cfg.arquivo_nomes_aprovados = tmp_path / "nomes.csv"
    cfg.arquivo_pastas_aprovadas = tmp_path / "pastas.csv"
    cfg.arquivo_pastas_aprovadas.write_text(f"pasta;codigo;tema;aprovado;semelhanca\n{PASTA};100;100- Impactos da filiacao;sim;\n",
                                            encoding="utf-8")
    (tmp_path / "dados").mkdir()
    (tmp_path / "dados" / "temas_site.csv").write_text("codigo,texto\n100,100- Filiação\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)

    assert main_mod.main(["--pasta", str(redacoes)]) == 0

    saida = capsys.readouterr().out
    assert f"Pasta aprovada: {PASTA} -> tema 100" in saida
    assert "Prontas para enviar:" in saida
    assert saida.count("Coluna 'Senha'") == 0  # CSV sem coluna Senha


def test_sugestao_de_nome_sai_mesmo_com_pasta_sem_codigo(tmp_path):
    """Nomes e pastas aprovados na mesma rodada (a pasta ainda sem código)."""
    from modulos.dados.nomes_aprovados import registrar_sugestoes
    completa = Aluno(nome="Ana Lalara Larili dos Larito", email="ana@escola.com")
    resultado = conciliar([completa], {PASTA: ["Ana Lalara Larili.JPG", "Ana Lalara Larili dos Larito.JPG"]},
                          codigos_site=["100"])
    assert {i.estado for i in resultado.itens if i.arquivo} == {SEM_CODIGO}

    caminho = tmp_path / "nomes.csv"
    assert registrar_sugestoes(resultado, [completa], caminho) == 1  # o nome exato não vira sugestão
    assert [(l["nome_no_arquivo"], l["aluno_email"]) for l in _ler(caminho)] == [
        ("Ana Lalara Larili", "ana@escola.com")]
