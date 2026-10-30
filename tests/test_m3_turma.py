# -*- coding: utf-8 -*-
"""M3 (parte A): escola/turma, senha por aluno, identidade estrita, menu.

Tudo com dados inventados numa RAIZ temporária (conftest). Sem navegador,
sem login, sem envio."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO, REVISAO_MANUAL
from modulos.base.turma import TurmaInvalida, aplicar_turma, listar_escolas, listar_turmas, raiz_redacoes
from modulos.dados.conciliacao_completa import conciliar_com_aprovacoes
from modulos.dados.planilha_arquivos import carregar_alunos


def _turma(escola, turma, alunos, temas, aprovados=""):
    """Cria uma turma: alunos = "Nome;Email;Senha" por linha; temas = {pasta: [arquivos]}."""
    pasta = raiz_redacoes() / escola / turma
    (pasta / "temas").mkdir(parents=True)
    (pasta / "alunos.csv").write_text("Nome;Email;Senha\n" + "".join(f"{a}\n" for a in alunos), encoding="utf-8")
    for tema, arquivos in temas.items():
        (pasta / "temas" / tema).mkdir()
        for arquivo in arquivos:
            (pasta / "temas" / tema / arquivo).write_bytes(f"{escola}/{turma}/{tema}/{arquivo}".encode())
    if aprovados:
        (pasta / "dados").mkdir()
        (pasta / "dados" / "nomes_aprovados.csv").write_text(aprovados, encoding="utf-8")
    return pasta


def _cfg(escola, turma):
    cfg = Config()
    aplicar_turma(cfg, escola, turma)
    return cfg


# ─── Contexto da turma ───────────────────────────────────────

def test_duas_escolas_com_turma_e_tema_de_mesmo_nome_nao_se_cruzam():
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s1"], {"100 - Tema": ["Ana Um.jpg", "Bia Dois.jpg"]},
           aprovados="nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo\n"
                     "Bia Dois;Ana Um;ana@um.example.com;sim;\n")
    _turma("Escola Dois", "3A", ["Bia Dois;bia@dois.example.com;s2"], {"100 - Tema": ["Bia Dois.jpg"]})

    um, dois = _cfg("Escola Um", "3A"), _cfg("Escola Dois", "3A")
    assert um.planilha != dois.planilha and um.pasta_raiz != dois.pasta_raiz
    assert um.arquivo_nomes_aprovados != dois.arquivo_nomes_aprovados
    assert um.id_turma == "Escola Um/3A" and dois.id_turma == "Escola Dois/3A"

    r_dois = conciliar_com_aprovacoes(dois, carregar_alunos(dois), ["100"]).resultado
    # a aprovação "bia dois -> ana@um" é da Escola Um: na Escola Dois a Bia é a Bia
    assert [(i.arquivo, i.aluno.email) for i in r_dois.fila_validada()] == [("Bia Dois.jpg", "bia@dois.example.com")]
    r_um = conciliar_com_aprovacoes(um, carregar_alunos(um), ["100"]).resultado
    assert {i.aluno.email for i in r_um.itens if i.aluno} == {"ana@um.example.com"}
    assert all(i.aluno.email != "bia@dois.example.com" for i in r_um.itens if i.aluno)


def test_so_pasta_com_alunos_csv_e_turma_e_so_escola_com_turma_aparece():
    _turma("Escola Um", "3A", [], {})
    (raiz_redacoes() / "Escola Um" / "Sem lista").mkdir()
    (raiz_redacoes() / "100 - Tema solto na raiz").mkdir(parents=True)  # dados antigos, antes da M3
    assert listar_escolas() == ["Escola Um"]
    assert listar_turmas("Escola Um") == ["3A"]


@pytest.mark.parametrize("escola, turma", [
    ("Escola Um", "Nao Existe"), ("Nao Existe", "3A"), ("..", "3A"), ("Escola Um", ".."),
    ("Escola Um/3A", "3A"), ("Escola Um", "3A/../3A"), ("", "3A"), (" Escola Um", "3A"),
])
def test_turma_invalida_e_recusada(escola, turma):
    _turma("Escola Um", "3A", [], {})
    with pytest.raises(TurmaInvalida):
        _cfg(escola, turma)


def test_caminho_absoluto_e_recusado(tmp_path):
    with pytest.raises(TurmaInvalida):
        _cfg(str(tmp_path), "3A")


def _ligar(link: Path, alvo: Path) -> None:
    """Junction no Windows (não precisa de administrador); link simbólico no resto."""
    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(alvo), str(link))
    else:
        os.symlink(alvo, link, target_is_directory=True)


@pytest.mark.parametrize("onde", ["escola", "turma", "temas"])
def test_link_ou_junction_que_sai_da_turma_e_recusado(tmp_path, onde):
    fora = tmp_path / "fora"
    (fora / "3A" / "temas").mkdir(parents=True)
    (fora / "3A" / "alunos.csv").write_text("Nome;Email;Senha\n", encoding="utf-8")
    if onde == "escola":
        raiz_redacoes().mkdir(parents=True)
        _ligar(raiz_redacoes() / "Escola Um", fora)
    elif onde == "turma":
        (raiz_redacoes() / "Escola Um").mkdir(parents=True)
        _ligar(raiz_redacoes() / "Escola Um" / "3A", fora / "3A")
    else:
        pasta = _turma("Escola Um", "3A", [], {})
        (pasta / "temas").rmdir()
        _ligar(pasta / "temas", fora / "3A" / "temas")
    with pytest.raises(TurmaInvalida):
        _cfg("Escola Um", "3A")


# ─── main: --escola/--turma ──────────────────────────────────

@pytest.mark.parametrize("argv, mensagem", [
    ([], "Escolha a turma"),
    (["--revisar"], "Escolha a turma"),
    (["--conferir-site"], "Escolha a turma"),
    (["--escola", "Escola Um"], "--escola e --turma vao juntos"),
    (["--turma", "3A"], "--escola e --turma vao juntos"),
    (["--escola", "Escola Um", "--turma", "3B"], "Turma não encontrada"),
    (["--escola", "Escola Um", "--turma", "3A", "--pasta", "x"], "--pasta saiu"),
    (["--escola", "Escola Um", "--turma", "3A", "--modo-teste"], "--modo-teste nao usa turma"),
])
def test_main_sem_turma_valida_recusa(argv, mensagem, capsys):
    import main as main_mod
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s1"], {})
    # sem fallback para a lista antiga nem para a raiz das redações
    (config_mod.RAIZ / "dados").mkdir()
    (config_mod.RAIZ / "dados" / "dados_alunos.csv").write_text("Nome;Email\nVelha;v@example.com\n", encoding="utf-8")
    with patch.object(main_mod, "carregar_alunos", side_effect=AssertionError("leu uma lista")):
        assert main_mod.main(argv) == 2
    assert mensagem in capsys.readouterr().out


def test_main_recusa_dados_do_config_ini_com_turma(capsys):
    import main as main_mod
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s1"], {})
    ini = config_mod.RAIZ / "config.ini"
    ini.write_text("[dados]\nplanilha = outra/alunos.csv\n", encoding="utf-8")
    assert main_mod.main(["--escola", "Escola Um", "--turma", "3A"]) == 2
    assert "tire pasta_raiz/planilha" in capsys.readouterr().out


def test_main_com_turma_usa_so_os_caminhos_dela_e_os_temas_do_projeto(monkeypatch, capsys):
    import main as main_mod
    pasta = _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s1"], {"100 - Tema": ["Ana Um.jpg"]})
    temas = config_mod.RAIZ / "dados" / "temas_site.csv"  # um só, para todas as turmas
    temas.parent.mkdir(exist_ok=True)
    temas.write_text("codigo,texto\n100,100- Tema\n", encoding="utf-8")
    monkeypatch.setattr(main_mod, "TEMAS_SITE_CSV", temas)
    assert main_mod.main(["--escola", "Escola Um", "--turma", "3A"]) == 0
    saida = capsys.readouterr().out
    assert not (pasta / "dados" / "temas_site.csv").exists()
    assert "Alunos carregados: 1" in saida and "Prontas para enviar:" in saida
    assert (pasta / "relatorios" / "relatorio_conciliacao.csv").is_file()
    assert (pasta / "logs" / "automacao.log").is_file()
    assert not (config_mod.RAIZ / "relatorios" / "relatorio_conciliacao.csv").exists()
    # o caderno continua global
    assert (config_mod.RAIZ / "relatorios" / "progresso.db").is_file()


def test_preparar_cria_a_turma(capsys):
    import main as main_mod
    assert main_mod.main(["--preparar", "--escola", "Escola Nova", "--turma", "1B"]) == 0
    pasta = raiz_redacoes() / "Escola Nova" / "1B"
    assert (pasta / "alunos.csv").read_text(encoding="utf-8") == "Nome;Email;Senha\n"
    assert (pasta / "temas").is_dir()
    assert main_mod.main(["--preparar", "--escola", "..", "--turma", "1B"]) == 2


# ─── Senha por aluno ─────────────────────────────────────────

def test_senha_e_texto_exato_e_nunca_aparece(caplog):
    pasta = _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com; 007 x ", "Bia;bia@um.example.com;"], {})
    alunos = carregar_alunos(_cfg("Escola Um", "3A"))
    assert [a.senha for a in alunos] == [" 007 x ", ""]
    assert "007" not in repr(alunos) and "007" not in str(alunos[0])
    from modulos.base.progresso_relatorio import configurar_logging
    log = configurar_logging(pasta / "logs")
    log.error("login falhou com 007 x no meio")
    texto = (pasta / "logs" / "automacao.log").read_text(encoding="utf-8")
    assert "007 x" not in texto and "suprimido" in texto


@pytest.fixture
def navegador():
    from modulos.envio import fluxo_envio_producao as fep
    with patch.object(fep, "sync_playwright"), patch.object(fep, "time"), \
         patch.object(fep, "verificar_dominio_autorizado"), patch.object(fep, "logout"), \
         patch.object(fep, "obter_senha", side_effect=AssertionError("pediu senha global")), \
         patch.object(fep, "login") as login, patch.object(fep, "confirmar_identidade"), \
         patch.object(fep, "enviar_item", return_value="ENVIADO") as enviar, \
         patch("modulos.base.config.PRODUCAO_BLOQUEADA", False), \
         patch("builtins.input", return_value="ENVIAR"):
        yield {"login": login, "enviar": enviar}


def test_cada_aluno_entra_com_a_sua_senha_e_sem_senha_nao_entra(navegador, capsys):
    from modulos.envio.fluxo_envio_producao import executar_envio_producao
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;senha-ana", "Bia Um;bia@um.example.com;",
                               "Caio Um;caio@um.example.com;senha-caio"],
           {"100 - Tema": ["Ana Um.jpg", "Bia Um.jpg", "Caio Um.jpg"]})
    cfg = _cfg("Escola Um", "3A")
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    resultado = conciliar_com_aprovacoes(cfg, carregar_alunos(cfg), ["100"]).resultado
    assert len(resultado.fila_validada()) == 3

    assert executar_envio_producao(cfg, resultado) == 0

    assert [c.args[2:] for c in navegador["login"].call_args_list] == [
        ("ana@um.example.com", "senha-ana"), ("caio@um.example.com", "senha-caio")]
    assert "Bia Um: sem senha no alunos.csv" in capsys.readouterr().out


def test_conferencia_nao_abre_conta_sem_senha(capsys):
    from modulos.site import conferencia_site as cs
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;senha-ana", "Bia Um;bia@um.example.com;"],
           {"100 - Tema": ["Ana Um.jpg", "Bia Um.jpg"]})
    cfg = _cfg("Escola Um", "3A")
    resultado = conciliar_com_aprovacoes(cfg, carregar_alunos(cfg), ["100"]).resultado
    abertas = []

    def ler(cfg_, conferencias, saida):
        for conf in conferencias:
            abertas.append((conf.aluno.email, conf.aluno.senha))
            conf.lista = []
        return False
    respostas = iter(["CONFERIR", "n"])
    assert cs.executar_conferencia_site(cfg, resultado, lambda _: next(respostas), lambda *_: None, ler=ler) == 0
    assert abertas == [("ana@um.example.com", "senha-ana")]
    relatorio = next((cfg.pasta_relatorios).glob("conferencia_site_*.csv")).read_text(encoding="utf-8-sig")
    assert "Bia Um;100 - Tema;Bia Um.jpg;100;não conferido" in relatorio


# ─── Identidade e homônimos ──────────────────────────────────

def test_identidade_diferente_abreviada_ou_ausente_nao_anexa(navegador):
    from modulos.base.excecoes import IdentidadeDivergente
    from modulos.envio import fluxo_envio_producao as fep
    _turma("Escola Um", "3A", ["Ana Lima Souza;ana@um.example.com;s"], {"100 - Tema": ["Ana Lima Souza.jpg"]})
    cfg = _cfg("Escola Um", "3A")
    resultado = conciliar_com_aprovacoes(cfg, carregar_alunos(cfg), ["100"]).resultado
    with patch.object(fep, "confirmar_identidade", side_effect=IdentidadeDivergente("Ana Lima")):
        assert fep.executar_envio_producao(cfg, resultado) == 1
    assert navegador["enviar"].call_count == 0


def test_homonimos_na_turma_vao_os_dois_para_revisao_manual():
    from modulos.dados.planilha_arquivos import conciliar
    _turma("Escola Um", "3A", ["Ana Lima;ana1@um.example.com;s", "ANA LIMA;ana2@um.example.com;s",
                               "Bia Um;bia@um.example.com;s"],
           {"100 - Tema": ["Ana Lima.jpg", "Bia Um.jpg"]})
    cfg = _cfg("Escola Um", "3A")
    alunos = carregar_alunos(cfg)
    resultado = conciliar_com_aprovacoes(cfg, alunos, ["100"]).resultado
    estados = {i.arquivo: i.estado for i in resultado.itens if i.arquivo}
    assert estados == {"Ana Lima.jpg": REVISAO_MANUAL, "Bia Um.jpg": EXATO_UNICO}
    # mesmo com uma aprovação apontando para um dos dois (o site não distingue)
    r = conciliar(alunos, {"100 - Tema": ["A Lima.jpg"]}, ["100"], nomes_aprovados={"a lima": alunos[1]})
    assert [i.estado for i in r.itens if i.arquivo] == [REVISAO_MANUAL]
    assert r.fila_validada() == []


# ─── Menu: escolher e trocar turma ───────────────────────────

def test_menu_escolhe_turma_e_trocar_nao_reaproveita_nada():
    from modulos.ferramentas import menu
    _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s"], {"100 - Tema": ["Ana Um.jpg"]})
    _turma("Escola Um", "3B", ["Bia Um;bia@um.example.com;"], {})
    chamadas, saidas = [], []
    respostas = iter(["1", "1", "s",            # escola 1, turma 3A, usar
                      "1", "",                  # conferir (3A)
                      "14", "e", "1", "v", "1", "2", "s",  # trocar escola: escola, voltar, escola, turma 3B, usar
                      "2", "", "0"])            # revisar (3B), sair
    assert menu.executar_menu(lambda argv: chamadas.append(argv) or 0, lambda _: next(respostas),
                              saidas.append) == 0
    assert chamadas == [["--escola", "Escola Um", "--turma", "3A"],
                        ["--revisar", "--escola", "Escola Um", "--turma", "3B"]]
    texto = "\n".join(saidas)
    assert "Alunos na lista" in texto and "Lista de alunos:" in texto and "100 - Tema" in texto
    assert "Alunos sem senha (não entram no site)" in texto


def test_menu_modo_teste_nao_leva_turma_e_sem_turma_nao_abre():
    from modulos.ferramentas import menu
    chamadas = []
    respostas = iter(["4", "", "", "0"])
    menu.executar_menu(lambda argv: chamadas.append(argv) or 0, lambda _: next(respostas), lambda *_: None,
                       turma=("E", "T"))
    assert chamadas == [["--modo-teste"]]
    assert menu.executar_menu(lambda argv: pytest.fail("abriu sem turma"), lambda _: "1", lambda *_: None) == 0


def test_main_seguidos_de_turmas_diferentes_trocam_o_log():
    import main as main_mod
    um = _turma("Escola Um", "3A", ["Ana Um;ana@um.example.com;s"], {})
    dois = _turma("Escola Dois", "3A", ["Bia;bia@dois.example.com;s"], {})
    main_mod.main(["--escola", "Escola Um", "--turma", "3A"])
    main_mod.main(["--escola", "Escola Dois", "--turma", "3A"])
    logging.getLogger("automacao_redacoes").info("so na turma dois")
    assert "so na turma dois" in (dois / "logs" / "automacao.log").read_text(encoding="utf-8")
    assert "so na turma dois" not in (um / "logs" / "automacao.log").read_text(encoding="utf-8")
    assert "Escola Dois" not in (um / "logs" / "automacao.log").read_text(encoding="utf-8")


def test_pagina_falsa_de_identidade_nao_e_usada():
    """Garantia extra: o menu do usuário é o único lugar lido."""
    from modulos.site.login import confirmar_identidade
    page = MagicMock(url="https://www.esquemaredacao.com.br/minhas-redacoes")
    page.locator.return_value.count.return_value = 1
    page.locator.return_value.first.text_content.return_value = "Ana Um"
    from modulos.dados.planilha_arquivos import Aluno
    assert confirmar_identidade(page, Aluno("Ana Um", "a@example.com"))
    assert {c.args[0] for c in page.locator.call_args_list} == {".navbar-right .dropdown-toggle"}
