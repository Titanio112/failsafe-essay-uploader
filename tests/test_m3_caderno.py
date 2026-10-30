# -*- coding: utf-8 -*-
"""M3 (parte B): caderno único com a turma, registros antigos, ações da turma.

Só bancos e pastas fictícios (tmp_path). Sem navegador, sem login, sem envio."""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import relogio
from modulos.base.estados import EXATO_UNICO
from modulos.base.progresso_relatorio import ENVIADO, REVISAO_MANUAL, Progresso
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao
from modulos.envio.fila_producao import montar_lote_producao
from modulos.envio.fila_teste import hash_do_arquivo

ANA = Aluno("Ana Um", "ana@um.example.com", senha="s")
BIA = Aluno("Bia Dois", "bia@dois.example.com", senha="s")


def _banco_antigo(caminho: Path, linhas) -> None:
    """Caderno como era antes da M3 (sem a coluna turma)."""
    con = sqlite3.connect(caminho)
    con.execute("""CREATE TABLE progresso (aluno_id TEXT NOT NULL, arquivo TEXT NOT NULL, pasta TEXT DEFAULT '',
                   estado TEXT NOT NULL, tentativas INTEGER NOT NULL DEFAULT 0, detalhe TEXT DEFAULT '',
                   hash_arquivo TEXT DEFAULT '', criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL,
                   PRIMARY KEY (aluno_id, arquivo))""")
    for aluno_id, arquivo, estado, h in linhas:
        con.execute("INSERT INTO progresso VALUES (?, ?, '100', ?, 0, '', ?, '2026-10-01T10:00:00+00:00', "
                    "'2026-10-01T10:00:00+00:00')", (aluno_id, arquivo, estado, h))
    con.commit()
    con.close()


def _foto(raiz: Path, pasta: str, arquivo: str, conteudo: bytes) -> Path:
    (raiz / pasta).mkdir(parents=True, exist_ok=True)
    (raiz / pasta / arquivo).write_bytes(conteudo)
    return raiz / pasta / arquivo


def _fila(aluno, pasta, arquivo):
    return ResultadoConciliacao(itens=[ItemConciliacao(pasta=pasta, arquivo=arquivo, pessoa=aluno.nome,
                                                       estado=EXATO_UNICO, aluno=aluno, codigo_tema="100")])


def test_caderno_antigo_ganha_a_coluna_com_copia_e_continua_impedindo_reenvio(tmp_path):
    banco = tmp_path / "relatorios" / "progresso.db"
    banco.parent.mkdir()
    temas = tmp_path / "Escola Um" / "3A" / "temas"
    foto = _foto(temas, "100 - Tema", "Ana Um.jpg", b"foto da ana")
    _banco_antigo(banco, [(ANA.id, "100 - Tema/Ana Um.jpg", ENVIADO, hash_do_arquivo(foto))])

    with Progresso(banco, "Escola Um/3A") as prog:
        assert prog.con.execute("SELECT turma FROM progresso").fetchall() == [("",)]
        assert len(list((banco.parent / "copias").glob("progresso_*.db"))) == 1  # cópia antes de mexer
        lotes, ignorados = montar_lote_producao(_fila(ANA, "100 - Tema", "Ana Um.jpg"), temas, prog)
        assert lotes == [] and "ja registrado como ENVIADO" in ignorados[0][1]
        # a mesma foto com outro nome também não volta
        _foto(temas, "100 - Tema", "Ana Um 2.jpg", b"foto da ana")
        lotes, ignorados = montar_lote_producao(_fila(ANA, "100 - Tema", "Ana Um 2.jpg"), temas, prog)
        assert lotes == [] and "mesma foto ja registrada" in ignorados[0][1]
    with Progresso(banco, "Escola Um/3A"):  # abrir de novo não copia nem migra outra vez
        pass
    assert len(list((banco.parent / "copias").glob("progresso_*.db"))) == 1


