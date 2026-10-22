# -*- coding: utf-8 -*-
"""Testes offline da T38: primeiro uso (--preparar e guia), pasta padrão.
Sem navegador. A RAIZ é temporária (conftest)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos import config as config_mod
from modulos.config import Config
from modulos.primeiro_uso import preparar, verificar


def test_pasta_padrao_e_redacoes_plataforma():
    assert Config().pasta_raiz == config_mod.RAIZ / "Redações plataforma"


def test_preparar_cria_o_que_falta_sem_sobrescrever(tmp_path):
    (tmp_path / ".env.example").write_text("ESQUEMA_SENHA_PADRAO=<definir>\n", encoding="utf-8")
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "Redações plataforma"
    cfg.planilha = tmp_path / "dados" / "dados_alunos.csv"
    saidas = []

    assert preparar(cfg, tmp_path, saida=saidas.append) == 0

    assert (cfg.pasta_raiz / "LEIA-ME.txt").read_text(encoding="utf-8").startswith("Coloque aqui")
    assert cfg.planilha.read_text(encoding="utf-8") == "Nome;Email\n"
    assert (tmp_path / ".env").is_file()
    assert any("criado:" in s for s in saidas)

    # Segunda vez: nada é recriado nem sobrescrito
    cfg.planilha.write_text("Nome;Email\nAna;ana@x.com\n", encoding="utf-8")
    saidas.clear()
    preparar(cfg, tmp_path, saida=saidas.append)
    assert cfg.planilha.read_text(encoding="utf-8") == "Nome;Email\nAna;ana@x.com\n"
    assert "  nada a criar: tudo ja existe." in saidas


def test_guia_aponta_o_que_falta(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "Redações plataforma"
    cfg.planilha = tmp_path / "dados_alunos.csv"
    cfg.planilha.write_text("Nome;Email\n", encoding="utf-8")  # só cabeçalho
    itens = verificar(cfg, tmp_path / ".env")
    assert [ok for ok, _, _ in itens] == [False, False, False]

    cfg.planilha.write_text("Nome;Email\nAna;ana@x.com\n", encoding="utf-8")
    (cfg.pasta_raiz / "100 - Tema").mkdir(parents=True)
    (cfg.pasta_raiz / "100 - Tema" / "Ana.JPG").write_bytes(b"x")
    (tmp_path / ".env").write_text("x", encoding="utf-8")
    assert all(ok for ok, _, _ in verificar(cfg, tmp_path / ".env"))


def test_main_sem_lista_de_alunos_explica_em_vez_de_quebrar(tmp_path, monkeypatch, capsys):
    import main as main_mod
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "Redações plataforma"
    cfg.planilha = tmp_path / "nao_existe.csv"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)

    assert main_mod.main([]) == 2
    saida = capsys.readouterr().out
    assert "python main.py --preparar" in saida
    assert "✘ Lista de alunos" in saida


def test_main_preparar(tmp_path, monkeypatch, capsys):
    import main as main_mod
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: Config())
    assert main_mod.main(["--preparar"]) == 0
    assert (config_mod.RAIZ / "Redações plataforma" / "LEIA-ME.txt").is_file()
    assert "=== Preparar (primeiro uso) ===" in capsys.readouterr().out
