# -*- coding: utf-8 -*-
"""Testes offline da T49: resolver as redações em REVISAO_MANUAL."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.progresso_relatorio import ENVIADO, ERRO, REVISAO_MANUAL, Progresso
from modulos.envio.fila_producao import montar_lote_producao
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.ferramentas.resolver import executar_resolver

ANA = Aluno("Ana Souza", "ana@x.com")
BIA = Aluno("Bia Lima", "bia@x.com")


def _banco(tmp_path):
    banco = tmp_path / "progresso.db"
    ontem = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    with Progresso(banco) as prog:
        prog.marcar(ANA.id, "100 - T/Ana Souza.JPG", REVISAO_MANUAL, pasta="100", detalhe="Confirmacao inconclusiva")
        prog.marcar(BIA.id, "100 - T/Bia Lima.JPG", REVISAO_MANUAL, pasta="100", detalhe="Confirmacao inconclusiva")
        prog.con.execute("UPDATE progresso SET atualizado_em = ?", (ontem,))
        prog.con.commit()
    return banco, ontem


def test_chegou_vira_enviado_nao_chegou_volta_para_a_fila(tmp_path):
    banco, ontem = _banco(tmp_path)
    respostas = iter(["s", "n"])
    saidas = []
    assert executar_resolver(banco, tmp_path, {ANA.id: ANA.nome, BIA.id: BIA.nome},
                             lambda _p: next(respostas), saidas.append) == 2
    with Progresso(banco) as prog:
        ana, bia = prog.obter(ANA.id, "100 - T/Ana Souza.JPG"), prog.obter(BIA.id, "100 - T/Bia Lima.JPG")
        assert ana["estado"] == ENVIADO and bia["estado"] == ERRO
        assert ana["atualizado_em"] == ontem  # data não muda: a contagem de hoje não é afetada
        assert prog.enviados_hoje(ANA.id, "100") == 0
        # Bia volta para o lote; Ana não
        (tmp_path / "100 - T").mkdir()
        for a in (ANA, BIA):
            (tmp_path / "100 - T" / f"{a.nome}.JPG").write_bytes(a.nome.encode())
        resultado = conciliar([ANA, BIA], {"100 - T": [f"{ANA.nome}.JPG", f"{BIA.nome}.JPG"]}, codigos_site=["100"])
        lotes, _ = montar_lote_producao(resultado, tmp_path, prog)
    assert [l.aluno for l in lotes] == [BIA]
    assert any("Ana Souza" in s for s in saidas)
    log = next(tmp_path.glob("resolucoes_*.csv")).read_text(encoding="utf-8-sig")
    assert "REVISAO_MANUAL;ENVIADO;s" in log and "REVISAO_MANUAL;ERRO;n" in log


def test_enter_deixa_como_esta_e_q_sai(tmp_path):
    banco, _ = _banco(tmp_path)
    respostas = iter(["", "q"])
    assert executar_resolver(banco, tmp_path, entrada=lambda _p: next(respostas), saida=lambda *_: None) == 0
    with Progresso(banco) as prog:
        assert prog.obter(ANA.id, "100 - T/Ana Souza.JPG")["estado"] == REVISAO_MANUAL


def test_sem_nada_para_resolver(tmp_path):
    saidas = []
    assert executar_resolver(tmp_path / "nao_existe.db", tmp_path, saida=saidas.append) == 0
    with Progresso(tmp_path / "p.db"):
        pass
    assert executar_resolver(tmp_path / "p.db", tmp_path, saida=saidas.append) == 0
    assert any("Nenhuma redação em revisão manual" in s for s in saidas)


def test_main_resolver_e_menu(monkeypatch):
    import main as main_mod
    from modulos.ferramentas import menu
    assert main_mod.main(["--resolver", "--envio-real"]) == 2
    monkeypatch.setattr("builtins.input", lambda _p: "q")
    assert main_mod.main(["--resolver"]) == 0
    assert menu.argumentos_da_opcao("7") == ["--resolver"]