def test_registro_novo_leva_a_turma_e_registro_existente_nao_troca(tmp_path):
    with Progresso(tmp_path / "p.db", "Escola Um/3A") as prog:
        prog.marcar(ANA.id, "100 - Tema/Ana Um.jpg", "A_ENVIAR")
    with Progresso(tmp_path / "p.db", "Escola Dois/3A") as prog:
        prog.marcar(ANA.id, "100 - Tema/Ana Um.jpg", ENVIADO)
        assert prog.con.execute("SELECT turma, estado FROM progresso").fetchall() == [("Escola Um/3A", ENVIADO)]


def test_foto_de_outro_aluno_e_barrada_entre_turmas(tmp_path):
    um, dois = tmp_path / "Escola Um" / "temas", tmp_path / "Escola Dois" / "temas"
    foto_ana = _foto(um, "100 - Tema", "Ana Um.jpg", b"a mesma foto")
    _foto(dois, "100 - Tema", "Bia Dois.jpg", b"a mesma foto")
    with Progresso(tmp_path / "p.db", "Escola Um/3A") as prog:
        prog.marcar(ANA.id, "100 - Tema/Ana Um.jpg", ENVIADO, pasta="100", hash_arquivo=hash_do_arquivo(foto_ana))
    with Progresso(tmp_path / "p.db", "Escola Dois/3A") as prog:
        lotes, ignorados = montar_lote_producao(_fila(BIA, "100 - Tema", "Bia Dois.jpg"), dois, prog)
    assert lotes == [] and "OUTRO aluno" in ignorados[0][1]


def test_contagem_do_dia_e_global(tmp_path):
    with Progresso(tmp_path / "p.db", "Escola Um/3A") as prog:
        prog.marcar(ANA.id, "100 - A/Ana Um.jpg", ENVIADO, pasta="100")
    with Progresso(tmp_path / "p.db", "Escola Dois/3A") as prog:
        assert prog.enviados_hoje(ANA.id, "100") == 1


# ─── Resolver e vincular ─────────────────────────────────────

def _caderno_misturado(banco: Path) -> None:
    _banco_antigo(banco, [(ANA.id, "100 - Antiga/Ana Um.jpg", REVISAO_MANUAL, ""),
                          (BIA.id, "100 - Antiga/Bia Dois.jpg", REVISAO_MANUAL, ""),
                          ("teste@example.com", "ensaio/100 - T/Ana Um.jpg", REVISAO_MANUAL, "")])
    with Progresso(banco, "Escola Um/3A") as prog:
        prog.marcar(ANA.id, "100 - Nova/Ana Um.jpg", REVISAO_MANUAL)
    with Progresso(banco, "Escola Dois/3A") as prog:
        prog.marcar(BIA.id, "100 - Nova/Bia Dois.jpg", REVISAO_MANUAL)


def test_resolver_mostra_so_a_turma_e_a_conta_de_teste(tmp_path):
    from modulos.ferramentas.resolver import executar_resolver
    banco = tmp_path / "p.db"
    _caderno_misturado(banco)
    saidas, perguntas = [], []
    executar_resolver(banco, tmp_path, entrada=lambda p: perguntas.append(p) or "", saida=saidas.append,
                      turma="Escola Um/3A", contas_teste=("teste@example.com",))
    texto = "\n".join(saidas)
    assert "100 - Nova/Ana Um.jpg" in texto
    assert "100 - T/Ana Um.jpg" in texto  # o do ensaio (a tela mostra sem o "ensaio/")
    assert "Bia Dois" not in texto and "100 - Antiga" not in texto
    assert "2 redação(ões) em revisão manual de antes das turmas" in texto
    assert '--vincular-antigos --escola "Escola Um" --turma "3A"' in texto
    assert len(perguntas) == 2


