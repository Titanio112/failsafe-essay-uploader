# -*- coding: utf-8 -*-
"""Testes offline da T56: achados da revisão do código das T51-T55
(conferência no site, enviar as que faltam, Configurações, Resolver).
Cada teste reproduz um cenário que dava errado antes. Sem navegador."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import relogio
from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.ferramentas import configuracoes, menu
from modulos.site import conferencia_site as cs
from modulos.site.lista_redacoes import ItemListaRedacao

ANA = Aluno(nome="Ana Souza", email="ana@x.com")


def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


def _item(pasta, codigo, aluno=ANA, arquivo=None):
    return ItemConciliacao(pasta=pasta, arquivo=arquivo or f"{aluno.nome}.JPG", pessoa=aluno.nome,
                           estado="EXATO_UNICO", aluno=aluno, codigo_tema=codigo)


def _linha(codigo):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- X", data="30/09/2026", situacao="Corrigida")


# ─── Conferência no site ─────────────────────────────────────

def test_sobra_de_outro_tema_segura_todas_as_que_faltam():
    # 2 fotos novas no 000 + 3 do 100 que foram mandadas como 000: o site tem 3x 000.
    # Antes: 2 "no site" (errado) e só 1 do 100 virava "outro tema?"; 2 iam para o envio.
    itens = [_item("A1", "000"), _item("A2", "000"), _item("B1", "100"), _item("B2", "100"), _item("B3", "100")]
    conf = cs.alunos_para_conferir(ResultadoConciliacao(itens=itens))[0]
    conf.lista = [_linha("000")] * 3
    cs.comparar(conf)
    assert [e for _, e, _ in conf.linhas][2:] == [cs.OUTRO_TEMA] * 3
    assert cs.faltam_enviar([conf]) == []


def test_parou_antes_conta_como_nao_tentado(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    bia = Aluno(nome="Bia Lima", email="bia@x.com")
    saidas = []

    def ler(cfg_, conferencias, senha, saida):
        conferencias[0].erro = "CAPTCHA/bloqueio: x"
        return True  # parou: a Bia nunca foi tentada

    cfg = Config()
    cfg.pasta_raiz, cfg.pasta_relatorios = tmp_path, tmp_path / "relatorios"
    cs.executar_conferencia_site(cfg, ResultadoConciliacao(itens=[_item("A", "000"), _item("A", "000", bia)]),
                                 _respostas("CONFERIR"), saidas.append, ler=ler)
    assert any("Não conferidas" in s and s.rstrip().endswith("1") for s in saidas)
    assert any("Não tentadas" in s and s.rstrip().endswith("1") for s in saidas)
    relatorio = next((tmp_path / "relatorios").glob("conferencia_site_*.csv"))
    with open(relatorio, encoding="utf-8-sig") as f:
        assert [l["resultado"] for l in csv.DictReader(f, delimiter=";")] == [cs.NAO_CONFERIDO, cs.NAO_TENTADO]


def test_erro_no_meio_ainda_grava_o_relatorio(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")

    def ler(cfg_, conferencias, senha, saida):
        conferencias[0].lista = [_linha("000")]
        raise RuntimeError("navegador caiu")

    cfg = Config()
    cfg.pasta_raiz, cfg.pasta_relatorios = tmp_path, tmp_path / "relatorios"
    r = cs.executar_conferencia_site(cfg, ResultadoConciliacao(itens=[_item("A", "000")]),
                                     _respostas("CONFERIR"), lambda *_: None, ler=ler)
    assert r == 1 and list((tmp_path / "relatorios").glob("conferencia_site_*.csv"))


def _relatorio(pasta: Path, linhas, colunas=cs.COLUNAS_CSV, encoding="utf-8-sig"):
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"conferencia_site_{relogio.agora():%Y%m%d}_010000.csv"
    with open(caminho, "w", encoding=encoding, newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(colunas)
        for pasta_tema, tema in linhas:
            w.writerow(["Ana Souza", pasta_tema, "Ana Souza.JPG", tema, cs.FORA_DO_SITE, 0, "", ""])


def test_relatorio_vale_so_para_o_mesmo_tema(tmp_path):
    _relatorio(tmp_path, [("F", "100")])
    # a pasta foi reaprovada como 000 depois da conferência: o 000 nunca foi olhado
    assert cs.faltantes_do_relatorio(tmp_path, ResultadoConciliacao(itens=[_item("F", "000")]),
                                     lambda *_: None) == []
    assert len(cs.faltantes_do_relatorio(tmp_path, ResultadoConciliacao(itens=[_item("F", "100")]),
                                         lambda *_: None)) == 1


def test_relatorio_mexido_no_excel_nao_quebra(tmp_path):
    _relatorio(tmp_path, [("F", "100")], colunas=["aluno,pasta,arquivo"])
    saidas = []
    assert cs.faltantes_do_relatorio(tmp_path, ResultadoConciliacao(itens=[_item("F", "100")]),
                                     saidas.append) is None
    assert any("Não consegui ler" in s for s in saidas)


def test_relatorio_em_ansi_nao_quebra(tmp_path):
    pasta = tmp_path
    caminho = pasta / f"conferencia_site_{relogio.agora():%Y%m%d}_010000.csv"
    caminho.write_bytes(";".join(cs.COLUNAS_CSV).encode() + b"\nAna;F;\xe7.JPG;100;n\xe3o;0;;\n")
    assert cs.faltantes_do_relatorio(pasta, ResultadoConciliacao(itens=[]), lambda *_: None) is None


# ─── Enviar as que faltam ────────────────────────────────────

def test_enviar_faltantes_usa_a_fila_inteira_contra_foto_repetida(tmp_path, monkeypatch):
    import main as main_mod
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    for pasta in ("A", "B"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / "Ana Souza.JPG").write_bytes(b"a mesma foto")
    cfg = Config()
    cfg.pasta_raiz, cfg.pasta_relatorios = tmp_path, tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "progresso.db"
    completo = ResultadoConciliacao(itens=[_item("A", "000"), _item("B", "100")])
    vistos = {}
    monkeypatch.setattr(main_mod, "executar_envio_producao",
                        lambda cfg, r, p, lotes=None, **_: vistos.setdefault("lotes", lotes) and 0)
    main_mod._enviar_faltantes(cfg, [completo.itens[1]], _respostas("s"), resultado=completo)
    assert vistos["lotes"] == []  # B é a mesma foto de A: fica de fora


def test_enviar_faltantes_bloqueado_antes_de_montar(monkeypatch):
    import main as main_mod
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)
    assert main_mod.main(["--enviar-faltantes"]) == 2


# ─── Configurações ───────────────────────────────────────────

def test_secao_com_comentario_nao_duplica(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[plataforma] ; navegador\nheadless = false\n", encoding="utf-8")
    configuracoes.gravar_opcao(ini, "plataforma", "headless", "true")
    assert ini.read_text(encoding="utf-8").count("[plataforma]") == 1
    assert config_mod.carregar_config(ini).headless is True


def test_secao_com_maiuscula_e_outra_secao(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("[Plataforma]\nheadless = false\n", encoding="utf-8")
    configuracoes.gravar_opcao(ini, "plataforma", "headless", "true")
    assert config_mod.carregar_config(ini).headless is True  # gravou onde o script lê


def test_arquivo_com_bom(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_bytes("﻿[plataforma]\nheadless = false\n".encode("utf-8"))
    assert config_mod.carregar_config(ini).headless is False
    configuracoes.gravar_opcao(ini, "plataforma", "headless", "true")
    assert config_mod.carregar_config(ini).headless is True


def test_valor_errado_nao_derruba_o_menu(tmp_path, monkeypatch):
    ini = tmp_path / "config.ini"
    ini.write_text("[plataforma]\nheadless = sim\n", encoding="utf-8")
    monkeypatch.setattr(config_mod, "RAIZ", tmp_path)
    with pytest.raises(config_mod.ConfigInvalida):
        config_mod.carregar_config(ini)
    saidas = []
    menu.mostrar_menu(saidas.append)
    assert any("config.ini com erro" in s for s in saidas)
    assert configuracoes.executar_configuracoes(ini, _respostas("n"), saidas.append) == 2


# ─── Resolver ────────────────────────────────────────────────

def test_resolver_abre_a_foto_do_modo_teste_na_pasta_de_teste(tmp_path, monkeypatch):
    from modulos.ferramentas import resolver
    monkeypatch.setattr(config_mod, "RAIZ", tmp_path)
    real = tmp_path / "Redações plataforma" / "84"
    teste = tmp_path / config_mod.PASTA_TESTE / "84"
    real.mkdir(parents=True)
    teste.mkdir(parents=True)
    (real / "Usuario Testes Ignorar.jpg").write_bytes(b"real")
    (teste / "Usuario Testes Ignorar.jpg").write_bytes(b"teste")
    nomes = {"teste@x.com": NOME_CONTA_TESTE}
    foto = resolver._foto(tmp_path / "Redações plataforma", "teste@x.com", "84/Usuario Testes Ignorar.jpg", nomes)
    assert foto == teste / "Usuario Testes Ignorar.jpg"
    ensaio = resolver._foto(tmp_path / "Redações plataforma", "teste@x.com",
                            "ensaio/84/Usuario Testes Ignorar.jpg", nomes)
    assert ensaio == real / "Usuario Testes Ignorar.jpg"
    assert resolver._foto(tmp_path / "Redações plataforma", "ana@x.com", "84/nao.jpg", {}) is None
