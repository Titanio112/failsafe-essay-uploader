# -*- coding: utf-8 -*-
"""Testes offline da T53: "talvez com outro tema" na conferência no site,
oferta de enviar só as que faltam, caminho do relatório clicável e
créditos no menu. Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import sobre, tela
from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.ferramentas import menu
from modulos.site import conferencia_site as cs
from modulos.site.lista_redacoes import ItemListaRedacao

ANA = Aluno(nome="Ana Souza", email="ana@x.com", senha="s")


def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


def _item(pasta, codigo, aluno=ANA):
    return ItemConciliacao(pasta=pasta, arquivo=f"{aluno.nome}.JPG", pessoa=aluno.nome, estado="EXATO_UNICO",
                           aluno=aluno, codigo_tema=codigo)


def _linha(codigo, data="30/09/2026"):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- X", data=data, situacao="Correção finalizada")


def _conf(itens, lista):
    conf = cs.alunos_para_conferir(ResultadoConciliacao(itens=itens))[0]
    conf.lista = lista
    cs.comparar(conf)
    return conf


def test_caso_real_23_10_filiacao_mandada_como_000():
    # 3 fotos do 000 + 1 do 100 na pasta; o site tem 4 do 000 e nenhuma do 100
    conf = _conf([_item("A", "000"), _item("B", "000"), _item("C", "000"), _item("F", "100")],
                 [_linha("000")] * 4)
    assert [e for _, e, _ in conf.linhas] == [cs.NO_SITE] * 3 + [cs.OUTRO_TEMA]
    assert cs.faltam_enviar([conf]) == []


def test_sem_sobra_continua_nao_esta_no_site():
    conf = _conf([_item("A", "000"), _item("F", "100")], [_linha("000")])
    assert [e for _, e, _ in conf.linhas] == [cs.NO_SITE, cs.FORA_DO_SITE]
    assert [i.pasta for i in cs.faltam_enviar([conf])] == ["F"]


def test_conta_que_nao_abriu_nunca_entra_em_faltam():
    conf = cs.alunos_para_conferir(ResultadoConciliacao(itens=[_item("F", "100")]))[0]
    conf.erro = "o site nao aceitou o login"
    cs.comparar(conf)
    assert cs.faltam_enviar([conf]) == []


def _cfg(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "progresso.db"
    return cfg


def test_depois_recebe_so_as_que_faltam(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    recebidos = []

    def ler(cfg_, conferencias, saida):  # M3: cada aluno com a senha dele
        conferencias[0].lista = [_linha("000")]
        return False

    itens = [_item("A", "000"), _item("F", "100")]
    # "n": não marcar a pasta A (T60, toda no site) como ENVIADA
    assert cs.executar_conferencia_site(_cfg(tmp_path), ResultadoConciliacao(itens=itens),
                                        _respostas("CONFERIR", "n"),
                                        lambda *_: None, ler=ler, depois=recebidos.append) == 0
    assert [[i.pasta for i in lote] for lote in recebidos] == [["F"]]


def test_depois_nao_e_chamado_se_parou(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    recebidos = []
    itens = [_item("F", "100")]
    cs.executar_conferencia_site(_cfg(tmp_path), ResultadoConciliacao(itens=itens), _respostas("CONFERIR"),
                                 lambda *_: None, ler=lambda c, conf, o: (setattr(conf[0], "lista", []), True)[1],
                                 depois=recebidos.append)
    assert recebidos == []


def test_enviar_faltantes_respeita_a_producao_bloqueada(tmp_path, monkeypatch, capsys):
    import main as main_mod
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)
    chamado = []
    monkeypatch.setattr(main_mod, "executar_envio_producao", lambda *a, **k: chamado.append(1) or 0)
    assert main_mod._enviar_faltantes(_cfg(tmp_path), [_item("F", "100")], _respostas("s")) == 2
    assert not chamado and "bloqueado" in capsys.readouterr().out.lower()


def test_enviar_faltantes_monta_lote_so_delas(tmp_path, monkeypatch):
    import main as main_mod
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    (tmp_path / "F").mkdir()
    (tmp_path / "F" / "Ana Souza.JPG").write_bytes(b"foto-f")
    vistos = {}

    def envio_falso(cfg, resultado, progresso, lotes=None, **_):
        vistos["lotes"] = [(l.aluno.nome, [i.chave_progresso for i in l.itens]) for l in lotes]
        return 0

    monkeypatch.setattr(main_mod, "executar_envio_producao", envio_falso)
    assert main_mod._enviar_faltantes(_cfg(tmp_path), [_item("F", "100")], _respostas("s")) == 0
    assert vistos["lotes"] == [("Ana Souza", ["F/Ana Souza.JPG"])]
    assert main_mod._enviar_faltantes(_cfg(tmp_path), [_item("F", "100")], _respostas("n")) == 0


def test_caminho_vira_link_no_terminal(tmp_path, monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    relatorio = tmp_path / "conferencia.csv"
    relatorio.write_text("x", encoding="utf-8")
    assert "\033]8;;" not in tela.caminho(relatorio)
    monkeypatch.setitem(tela._cores, "ativas", True)
    assert tela.caminho(relatorio).startswith("\033]8;;file:///")


def test_menu_mostra_os_creditos():
    saidas = []
    menu.mostrar_menu(saidas.append)
    assert sobre.creditos() in "\n".join(saidas)
    assert sobre.AUTOR in sobre.creditos()
