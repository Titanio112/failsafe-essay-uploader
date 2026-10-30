# -*- coding: utf-8 -*-
"""Testes offline da T52: links que o Windows consegue abrir, "v = ver a
foto", configurações no menu e conferência no site (só leitura). Sem navegador."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import tela
from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.ferramentas import configuracoes, menu
from modulos.site import conferencia_site as cs
from modulos.site.lista_redacoes import ItemListaRedacao


def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


# ─── Links ───────────────────────────────────────────────────

def test_link_fora_do_vscode_deixa_acentos_sem_codificar(tmp_path, monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    uri = tela.uri_de(tmp_path / "Redações plataforma" / "Cecília #1.JPG")
    assert uri.startswith("file:///")
    assert "Redações%20plataforma/Cecília%20%231.JPG" in uri  # espaço e # codificados, acento não


def test_link_no_vscode_usa_o_proprio_vscode_e_pasta_sem_link(tmp_path, monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "vscode")
    monkeypatch.setitem(tela._cores, "ativas", True)
    foto = tmp_path / "Redações plataforma" / "Ana.JPG"
    assert tela.uri_de(foto).startswith("vscode://file/")
    assert "Reda%C3%A7%C3%B5es" in tela.uri_de(foto)  # o VS Code decodifica UTF-8 certo
    duplo = tela.link_arquivo(tmp_path / "Redações plataforma", "3B - Filiação", "Ana.JPG")
    assert duplo.startswith("3B - Filiação/")  # pasta não abre janela nova do VS Code
    assert duplo.count("\033]8;;vscode://file/") == 1


def test_abrir_arquivo_que_nao_existe(tmp_path):
    assert tela.abrir(tmp_path / "nao.jpg") == "não encontrado"


def test_revisao_v_abre_as_fotos(tmp_path, monkeypatch):
    from modulos.ferramentas import revisao_interativa as ri
    abertos = []
    monkeypatch.setattr(tela, "abrir", lambda alvo: abertos.append(Path(alvo).name) or "")
    item = ItemConciliacao(pasta="100 - T", arquivo="Ana S.JPG", pessoa="Ana S", estado="SUGESTAO_FUZZY")
    alunos = [Aluno(nome="Ana Souza", email="ana@x.com", senha="s")]
    renomeados, saiu = ri.revisar_nomes([("Ana S", [item])], alunos, tmp_path, tmp_path / "p.db",
                                        tmp_path / "log.csv", entrada=_respostas("v", "q"),
                                        saida=lambda *_: None)
    assert abertos == ["Ana S.JPG"] and saiu and renomeados == 0


# ─── Configurações ───────────────────────────────────────────

def test_gravar_opcao_mantem_comentarios(tmp_path):
    ini = tmp_path / "config.ini"
    ini.write_text("# meu comentario\n[plataforma]\nheadless = false\nslow_mo_ms = 300\n\n[dados]\nx = 1\n",
                   encoding="utf-8")
    configuracoes.gravar_opcao(ini, "plataforma", "headless", "true")
    texto = ini.read_text(encoding="utf-8")
    assert "# meu comentario" in texto and "headless = true" in texto and "slow_mo_ms = 300" in texto
    assert "[dados]\nx = 1" in texto


def test_gravar_opcao_cria_arquivo(tmp_path):
    ini = tmp_path / "config.ini"
    configuracoes.gravar_opcao(ini, "plataforma", "headless", "true")
    assert config_mod.carregar_config(ini).headless is True


def test_menu_configuracoes_troca_o_navegador(tmp_path, monkeypatch):
    ini = tmp_path / "config.ini"
    monkeypatch.setattr(configuracoes, "caminho_config", lambda: ini)
    saidas = []
    # T53: pergunta direta s/n ("não" era o que o Antônio digitou e dava "Opção inválida")
    assert menu.argumentos_da_opcao("13", _respostas("1", "não"), saida=saidas.append) is None
    assert config_mod.carregar_config(ini).headless is True
    assert any("escondido" in s for s in saidas)
    configuracoes.executar_configuracoes(ini, _respostas("x", "s"), lambda *_: None)
    assert config_mod.carregar_config(ini).headless is False
    configuracoes.executar_configuracoes(ini, _respostas(""), lambda *_: None)  # Enter = mantém
    assert config_mod.carregar_config(ini).headless is False


def test_menu_mostra_11_opcoes_e_navegador():
    saidas = []
    menu.mostrar_menu(saidas.append)
    texto = "\n".join(saidas)
    assert "13) Configurações" in texto and "navegador: aparece" in texto
    assert " 5) Conferir no site" in texto


def test_envio_pelo_menu_nao_pergunta_mais_do_navegador():
    assert menu.argumentos_da_opcao("4", _respostas("e"), saida=lambda *_: None) == ["--modo-teste", "--envio-real"]


# ─── Conferência no site ─────────────────────────────────────

ANA = Aluno(nome="Ana Souza", email="ana@x.com", senha="s")
BIA = Aluno(nome="Bia Lima", email="bia@x.com", senha="s")


def _item(aluno, pasta, arquivo, codigo):
    return ItemConciliacao(pasta=pasta, arquivo=arquivo, pessoa=aluno.nome, estado="EXATO_UNICO",
                           aluno=aluno, codigo_tema=codigo)


def _resultado():
    return ResultadoConciliacao(itens=[
        _item(ANA, "100 - T", "Ana Souza.JPG", "100"),
        _item(ANA, "000 - A", "Ana Souza.JPG", "000"),
        _item(ANA, "000 - B", "Ana Souza.JPG", "000"),
        _item(BIA, "100 - T", "Bia Lima.JPG", "100"),
    ])


def _linha(codigo, data="01/09/2026", situacao="Corrigida"):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- X", data=data, situacao=situacao)


def test_comparar_qualquer_data_e_tema_repetido():
    ana = cs.alunos_para_conferir(_resultado())[0]
    ana.lista = [_linha("100"), _linha("000")]
    cs.comparar(ana)
    assert [e for _, e, _ in ana.linhas] == [cs.NO_SITE, cs.NO_SITE, cs.EM_PARTE]


def _cfg(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    return cfg


def test_conferencia_sem_confirmar_nao_abre_conta(tmp_path, monkeypatch):
    chamado = []
    r = cs.executar_conferencia_site(_cfg(tmp_path), _resultado(), _respostas("conferir"),
                                     lambda *_: None, ler=lambda *a: chamado.append(1))
    assert r == 2 and not chamado


def test_conferencia_grava_relatorio_e_nao_toca_no_caderno(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    cfg = _cfg(tmp_path)

    def ler(cfg_, conferencias, saida):  # M3: cada aluno com a senha dele
        ana, bia = conferencias
        ana.lista = [_linha("100")]
        bia.erro = "o site nao aceitou o login"
        return False

    saidas = []
    assert cs.executar_conferencia_site(cfg, _resultado(), _respostas("CONFERIR"), saidas.append, ler=ler) == 0
    relatorio = next((tmp_path / "relatorios").glob("conferencia_site_*.csv"))
    with open(relatorio, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    assert [(l["aluno"], l["tema"], l["resultado"]) for l in linhas] == [
        ("Ana Souza", "100", cs.NO_SITE), ("Ana Souza", "000", cs.FORA_DO_SITE),
        ("Ana Souza", "000", cs.FORA_DO_SITE), ("Bia Lima", "100", cs.NAO_CONFERIDO)]
    assert any("Nada foi enviado" in s for s in saidas)


def test_conferencia_nunca_importa_o_envio_de_item():
    fonte = Path(cs.__file__).read_text(encoding="utf-8")
    assert "enviar_item" not in fonte and "Enviar resposta" not in fonte and ".marcar(" not in fonte


@pytest.mark.parametrize("extra", [["--envio-real"], ["--modo-teste"], ["--revisar"], ["--ensaio", "2"]])
def test_conferir_site_roda_sozinho(extra):
    import main as main_mod
    assert main_mod.main(["--conferir-site", *extra]) == 2
