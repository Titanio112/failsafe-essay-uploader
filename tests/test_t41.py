# -*- coding: utf-8 -*-
"""Testes offline da T41: todo o visual do terminal mora em modulos/base/tela.py."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import tela

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def test_nenhum_outro_arquivo_tem_codigo_de_cor():
    """Visual modular: cor ANSI ("\\033[...m") só pode existir em tela.py."""
    padrao = re.compile(r"\\033\[|\\x1b\[|\x1b\[")
    achados = []
    for arquivo in sorted((RAIZ_PROJETO / "modulos").rglob("*.py")) + [RAIZ_PROJETO / "main.py"]:
        if arquivo.name == "tela.py":
            continue
        if padrao.search(arquivo.read_text(encoding="utf-8")):
            achados.append(str(arquivo.relative_to(RAIZ_PROJETO)))
    assert achados == []


def test_sem_terminal_nao_sai_cor():
    saidas = []
    tela.titulo("TESTE", saidas.append)
    tela.ok("deu certo", saidas.append)
    tela.contagens([("Enviados", 2, "ok"), ("Erros", 0, "erro")], saidas.append)
    assert not any("\033[" in s for s in saidas)
    assert "  ✔ deu certo" in saidas
    assert "  Enviados: 2" in saidas and "  Erros:    0" in saidas


def test_com_cores_cada_papel_tem_sua_cor(monkeypatch):
    monkeypatch.setitem(tela._cores, "ativas", True)
    saidas = []
    tela.ok("a", saidas.append)
    tela.erro("b", saidas.append)
    tela.aviso("c", saidas.append)
    assert "\033[32m" in saidas[0] and "\033[31m" in saidas[1] and "\033[33m" in saidas[2]
    # zero fica apagado (cinza), mesmo com papel de erro
    saidas.clear()
    tela.contagens([("Erros", 0, "erro")], saidas.append)
    assert "\033[90m0" in saidas[0]


def test_mudar_o_visual_e_so_mexer_no_tela(monkeypatch):
    """Ex.: trocar o símbolo de ok e a largura em tela.py muda a saída toda."""
    monkeypatch.setitem(tela.SIMBOLOS, "ok", "[OK]")
    monkeypatch.setattr(tela, "LARGURA", 20)
    saidas = []
    tela.ok("pronto", saidas.append)
    tela.cabecalho("X", saidas.append)
    assert "  [OK] pronto" in saidas
    assert "─" * 20 in saidas


def test_log_no_terminal_fica_curto():
    registro = logging.LogRecord("automacao_redacoes", logging.INFO, __file__, 1,
                                 "Envio confirmado: tema %s", ("0",), None)
    linha = tela.FormatoTerminal().format(registro)
    assert re.fullmatch(r"  \d\d:\d\d:\d\d • Envio confirmado: tema 0", linha)


def test_dry_run_tem_titulo_e_secoes(tmp_path, monkeypatch, capsys):
    import main as main_mod
    from modulos.base.config import Config
    redacoes = tmp_path / "Redações plataforma" / "100 - Tema"
    redacoes.mkdir(parents=True)
    (redacoes / "Ana Lalara.JPG").write_bytes(b"x")
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "Redações plataforma"
    cfg.turma = "Turma"  # M3: o main exige turma (aqui os caminhos já vêm prontos)
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Nome;Email\nAna Lalara;ana@x.com\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)

    assert main_mod.main([]) == 0
    saida = capsys.readouterr().out
    assert "CONFERÊNCIA  ·  alunos da lista  ·  nada é enviado" in saida
    for secao in ("── Dados ", "── Resumo ", "── Detalhes por tema ", "── Arquivos gerados "):
        assert secao in saida
    assert "✔ pronto: Ana Lalara.JPG → Ana Lalara" in saida
    assert "• Só conferência: nada foi enviado." in saida
