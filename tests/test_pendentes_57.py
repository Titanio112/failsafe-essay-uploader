# -*- coding: utf-8 -*-
"""Issue #57: reconferir só as contas pendentes, arquivo aberto no Excel e LEIA-ME na pasta da escola. Dados inventados."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import pendencias
from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.ferramentas import cadastro_aluno as cad
from modulos.ferramentas import menu
from modulos.site import conferencia_site as cs

TURMA = ("Escola A", "1A")
DA_TURMA = ["--escola", "Escola A", "--turma", "1A"]


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _cfg(tmp_path):
    cfg = Config()
    cfg.pasta_relatorios = tmp_path
    return cfg


def _resultado(nomes, arquivo=lambda n: f"{n}.jpg"):
    itens = [ItemConciliacao(pasta="100 - Tema", arquivo=arquivo(n), pessoa=n, estado=EXATO_UNICO,
                             aluno=Aluno(n, f"{n.split()[0].lower()}@x.example.com", senha="s"), codigo_tema="100")
             for n in nomes]
    return ResultadoConciliacao(itens=itens)


def _ler_que_anota(visto, com_erro=()):
    def ler(cfg, conferencias, saida):
        visto.append([c.aluno.nome for c in conferencias])
        for c in conferencias:
            if c.aluno.nome in com_erro:
                c.erro, c.tipo_erro = "o site nao aceitou o login", "login"
            else:
                c.lista = []  # conta aberta: a foto não está no site
        return False
    return ler


def _conferir(cfg, resultado, ler, *respostas, **kw):
    return cs.executar_conferencia_site(cfg, resultado, _resp(*respostas), lambda *_: None, ler=ler, **kw)


def test_so_pendentes_le_so_as_contas_que_nao_abriram_e_o_relatorio_fica_completo(tmp_path):
    cfg, visto = _cfg(tmp_path), []
    resultado = _resultado(["Ana Um", "Bia Dois", "Caio Tres"])
    _conferir(cfg, resultado, _ler_que_anota(visto, com_erro={"Bia Dois"}), "CONFERIR")
    assert visto == [["Ana Um", "Bia Dois", "Caio Tres"]]
    assert cs.preparacao_concluida(tmp_path, cfg.id_turma)[0] is False  # a Bia não abriu
    assert cs.contas_pendentes_hoje(tmp_path, cfg.id_turma) == 1

    # a Bia foi corrigida: só ela é aberta, e o relatório de hoje passa a estar completo
    _conferir(cfg, resultado, _ler_que_anota(visto), "CONFERIR", so_pendentes=True)
    assert visto[1] == ["Bia Dois"]
    assert cs.preparacao_concluida(tmp_path, cfg.id_turma) == (True, "")
    assert cs.contas_pendentes_hoje(tmp_path, cfg.id_turma) == 0
    linhas, _ = cs._linhas_de_hoje(tmp_path, cfg.id_turma)
    assert sorted(l["aluno"] for l in linhas) == ["Ana Um", "Bia Dois", "Caio Tres"]  # as conferidas vieram junto
    assert {l["resultado"] for l in linhas} == {cs.FORA_DO_SITE}


def test_sem_nada_pendente_nao_abre_conta_nenhuma(tmp_path):
    cfg, visto = _cfg(tmp_path), []
    resultado = _resultado(["Ana Um", "Bia Dois"])
    _conferir(cfg, resultado, _ler_que_anota(visto), "CONFERIR")
    assert _conferir(cfg, resultado, _ler_que_anota(visto), so_pendentes=True) == 0
    assert len(visto) == 1  # a 2ª vez nem chegou a abrir o navegador


def test_aluno_renomeado_ou_foto_trocada_nao_e_reaproveitado(tmp_path):
    cfg, visto = _cfg(tmp_path), []
    _conferir(cfg, _resultado(["Ana Um", "Bia Dois", "Caio Tres"]), _ler_que_anota(visto, com_erro={"Bia Dois"}), "CONFERIR")
    # a Bia virou "Bia D. Dois" (nome e foto) e a foto do Caio mudou de nome: as duas são lidas; a Ana não
    novo = _resultado(["Ana Um", "Bia D. Dois", "Caio Tres"], arquivo=lambda n: "Caio.jpg" if n == "Caio Tres" else f"{n}.jpg")
    _conferir(cfg, novo, _ler_que_anota(visto), "CONFERIR", so_pendentes=True)
    assert visto[1] == ["Bia D. Dois", "Caio Tres"]
    assert cs.preparacao_concluida(tmp_path, cfg.id_turma)[0] is True


def test_sem_conferencia_de_hoje_confere_todas_e_pergunta_so_quando_ha_o_que_reaproveitar(tmp_path):
    cfg, visto = _cfg(tmp_path), []
    resultado = _resultado(["Ana Um", "Bia Dois"])
    _conferir(cfg, resultado, _ler_que_anota(visto, com_erro={"Bia Dois"}), "CONFERIR", so_pendentes=True)
    assert visto == [["Ana Um", "Bia Dois"]]  # nada de hoje para aproveitar: todas
    # agora há (e a Bia segue pendente): o script pergunta; "n" = todas de novo, Enter = só as pendentes
    _conferir(cfg, resultado, _ler_que_anota(visto, com_erro={"Bia Dois"}), "n", "CONFERIR")
    assert visto[1] == ["Ana Um", "Bia Dois"]
    _conferir(cfg, resultado, _ler_que_anota(visto), "", "CONFERIR")
    assert visto[2] == ["Bia Dois"]


def test_depois_do_resolver_e_da_manual_o_menu_oferece_conferir_so_as_pendentes(tmp_path):
    chamadas = []
    from modulos.base.turma import raiz_redacoes
    cfg = _cfg(raiz_redacoes() / "Escola A" / "1A" / "relatorios")
    cfg.id_turma = "Escola A/1A"
    _conferir(cfg, _resultado(["Ana Um", "Bia Dois"]), _ler_que_anota([], com_erro={"Bia Dois"}), "CONFERIR")

    def main(argv):
        chamadas.append(argv)
        return 0
    menu.proximo_passo(["--resolver"], TURMA, main, _resp(""), lambda *_: None)  # Enter = sim
    assert chamadas == [["--conferir-site", "--so-pendentes"] + DA_TURMA]
    chamadas.clear()
    menu.proximo_passo(["--resolver"], TURMA, main, _resp("n"), lambda *_: None)
    assert chamadas == []
    pendencias.cadastro_mudou = True

    def main_que_conserta(argv):
        chamadas.append(argv)
        pendencias.cadastro_mudou = False
        return 0
    menu.proximo_passo(["--conferir-site"], TURMA, main_que_conserta, _resp(""), lambda *_: None)
    assert chamadas[0] == ["--conferir-site", "--so-pendentes"] + DA_TURMA


def test_resolver_sem_conferencia_pendente_nao_oferece_nada():
    chamadas = []
    menu.proximo_passo(["--resolver"], TURMA, lambda argv: chamadas.append(argv), _resp(), lambda *_: None)
    assert chamadas == []


def test_arquivo_aberto_repete_ate_gravar_e_p_desiste():
    tentativas, saidas = [], []

    def grava():
        tentativas.append(1)
        if len(tentativas) < 3:
            raise PermissionError(13, "Permission denied")
        return "ok"
    assert cad.gravar_com_nova_tentativa(grava, _resp("", ""), saidas.append) == "ok"
    assert len(tentativas) == 3 and "aberto em outro programa" in "\n".join(saidas)

    def sempre_recusa():
        raise PermissionError(13, "Permission denied")
    with pytest.raises(PermissionError):
        cad.gravar_com_nova_tentativa(sempre_recusa, _resp("", "p"), lambda *_: None)

    def sem_terminal(_):
        raise EOFError
    with pytest.raises(PermissionError):  # sem como perguntar: desiste em vez de ficar preso
        cad.gravar_com_nova_tentativa(sempre_recusa, sem_terminal, lambda *_: None)


def test_arquivo_trancado_nao_gera_copia_nem_escreve_pela_metade(tmp_path, monkeypatch):
    planilha = tmp_path / "alunos.csv"
    planilha.write_text("Nome;Email;Senha\nAna Um;ana@x.example.com;s1\n", encoding="utf-8")
    antes = planilha.read_bytes()

    def trancado(*a, **k):
        raise PermissionError(13, "Permission denied")
    monkeypatch.setattr(cad, "_exigir_gravavel", trancado)
    with pytest.raises(PermissionError):
        cad.trocar_nome(planilha, "ana@x.example.com", "Ana U.")
    with pytest.raises(PermissionError):
        cad.acrescentar_aluno(planilha, "Bia Dois", "bia@x.example.com", "s2")
    assert planilha.read_bytes() == antes and not list(tmp_path.glob("alunos.*.bak.csv"))


def test_leiame_fica_na_pasta_da_escola_e_nao_em_temas(tmp_path):
    from modulos.ferramentas.primeiro_uso import preparar
    cfg = Config()
    cfg.escola, cfg.turma = "Escola A", "1A"
    turma = tmp_path / "Redações plataforma" / "Escola A" / "1A"
    cfg.pasta_raiz, cfg.planilha = turma / "temas", turma / "alunos.csv"
    preparar(cfg, tmp_path, saida=lambda *_: None)
    assert (turma.parent / "LEIA-ME.md").read_text(encoding="utf-8").startswith("# Escola: Escola A")
    assert not (turma / "temas" / "LEIA-ME.md").exists()
