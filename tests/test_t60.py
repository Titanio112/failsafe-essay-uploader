# -*- coding: utf-8 -*-
"""Testes offline da T60 (issue 030): marcar pastas enviadas depois da conferência."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno, conciliar, descobrir_pastas
from modulos.ferramentas import arquivo_morto
from modulos.ferramentas.pastas_enviadas import PREFIXO, marcar_pastas_enviadas, pastas_prontas
from modulos.site import conferencia_site as cs
from modulos.site.lista_redacoes import ItemListaRedacao

ANA, BIA = Aluno("Ana Souza", "ana@x.com", senha="s"), Aluno("Bia Lima", "bia@x.com", senha="s")
NADA = lambda *_: None  # noqa: E731


def _linha(codigo, situacao="Pendente"):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- T", data="01/10/2026", situacao=situacao,
                            nota="", botao_texto="")


def _conferir(arquivos, listas, erro=""):
    """listas: {email: [linhas do site]} -> (resultado, conferências comparadas)."""
    resultado = conciliar([ANA, BIA], arquivos, codigos_site={"53", "100"})
    conferencias = cs.alunos_para_conferir(resultado)
    for conf in conferencias:
        conf.lista = listas.get(conf.aluno.email)
        conf.erro = erro
        cs.comparar(conf)
    return resultado, conferencias


def test_pasta_com_todas_as_fotos_no_site_esta_pronta():
    resultado, confs = _conferir({"53 - T": ["Ana Souza.jpg", "Bia Lima.jpg"]},
                                 {"ana@x.com": [_linha("53")], "bia@x.com": [_linha("53")]})
    assert pastas_prontas(resultado, confs) == ["53 - T"]


@pytest.mark.parametrize("arquivos, listas", [
    ({"53 - T": ["Ana Souza.jpg", "Bia Lima.jpg"]}, {"ana@x.com": [_linha("53")], "bia@x.com": []}),
    ({"53 - T": ["Ana Souza.jpg"]}, {"ana@x.com": [_linha("53", "Cancelada")]}),
    ({"53 - T": ["Ana Souza.jpg", "Fulano.jpg"]}, {"ana@x.com": [_linha("53")]}),
    ({"53 - T": ["Ana Souza.jpg"]}, {"ana@x.com": [_linha("100")]}),
])
def test_pasta_com_alguma_foto_que_nao_esta_no_site_fica_de_fora(arquivos, listas):
    resultado, confs = _conferir(arquivos, listas)
    assert pastas_prontas(resultado, confs) == []


def test_conta_que_nao_abriu_nao_conta_como_no_site():
    resultado, confs = _conferir({"53 - T": ["Ana Souza.jpg"]}, {"ana@x.com": [_linha("53")]}, erro="login")
    assert pastas_prontas(resultado, confs) == []


def test_marcar_renomeia_com_log_so_com_sim(tmp_path):
    (tmp_path / "53 - T").mkdir()
    assert marcar_pastas_enviadas(tmp_path, ["53 - T"], tmp_path / "rel", lambda _: "n", NADA) == 0
    assert (tmp_path / "53 - T").is_dir()
    assert marcar_pastas_enviadas(tmp_path, ["53 - T"], tmp_path / "rel", lambda _: "s", NADA) == 1
    assert (tmp_path / f"{PREFIXO}53 - T").is_dir()
    log = next((tmp_path / "rel").glob("pastas_enviadas_*.csv")).read_text(encoding="utf-8-sig")
    assert "53 - T" in log


def test_pasta_enviada_fica_fora_do_envio_e_da_revisao(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    (tmp_path / "53 - T").mkdir()
    (tmp_path / f"{PREFIXO}100 - X").mkdir()
    (tmp_path / "enviada - 7 - Y").mkdir()  # maiúscula/minúscula não importa
    assert [p.name for p in descobrir_pastas(cfg)] == ["53 - T"]


def test_arquivo_morto_mostra_primeiro_as_enviadas_e_e_escolhe_so_elas(tmp_path):
    for nome in ("10 - A", f"{PREFIXO}53 - T", "99 - Z"):
        (tmp_path / nome).mkdir()
    pastas = arquivo_morto.pastas_de_tema(tmp_path)
    assert pastas[0][0].name == f"{PREFIXO}53 - T"
    assert [p.name for p in arquivo_morto._escolher(pastas, lambda _: "e", NADA)] == [f"{PREFIXO}53 - T"]


def test_conferencia_pergunta_e_marca_no_fim(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    (tmp_path / "53 - T").mkdir()
    (tmp_path / "53 - T" / "Ana Souza.jpg").write_bytes(b"x")
    cfg = Config()
    cfg.pasta_raiz, cfg.pasta_relatorios = tmp_path, tmp_path / "rel"
    resultado = conciliar([ANA], {"53 - T": ["Ana Souza.jpg"]}, codigos_site={"53"})
    respostas = iter(["CONFERIR", "s"])

    def ler(cfg_, conferencias, saida):  # M3: cada aluno com a senha dele
        conferencias[0].lista = [_linha("53")]
        return False

    assert cs.executar_conferencia_site(cfg, resultado, lambda _: next(respostas), NADA, ler=ler) == 0
    assert (tmp_path / f"{PREFIXO}53 - T" / "Ana Souza.jpg").is_file()


def test_conferencia_que_parou_nao_marca(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    (tmp_path / "53 - T").mkdir()
    cfg = Config()
    cfg.pasta_raiz, cfg.pasta_relatorios = tmp_path, tmp_path / "rel"
    resultado = conciliar([ANA], {"53 - T": ["Ana Souza.jpg"]}, codigos_site={"53"})
    respostas = iter(["CONFERIR"])

    def ler(cfg_, conferencias, saida):  # M3: cada aluno com a senha dele
        conferencias[0].lista = [_linha("53")]
        return True  # parou (CAPTCHA, 2 logins seguidos...)

    assert cs.executar_conferencia_site(cfg, resultado, lambda _: next(respostas), NADA, ler=ler) == 1
    assert (tmp_path / "53 - T").is_dir()