def test_vincular_antigos_so_os_alunos_da_turma_com_copia(tmp_path):
    from modulos.ferramentas.resolver import vincular_antigos
    banco = tmp_path / "relatorios" / "p.db"
    banco.parent.mkdir()
    _caderno_misturado(banco)
    copias_antes = len(list((banco.parent / "copias").glob("*.db")))  # 1: a da migração

    assert vincular_antigos(banco, "Escola Um/3A", [ANA.id], entrada=lambda _: "n", saida=lambda *_: None) == 0
    assert vincular_antigos(banco, "Escola Um/3A", [ANA.id], entrada=lambda _: "s", saida=lambda *_: None) == 1

    assert len(list((banco.parent / "copias").glob("*.db"))) == copias_antes + 1
    con = sqlite3.connect(banco)
    turmas = dict(con.execute("SELECT arquivo, turma FROM progresso").fetchall())
    estados = {e for (e,) in con.execute("SELECT estado FROM progresso")}
    con.close()
    assert turmas == {"100 - Antiga/Ana Um.jpg": "Escola Um/3A", "100 - Antiga/Bia Dois.jpg": "",
                      "ensaio/100 - T/Ana Um.jpg": "", "100 - Nova/Ana Um.jpg": "Escola Um/3A",
                      "100 - Nova/Bia Dois.jpg": "Escola Dois/3A"}
    assert estados == {REVISAO_MANUAL}  # só a turma mudou


def test_main_vincular_antigos(turma_ficticia, monkeypatch):
    import main as main_mod
    from modulos.base import config as config_mod
    banco = config_mod.RAIZ / "relatorios" / "progresso.db"
    banco.parent.mkdir()
    _banco_antigo(banco, [("ana@example.com", "100 - X/Ana Exemplo.jpg", ENVIADO, "")])
    monkeypatch.setattr("builtins.input", lambda _p: "s")
    assert main_mod.main(["--vincular-antigos", *turma_ficticia]) == 0
    con = sqlite3.connect(banco)
    assert con.execute("SELECT turma FROM progresso").fetchall() == [("Escola Ficticia/Turma A",)]
    con.close()
    assert main_mod.main(["--vincular-antigos"]) == 2                    # sem turma
    assert main_mod.main(["--vincular-antigos", "--resolver", *turma_ficticia]) == 2  # roda sozinho


# ─── Desfazer e enviar faltantes: só da turma ────────────────

def test_desfazer_recusa_log_de_outra_turma(tmp_path):
    from modulos.ferramentas.revisao_interativa import COLUNAS_LOG, desfazer_renomeacoes
    um, dois = tmp_path / "Escola Um" / "3A" / "temas", tmp_path / "Escola Dois" / "3A" / "temas"
    _foto(dois, "100 - Tema", "Bia Dois.jpg", b"x")
    log = tmp_path / "renomeacoes.csv"
    with open(log, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(COLUNAS_LOG)
        w.writerow(["100 - Tema", "Bia.jpg", "Bia Dois.jpg", BIA.email, str(dois.resolve())])
    saidas = []
    assert desfazer_renomeacoes(log, um, saidas.append, exigir_raiz=True) == 0
    assert any("não é desta turma" in s for s in saidas)
    assert (dois / "100 - Tema" / "Bia Dois.jpg").is_file()
    assert desfazer_renomeacoes(log, dois, lambda *_: None, exigir_raiz=True) == 1


def test_enviar_faltantes_recusa_relatorio_de_outra_turma(tmp_path):
    from modulos.site import conferencia_site as cs
    hoje = relogio.agora().strftime("%Y%m%d")
    caminho = tmp_path / f"conferencia_site_{hoje}_010000.csv"
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cs.COLUNAS_CSV)
        w.writerow([ANA.nome, "100 - Tema", "Ana Um.jpg", "100", cs.FORA_DO_SITE, 0, "", "", "Escola Dois/3A"])
    resultado = _fila(ANA, "100 - Tema", "Ana Um.jpg")
    saidas = []
    assert cs.faltantes_do_relatorio(tmp_path, resultado, saidas.append, turma="Escola Um/3A") is None
    assert any("é de outra turma" in s for s in saidas)
    assert len(cs.faltantes_do_relatorio(tmp_path, resultado, lambda *_: None, turma="Escola Dois/3A")) == 1
