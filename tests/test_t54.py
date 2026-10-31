# -*- coding: utf-8 -*-
"""Testes offline da T54: tela da conferência em colunas curtas, aviso
quando não falta nada e menu 7 (enviar as que faltam pela conferência de
hoje). Sem navegador."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import relogio, tela
from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.ferramentas import menu
from modulos.site import conferencia_site as cs
from modulos.site.lista_redacoes import ItemListaRedacao

ANA = Aluno(nome="Ana Souza", email="ana@x.com", senha="s")
PASTA_LONGA = "3B - Impactos da Invisibilidade da filiação para o cidadão brasileiro"


def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


def _item(pasta, codigo, aluno=ANA):
    return ItemConciliacao(pasta=pasta, arquivo=f"{aluno.nome}.JPG", pessoa=aluno.nome, estado="EXATO_UNICO",
                           aluno=aluno, codigo_tema=codigo)


def _linha(codigo):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- X", data="30/09/2026", situacao="Correção finalizada")


def test_cada_foto_cabe_numa_linha(tmp_path):
    conf = cs.alunos_para_conferir(ResultadoConciliacao(itens=[_item("3B - Efeitos", "000"),
                                                               _item(PASTA_LONGA, "100")]))[0]
    conf.lista = [_linha("000"), _linha("000")]
    cs.comparar(conf)
    saidas = []
    cs._mostrar_aluno(conf, tmp_path, saidas.append)
    linhas = [s for s in saidas if "tema" in s]
    assert all(len(s) <= tela.LARGURA for s in linhas)
    assert "no site" in linhas[0] and "30/09/2026" in linhas[0]
    assert "outro tema?" in linhas[1] and "como 000?" in linhas[1] and "…" in linhas[1]
    assert not any("Ana Souza.JPG" in s for s in saidas)  # o nome do aluno já está no cabeçalho


def test_linha_com_link_tambem_cabe(tmp_path, monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    monkeypatch.setitem(tela._cores, "ativas", True)
    conf = cs.alunos_para_conferir(ResultadoConciliacao(itens=[_item(PASTA_LONGA, "100")]))[0]
    conf.lista = []
    cs.comparar(conf)
    saidas = []
    cs._mostrar_aluno(conf, tmp_path, saidas.append)
    visivel = re.sub(r"\033\]8;;[^\033]*\033\\|\033\[[0-9;]*m", "", saidas[-1])
    assert len(visivel) <= tela.LARGURA and "\033]8;;file:" in saidas[-1]


def _cfg(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    return cfg


def test_sem_faltar_nada_diz_por_que_nao_pergunta(tmp_path, monkeypatch):
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "x")
    saidas, chamado = [], []

    def ler(cfg_, conferencias, saida):  # M3: cada aluno com a senha dele
        conferencias[0].lista = [_linha("000")]
        return False

    cs.executar_conferencia_site(_cfg(tmp_path), ResultadoConciliacao(itens=[_item("A", "000")]),
                                 _respostas("CONFERIR", "n"), saidas.append, ler=ler, depois=chamado.append)
    assert not chamado and any("Não falta enviar nenhuma" in s for s in saidas)


def _relatorio(pasta: Path, data: str, linhas):
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"conferencia_site_{data}_010000.csv"
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cs.COLUNAS_CSV)
        for aluno, pasta_tema, resultado in linhas:
            w.writerow([aluno, pasta_tema, f"{aluno}.JPG", "100", resultado, 0, "", ""])
    return caminho


def test_faltantes_do_relatorio_de_hoje(tmp_path):
    hoje = relogio.agora().strftime("%Y%m%d")
    _relatorio(tmp_path, hoje, [("Ana Souza", "F", cs.FORA_DO_SITE), ("Ana Souza", "G", cs.OUTRO_TEMA),
                                ("Ana Souza", "H", cs.FORA_DO_SITE)])  # H não está mais na pasta
    resultado = ResultadoConciliacao(itens=[_item("F", "100"), _item("G", "100")])
    faltam = cs.faltantes_do_relatorio(tmp_path, resultado, lambda *_: None)
    assert [i.pasta for i in faltam] == ["F"]


def test_relatorio_de_outro_dia_nao_vale(tmp_path):
    _relatorio(tmp_path, "20200101", [("Ana Souza", "F", cs.FORA_DO_SITE)])
    saidas = []
    resultado = ResultadoConciliacao(itens=[_item("F", "100")])
    assert cs.faltantes_do_relatorio(tmp_path, resultado, saidas.append) is None
    assert any("não é de hoje" in s for s in saidas)


def test_sem_relatorio(tmp_path):
    assert cs.faltantes_do_relatorio(tmp_path, ResultadoConciliacao(itens=[]), lambda *_: None) is None


def test_menu_7_bloqueado_hoje(monkeypatch):
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)
    saidas = []
    assert menu.argumentos_da_opcao("7", _respostas(), saida=saidas.append) is None
    assert any("BLOQUEADO" in s for s in saidas)
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    assert menu.argumentos_da_opcao("7", _respostas()) == ["--enviar-faltantes"]


def test_enviar_faltantes_roda_sozinho():
    import main as main_mod
    assert main_mod.main(["--enviar-faltantes", "--conferir-site"]) == 2
    assert main_mod.main(["--enviar-faltantes", "--envio-real"]) == 2


def test_log_so_no_arquivo_nao_aparece_na_tela(tmp_path, capsys):
    import logging
    from modulos.base.progresso_relatorio import configurar_logging
    log = configurar_logging(tmp_path)
    log.info("so no arquivo", extra={"so_no_arquivo": True})
    log.info("nos dois")
    for h in log.handlers:
        h.flush()
    tela_saida = capsys.readouterr().out
    assert "so no arquivo" not in tela_saida and "nos dois" in tela_saida
    assert "so no arquivo" in (tmp_path / "automacao.log").read_text(encoding="utf-8")
    logging.getLogger("automacao_redacoes").handlers.clear()
