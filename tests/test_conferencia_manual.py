# -*- coding: utf-8 -*-
"""Issue #55: conferência manual guiada de identidade divergente e login recusado. Navegador e site são falsos."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO
from modulos.base.excecoes import CaptchaOuBloqueio
from modulos.base.turma import aplicar_turma, raiz_redacoes
from modulos.dados.planilha_arquivos import ItemConciliacao, ResultadoConciliacao, carregar_alunos
from modulos.site import conferencia_manual as cm
from modulos.site import conferencia_site as cs

LISTA = ("Nome;Email;Senha\n"
         "Davi Lucas de Moura Fontes;davi@x.example.com;s1\n"
         "Bia Dois;bia@x.example.com;s2\n"
         "Caio Tres;caio@x.example.com;s3\n")


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _cenario():
    pasta = raiz_redacoes() / "Escola A" / "1A"
    (pasta / "temas" / "100 - Tema").mkdir(parents=True)
    (pasta / "alunos.csv").write_text(LISTA, encoding="utf-8")
    (pasta / "temas" / "100 - Tema" / "Davi Lucas de Moura Fontes.jpg").write_bytes(b"x")
    cfg = Config()
    aplicar_turma(cfg, "Escola A", "1A")
    alunos = carregar_alunos(cfg)
    return pasta, cfg, alunos


def _conf(aluno, tipo, erro="x"):
    item = SimpleNamespace(pasta="100 - Tema", arquivo=f"{aluno.nome}.jpg")
    c = cs.ConferenciaAluno(aluno, [item])
    c.erro, c.tipo_erro = erro, tipo
    return c


def _abrir(nome_site):
    @contextmanager
    def abrir(cfg, aluno):
        yield nome_site
    return abrir


def _nunca_abrir(cfg, aluno):
    raise AssertionError("abriu o navegador")


def test_mesma_pessoa_troca_o_nome_na_lista_e_renomeia_a_foto_com_copia_e_log():
    pasta, cfg, alunos = _cenario()
    conf = _conf(alunos[0], "identidade")
    saidas = []
    r = _resp("s", "s")  # fazer a conferência manual; é a mesma pessoa
    n = cm.conferir_manualmente(cfg, [conf], r, saidas.append, abrir=_abrir("Davi L. de Moura Fontes"), alunos=alunos)
    assert n == 1
    linhas = (pasta / "alunos.csv").read_text(encoding="utf-8-sig").splitlines()
    assert linhas == ["Nome;Email;Senha", "Davi L. de Moura Fontes;davi@x.example.com;s1",
                      "Bia Dois;bia@x.example.com;s2", "Caio Tres;caio@x.example.com;s3"]  # só o nome mudou
    assert list(pasta.glob("alunos.*.bak.csv"))  # cópia antes
    assert (pasta / "temas" / "100 - Tema" / "Davi L. de Moura Fontes.jpg").is_file()
    assert not (pasta / "temas" / "100 - Tema" / "Davi Lucas de Moura Fontes.jpg").exists()
    assert list((pasta / "relatorios").glob("renomeacoes_*.csv"))  # dá para desfazer
    texto = "\n".join(saidas)  # os dois nomes, um embaixo do outro
    assert "Nome na planilha: Davi Lucas de Moura Fontes" in texto and "Nome no site:     Davi L. de Moura Fontes" in texto


def test_nao_e_a_mesma_pessoa_mostra_o_caminho_e_nao_mexe_na_lista():
    pasta, cfg, alunos = _cenario()
    antes = (pasta / "alunos.csv").read_bytes()
    conf = _conf(alunos[0], "identidade")
    saidas = []
    r = _resp("s", "n", "s")  # manual; NÃO é a mesma; "consegui" na mão
    assert cm.conferir_manualmente(cfg, [conf], r, saidas.append, abrir=_abrir("Outra Pessoa Qualquer"), alunos=alunos) == 1
    assert (pasta / "alunos.csv").read_bytes() == antes and not list(pasta.glob("alunos.*.bak.csv"))
    assert "alunos.csv" in "\n".join(saidas)
    r = _resp("s", "n", "n")  # e quando não conseguiu: pula
    assert cm.conferir_manualmente(cfg, [conf], r, lambda *_: None, abrir=_abrir("Outra Pessoa"), alunos=alunos) == 0


def test_senha_recusada_nao_abre_navegador_e_vai_direto_ao_caminho():
    pasta, cfg, alunos = _cenario()
    conf = _conf(alunos[1], "login", "o site nao aceitou o login")
    assert cm.conferir_manualmente(cfg, [conf], _resp("s", "s"), lambda *_: None, abrir=_nunca_abrir, alunos=alunos) == 1
    assert cm.conferir_manualmente(cfg, [conf], _resp("s", "n"), lambda *_: None, abrir=_nunca_abrir, alunos=alunos) == 0


def test_nome_do_site_igual_ao_de_outro_aluno_nao_troca_e_cai_no_manual():
    pasta, cfg, alunos = _cenario()
    antes = (pasta / "alunos.csv").read_bytes()
    conf = _conf(alunos[0], "identidade")
    r = _resp("s", "s", "n")  # é a mesma pessoa, mas o nome do site já é de outro aluno -> manual -> pula
    assert cm.conferir_manualmente(cfg, [conf], r, lambda *_: None, abrir=_abrir("Bia Dois"), alunos=alunos) == 0
    assert (pasta / "alunos.csv").read_bytes() == antes


def test_responder_n_no_inicio_nao_abre_nada_e_captcha_para_tudo():
    pasta, cfg, alunos = _cenario()
    conf = _conf(alunos[0], "identidade")
    assert cm.conferir_manualmente(cfg, [conf], _resp("n"), lambda *_: None, abrir=_nunca_abrir, alunos=alunos) == 0

    @contextmanager
    def captcha(cfg, aluno):
        raise CaptchaOuBloqueio("captcha")
        yield ""
    segunda = _conf(alunos[2], "identidade")
    saidas = []
    assert cm.conferir_manualmente(cfg, [conf, segunda], _resp("s"), saidas.append, abrir=captcha, alunos=alunos) == 0
    assert "CAPTCHA" in "\n".join(saidas) and "CONTA 2" not in "\n".join(saidas)


def test_conferencia_oferece_a_manual_e_se_o_cadastro_mudou_nao_oferece_enviar():
    pasta, cfg, alunos = _cenario()
    itens = [ItemConciliacao(pasta="100 - Tema", arquivo=f"{a.nome}.jpg", pessoa=a.nome, estado=EXATO_UNICO,
                             aluno=a, codigo_tema="100") for a in alunos[:2]]

    def ler(cfg_, conferencias, saida):
        for c in conferencias:  # ordem alfabética: por nome, não por posição
            if c.aluno.nome == "Bia Dois":
                c.lista = []  # conta aberta: a foto não está no site
            else:
                c.erro, c.tipo_erro = "identidade nao confere", "identidade"
        return False
    visto = {}

    def depois(faltam):
        visto["faltam"] = len(faltam)

    def guiada(problemas):
        visto["problemas"] = [c.aluno.nome for c in problemas]
        return visto.pop("muda", 0)
    # sem mudança no cadastro: segue para a oferta de envio das que faltam
    cs.executar_conferencia_site(cfg, ResultadoConciliacao(itens=itens), _resp("CONFERIR"), lambda *_: None, ler=ler,
                                 depois=depois, guiada=guiada)
    assert visto == {"problemas": ["Davi Lucas de Moura Fontes"], "faltam": 1}
    # cadastro mudou: não oferece enviar (a conferência já não vale)
    visto.clear()
    visto["muda"] = 1
    saidas = []
    cs.executar_conferencia_site(cfg, ResultadoConciliacao(itens=itens), _resp("CONFERIR"), saidas.append, ler=ler,
                                 depois=depois, guiada=guiada)
    assert "faltam" not in visto and "Conferir contas no site" in "\n".join(saidas)
