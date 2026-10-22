# -*- coding: utf-8 -*-
"""Testes offline da T45: conferência mais curta, próximo passo (ensaio) e
log em arquivo. Sem navegador. A RAIZ é temporária (conftest)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.config import Config


def _main(tmp_path, monkeypatch):
    import main as main_mod
    raiz = tmp_path / "Redações plataforma"
    for pasta, arquivos in {"3B - Sem tema": ["Ana Souza.JPG", "Ana.JPG", "Fulano.JPG", "Bia em branco.JPG"],
                            "100 - Tema": ["Ana Souza.JPG"]}.items():
        (raiz / pasta).mkdir(parents=True)
        for nome in arquivos:
            (raiz / pasta / nome).write_bytes(nome.encode())
    cfg = Config()
    cfg.pasta_raiz = raiz
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Nome;Email\nAna Souza;ana@x.com\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    return main_mod


def test_pasta_sem_tema_vira_uma_linha_e_pasta_com_tema_lista_arquivos(tmp_path, monkeypatch, capsys):
    assert _main(tmp_path, monkeypatch).main([]) == 0
    saida = capsys.readouterr().out
    assert "sem tema aprovado: nenhum arquivo vai ate escolher o tema" in saida
    assert "nomes: 1 exato(s), 1 parecido(s), 1 sem aluno, 1 para decidir a mao" in saida
    assert "SEM_CODIGO: Fulano.JPG" not in saida
    assert "✔ EXATO_UNICO: Ana Souza.JPG -> Ana Souza" in saida


def test_com_fila_sugere_o_ensaio(tmp_path, monkeypatch, capsys):
    assert _main(tmp_path, monkeypatch).main([]) == 0
    assert "python main.py --ensaio 3" in capsys.readouterr().out


def test_log_vai_para_logs_automacao(tmp_path, monkeypatch):
    import logging
    assert _main(tmp_path, monkeypatch).main([]) == 0
    logging.getLogger("automacao_redacoes").info("linha de teste do log")
    texto = (config_mod.RAIZ / "logs" / "automacao.log").read_text(encoding="utf-8")
    assert "INFO linha de teste do log" in texto
