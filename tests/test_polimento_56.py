# -*- coding: utf-8 -*-
"""Issue #56: Enter = sim, textos sem número de menu, erro de conta inteiro, conferir de novo e motivo do bloqueio."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import pendencias, relogio, tela
from modulos.base.turma import raiz_redacoes
from modulos.dados.planilha_arquivos import Aluno
from modulos.ferramentas import menu
from modulos.site import conferencia_manual, confirmacao
from modulos.site import conferencia_site as cs

RAIZ = Path(__file__).resolve().parent.parent
TURMA = ("Escola A", "1A")
DA_TURMA = ["--escola", "Escola A", "--turma", "1A"]


def _resp(*r):
    it = iter(r)
    return lambda _: next(it)


def _sem_espacos_extras(linhas) -> str:
    return " ".join("\n".join(linhas).split())


def test_enter_e_s_sao_sim_n_e_qualquer_outra_coisa_e_nao_e_sem_terminal_e_nao():
    for resposta in ("", "s", "S", "sim", "  "):
        assert tela.sim("Continuar?", _resp(resposta)) is True
    for resposta in ("n", "nao", "talvez"):
        assert tela.sim("Continuar?", _resp(resposta)) is False

    def sem_terminal(_):
        raise EOFError
    assert tela.sim("Continuar?", sem_terminal) is False  # nunca confirma sozinho
    visto = []
    tela.sim("Continuar?", lambda p: visto.append(p) or "n")
    assert "Enter/s = sim" in visto[0] and "n = não" in visto[0]


def test_nenhum_texto_do_script_cita_numero_de_menu():
    """Os números mudam quando o menu muda; os textos citam o NOME da etapa."""
    achados = []
    for arquivo in [RAIZ / "main.py", *sorted((RAIZ / "modulos").rglob("*.py"))]:
        for n, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\b[Mm]enu \d|menu opção \d|\b\d+\) (Configura|Conferir|Revisar|Enviar)", linha):
                achados.append(f"{arquivo.name}:{n}: {linha.strip()}")
    assert achados == []


def test_a_conferencia_manual_importa_o_logout_certo():
    assert conferencia_manual.logout is confirmacao.logout  # o ImportError do teste real (issue #56)


def test_erro_de_conta_sai_inteiro_sem_cortar_e_o_bloco_de_atencao_vem_em_grupos():
    erro = "o site nao aceitou o login (senha do alunos.csv errada? conta bloqueada?)"
    a = Aluno("Aluno Com Nome Bem Comprido Para Quebrar Linha", "a@x.example.com", senha="s")
    login = cs.ConferenciaAluno(a, [])
    login.erro, login.tipo_erro = erro, "login"
    ident = cs.ConferenciaAluno(Aluno("Bia Dois", "b@x.example.com", senha="s"), [])
    longo = "o site abriu a conta de outra pessoa " + "e depois mostrou mais um texto bem grande " * 3
    ident.erro, ident.tipo_erro = longo, "identidade"
    outro = cs.ConferenciaAluno(Aluno("Caio Tres", "c@x.example.com"), [])
    outro.erro = "sem senha no alunos.csv da turma"
    saidas = []
    cs._mostrar_aluno(login, RAIZ, saidas.append)
    texto = _sem_espacos_extras(saidas)
    assert "…" not in texto and erro in texto
    assert max(len(s) for s in saidas) <= tela.LARGURA

    saidas.clear()
    cs._mostrar_problemas([outro, ident, login], saidas.append)
    texto = _sem_espacos_extras(saidas)
    assert "…" not in texto and longo.strip() in texto
    ordem = [texto.index(t) for t in ("Senha ou login recusado pelo site (1)",
                                      "Nome no site diferente do nome na lista (1)", "Outros problemas (1)")]
    assert ordem == sorted(ordem)


def _conferencia(linhas):
    """Relatório de hoje da turma 1A: ``linhas`` = [(aluno, resultado)]."""
    pasta = raiz_redacoes() / "Escola A" / "1A" / "relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    with open(pasta / f"conferencia_site_{relogio.agora():%Y%m%d}_100000.csv", "w", encoding="utf-8-sig",
              newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cs.COLUNAS_CSV)
        for i, (aluno, resultado) in enumerate(linhas):
            w.writerow([aluno, "100 - Tema", f"{aluno} {i}.jpg", "100", resultado, 0, "", "", "Escola A/1A"])


def _menu():
    saidas = []
    menu.mostrar_menu(saidas.append, TURMA)
    return _sem_espacos_extras(saidas)


def test_menu_diz_por_que_o_enviar_esta_bloqueado(monkeypatch):
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    assert "bloqueado: falta conferir as contas no site hoje" in _menu()
    # 2 contas sem abrir (a 1ª com 2 redações): o menu conta as CONTAS e as redações
    _conferencia([("Ana", cs.NAO_CONFERIDO), ("Ana", cs.NAO_CONFERIDO), ("Bia", cs.NAO_TENTADO), ("Caio", cs.NO_SITE)])
    texto = _menu()
    assert "restam 2 conta(s) sem conferir (3 redação(ões))" in texto and 'conclua "Conferir contas no site"' in texto
    # tudo certo e tudo no site: Enviar as que faltam explica que não há o que enviar; Enviar para os alunos libera
    _conferencia([("Ana", cs.NO_SITE), ("Bia", cs.NO_SITE)])
    texto = _menu()
    assert "nada falta enviar: nenhuma das 2 redações conferidas está ausente do site" in texto
    assert texto.count("bloqueado") == 1
    saidas = []
    menu.executar_menu(lambda argv: 0, _resp("5", "", "0"), saidas.append, turma=TURMA)
    assert "Enviar bloqueado: nada falta enviar" in "\n".join(saidas)
    # a trava de produção aparece com o nome da constante, por cima de tudo
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)
    assert "trava de produção ligada (PRODUCAO_BLOQUEADA em modulos/base/config.py)" in _menu()


def test_cadastro_mudou_oferece_conferir_de_novo_e_enter_aceita():
    chamadas = []
    pendencias.revisao_pendente = False
    pendencias.cadastro_mudou = True

    def main(argv):
        chamadas.append(argv)
        pendencias.cadastro_mudou = False  # a nova conferência já não muda o cadastro
        return 0
    menu.proximo_passo(["--conferir-site"], TURMA, main, _resp(""), lambda *_: None)  # Enter = sim
    assert chamadas == [["--conferir-site"] + DA_TURMA]
    pendencias.cadastro_mudou = True
    menu.proximo_passo(["--conferir-site"], TURMA, main, _resp("n"), lambda *_: None)
    assert chamadas == [["--conferir-site"] + DA_TURMA]  # "n" volta ao menu sem conferir
    pendencias.cadastro_mudou = False


def test_conferencia_marca_que_o_cadastro_mudou_quando_a_manual_corrige_algo(monkeypatch):
    from modulos.base.estados import EXATO_UNICO
    from modulos.base.config import Config
    from modulos.dados.planilha_arquivos import ItemConciliacao, ResultadoConciliacao
    aluno = Aluno("Ana Um", "ana@x.example.com", senha="s")
    item = ItemConciliacao(pasta="100 - Tema", arquivo="Ana Um.jpg", pessoa="Ana Um", estado=EXATO_UNICO, aluno=aluno,
                           codigo_tema="100")

    def ler(cfg, conferencias, saida):
        conferencias[0].erro, conferencias[0].tipo_erro = "identidade nao confere", "identidade"
        return False
    pendencias.cadastro_mudou = False
    cs.executar_conferencia_site(Config(), ResultadoConciliacao(itens=[item]), _resp("CONFERIR"), lambda *_: None,
                                 ler=ler, guiada=lambda problemas: 1)
    assert pendencias.cadastro_mudou is True
    cs.executar_conferencia_site(Config(), ResultadoConciliacao(itens=[item]), _resp("CONFERIR"), lambda *_: None,
                                 ler=ler, guiada=lambda problemas: 0)
    assert pendencias.cadastro_mudou is False  # cada conferência começa limpa
