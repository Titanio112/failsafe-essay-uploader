# -*- coding: utf-8 -*-
"""Testes offline da T57: `v` na parte dos temas da revisão, limite no
menu 6, aviso da coluna Senha só no log, arquivo morto, log com o comando
e nome repetido de redação já enviada. Sem navegador."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base import tela
from modulos.base.progresso_relatorio import ENVIADO, Progresso
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.envio.fila_producao import montar_lote_producao
from modulos.envio.fila_teste import hash_do_arquivo
from modulos.ferramentas import arquivo_morto, menu
from modulos.ferramentas.revisao_interativa import revisar_pastas


def _respostas(*r):
    it = iter(r)
    return lambda _p: next(it)


# ─── v na parte dos temas ────────────────────────────────────

def test_v_na_parte_dos_temas_abre_a_pasta(tmp_path, monkeypatch):
    abertos = []
    monkeypatch.setattr(tela, "abrir", lambda alvo: abertos.append(Path(alvo).name) or "")
    temas = [("53", "53- Impactos da evasão escolar para o Brasil"), ("000", "000- DISSERTATIVO")]
    saidas = []
    revisar_pastas(["impactos da evasão escolar"], temas, tmp_path / "p.csv",
                   entrada=_respostas("v", "q"), saida=saidas.append, pasta_raiz=tmp_path)
    assert abertos == ["impactos da evasão escolar"]
    assert not any('Nenhum tema tem "v"' in s for s in saidas)  # antes, "v" virava busca


def test_sem_pasta_raiz_v_continua_sendo_busca(tmp_path):
    saidas = []
    revisar_pastas(["x"], [("53", "53- Tema")], tmp_path / "p.csv", entrada=_respostas("v", "q"),
                   saida=saidas.append)
    assert any('tem "v"' in s for s in saidas)


# ─── Menu 6 com limite ───────────────────────────────────────

def test_menu_6_pergunta_o_limite(monkeypatch):
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)
    assert menu.argumentos_da_opcao("6", _respostas("1", "1")) == [
        "--envio-real", "--limite-alunos", "1", "--limite-redacoes", "1"]
    assert menu.argumentos_da_opcao("6", _respostas("", "")) == ["--envio-real"]
    assert menu.argumentos_da_opcao("6", _respostas("zero"), saida=lambda *_: None) is None


def test_menu_6_bloqueado_nao_pergunta(monkeypatch):
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", True)
    assert menu.argumentos_da_opcao("6", _respostas(), saida=lambda *_: None) is None


# ─── Aviso da coluna Senha ───────────────────────────────────

def test_aviso_da_senha_nao_aparece_na_tela(tmp_path, capsys):
    import warnings
    from modulos.base.config import Config
    from modulos.dados.planilha_arquivos import carregar_alunos
    cfg = Config()
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Nome;Email;Senha\nAna Souza;ana@x.com;123\n", encoding="utf-8")
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        assert len(carregar_alunos(cfg)) == 1
    assert "Coluna 'Senha'" not in capsys.readouterr().out


# ─── Arquivo morto ───────────────────────────────────────────

def _pasta_com_fotos(raiz: Path, nome: str, n: int) -> Path:
    pasta = raiz / nome
    pasta.mkdir(parents=True)
    for i in range(n):
        (pasta / f"Aluno {i}.JPG").write_bytes(b"x")
    return pasta


def test_arquiva_as_escolhidas_sem_apagar(tmp_path):
    raiz = tmp_path / "Redações plataforma"
    _pasta_com_fotos(raiz, "3B - Velha", 2)
    _pasta_com_fotos(raiz, "3B - Nova", 1)
    (raiz / "LEIA-ME.md").write_text("x", encoding="utf-8")
    r = arquivo_morto.executar_arquivar(raiz, tmp_path, tmp_path / "relatorios",
                                        _respostas("2", "s"), lambda *_: None)
    assert r == 0
    assert sorted(p.name for p in raiz.iterdir()) == ["3B - Nova", "LEIA-ME.md"]
    destino = next((tmp_path / "Arquivo morto").iterdir())
    assert sorted(p.name for p in (destino / "3B - Velha").iterdir()) == ["Aluno 0.JPG", "Aluno 1.JPG"]
    log = next((tmp_path / "relatorios").glob("arquivamento_*.csv"))
    with open(log, encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    assert len(linhas) == 1 and linhas[0]["origem"].endswith("3B - Velha")


def test_arquivar_nao_move_sem_confirmar(tmp_path):
    raiz = tmp_path / "R"
    _pasta_com_fotos(raiz, "A", 1)
    assert arquivo_morto.executar_arquivar(raiz, tmp_path, tmp_path / "rel", _respostas("t", "n"),
                                           lambda *_: None) == 0
    assert (raiz / "A").is_dir() and not (tmp_path / "Arquivo morto").exists()


def test_arquivar_resposta_invalida(tmp_path):
    raiz = tmp_path / "R"
    _pasta_com_fotos(raiz, "A", 1)
    assert arquivo_morto.executar_arquivar(raiz, tmp_path, tmp_path / "rel", _respostas("9"),
                                           lambda *_: None) == 2
    assert (raiz / "A").is_dir()


def test_arquivar_espera_o_envio(tmp_path):
    from modulos.base.trava import trava_de_envio
    raiz = tmp_path / "R"
    _pasta_com_fotos(raiz, "A", 1)
    with trava_de_envio(tmp_path / "rel" / "envio.trava"):
        assert arquivo_morto.executar_arquivar(raiz, tmp_path, tmp_path / "rel", _respostas("t", "s"),
                                               lambda *_: None) == 2
    assert (raiz / "A").is_dir()


def test_menu_11_arquivo_morto():
    assert menu.argumentos_da_opcao("11") == ["--arquivar"]


# ─── Log com o comando ───────────────────────────────────────

def test_log_registra_o_comando(tmp_path):
    import logging
    import main as main_mod
    main_mod.main(["--resolver"])
    for h in logging.getLogger("automacao_redacoes").handlers:
        h.flush()
    texto = (config_mod.RAIZ / "logs" / "automacao.log").read_text(encoding="utf-8")
    assert "Inicio: python main.py --resolver" in texto


# ─── Nome repetido de redação já enviada ─────────────────────

def test_nome_repetido_com_foto_nova_explica_e_nao_envia(tmp_path):
    ana = Aluno(nome="Ana Souza", email="ana@x.com")
    (tmp_path / "3B - Tema").mkdir()
    foto = tmp_path / "3B - Tema" / "Ana Souza.JPG"
    foto.write_bytes(b"foto antiga")
    item = ItemConciliacao(pasta="3B - Tema", arquivo="Ana Souza.JPG", pessoa="Ana Souza",
                           estado="EXATO_UNICO", aluno=ana, codigo_tema="000")
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ana.id, item.chave, ENVIADO, pasta="000", hash_arquivo=hash_do_arquivo(foto))
        foto.write_bytes(b"foto NOVA da semana seguinte")
        lotes, ignorados = montar_lote_producao(ResultadoConciliacao(itens=[item]), tmp_path, prog)
    assert lotes == []
    assert "FOTO E OUTRA" in ignorados[0][1]
