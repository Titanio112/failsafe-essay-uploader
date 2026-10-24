# -*- coding: utf-8 -*-
"""Testes offline da T51: links clicáveis para os arquivos, progresso ao
vivo do envio e envio sem janela do navegador. Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import tela
from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.base.progresso_relatorio import ENVIADO
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import fluxo_envio_producao as fep


# ─── Links ───────────────────────────────────────────────────

def test_link_so_no_terminal_de_verdade(tmp_path, monkeypatch):
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    arquivo = tmp_path / "Redações plataforma" / "3B - Filiação" / "Cecília em branco.JPG"
    assert tela.link("Cecília em branco.JPG", arquivo) == "Cecília em branco.JPG"  # sem TTY: só o texto
    monkeypatch.setitem(tela._cores, "ativas", True)
    texto = tela.link("Cecília em branco.JPG", arquivo)
    uri = tela.uri_de(arquivo)
    assert texto == f"\033]8;;{uri}\033\\Cecília em branco.JPG\033]8;;\033\\"
    # T52: espaço codificado, acentos NÃO (o Windows lê %C3%A7 como dois caracteres)
    assert uri.startswith("file:///") and "%20" in uri and "Redações" in uri and "%C3" not in uri
    duplo = tela.link_arquivo(tmp_path, "3B - Filiação", "Cecília em branco.JPG")
    assert duplo.count("\033]8;;file:") == 2  # pasta e arquivo clicáveis


def test_conferencia_poe_link_nos_arquivos(tmp_path, monkeypatch, capsys):
    import main as main_mod
    monkeypatch.delenv("TERM_PROGRAM", raising=False)
    raiz = tmp_path / "Redações plataforma"
    (raiz / "100 - Tema").mkdir(parents=True)
    (raiz / "100 - Tema" / "Ana em branco.JPG").write_bytes(b"x")
    cfg = Config()
    cfg.pasta_raiz = raiz
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Nome;Email\nAna Souza;ana@x.com\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    monkeypatch.setattr(tela, "ativar_cores", lambda: tela._cores.__setitem__("ativas", True))
    monkeypatch.setitem(tela._cores, "ativas", False)
    assert main_mod.main([]) == 0
    saida = capsys.readouterr().out
    alvo = tela.uri_de(raiz / "100 - Tema" / "Ana em branco.JPG")
    assert f"\033]8;;{alvo}\033\\Ana em branco.JPG" in saida


# ─── Progresso ───────────────────────────────────────────────

@pytest.mark.parametrize("segundos, texto", [(5, "5 s"), (90, "1 min 30 s"), (900, "15 min"), (3720, "1 h 2 min")])
def test_tempo_legivel(segundos, texto):
    assert tela.tempo(segundos) == texto


def test_linha_de_progresso():
    assert "calculando o tempo" in tela.linha_progresso(0, 10, 0)
    linha = tela.linha_progresso(5, 20, 300)  # 5 em 5 min -> 15 faltando ~15 min
    assert "5 de 20 redações" in linha and " 25%" in linha
    assert "passou 5 min 00 s" in linha and "faltam ~15 min" in linha
    assert "terminado" in tela.linha_progresso(20, 20, 1200)


def test_andamento_conta_itens_pulados_e_nao_repete_linha():
    linhas, agora = [], [0.0]
    andamento = fep.Andamento(4, linhas.append, relogio=lambda: agora[0])
    agora[0] = 60
    andamento.avancar()
    andamento.chegar_a(1)  # nada mudou: não imprime de novo
    agora[0] = 120
    andamento.chegar_a(3)  # aluno com login falho: 2 itens pulados
    assert len(linhas) == 2
    assert "1 de 4" in linhas[0] and "faltam ~3 min" in linhas[0]
    assert "3 de 4" in linhas[1] and "faltam ~40 s" in linhas[1]


def test_envio_mostra_o_progresso(tmp_path, capsys):
    teste = Aluno(NOME_CONTA_TESTE, "teste@teste.com")
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    arquivos = {}
    for pasta in ("3B - A", "3B - B"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / f"{teste.nome}.jpg").write_bytes(pasta.encode())
        arquivos[pasta] = [f"{teste.nome}.jpg"]
    resultado = conciliar([teste], arquivos, codigos_site=["000"],
                          codigos_pasta={"3B - A": "000", "3B - B": "000"})
    with patch.object(fep, "sync_playwright") as pw, patch.object(fep, "obter_senha", return_value="s"), \
         patch.object(fep, "verificar_dominio_autorizado"), patch.object(fep, "login"), \
         patch.object(fep, "confirmar_identidade"), patch.object(fep, "logout"), \
         patch.object(fep, "enviar_item", return_value=ENVIADO), \
         patch("builtins.input", return_value="ENVIAR TESTE"):
        pw.return_value.__enter__.return_value.chromium.launch.return_value = MagicMock()
        assert fep.executar_envio_producao(cfg, resultado, conta_teste=teste.email) == 0
    saida = capsys.readouterr().out
    assert "1 de 2 redações" in saida and "2 de 2 redações" in saida and "terminado" in saida


# ─── Sem janela ──────────────────────────────────────────────

def test_sem_janela_liga_o_headless(tmp_path, monkeypatch):
    import main as main_mod
    cfg = Config()
    assert cfg.headless is False  # padrão: mostra o navegador
    cfg.pasta_raiz = tmp_path / "nao_existe"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    main_mod.main(["--sem-janela"])
    assert cfg.headless is True
