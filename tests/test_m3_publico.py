# -*- coding: utf-8 -*-
"""M3 (parte C): arquivo morto da turma, exemplos/ fictício, .gitignore e auditoria.

Dados inventados (RAIZ temporária do conftest). Sem navegador."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import config as config_mod
from modulos.base.turma import raiz_redacoes
from modulos.ferramentas.auditoria_publica import alvos_locais, auditar, nome_proibido

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ_PROJETO / "exemplos" / "Escola Ficticia" / "Turma Exemplo"


# ─── Arquivo morto ───────────────────────────────────────────

def _temas(turma_ficticia):
    temas = raiz_redacoes() / turma_ficticia[1] / turma_ficticia[3] / "temas"
    for pasta in ("ENVIADA - 100 - Velha", "100 - Nova"):
        (temas / pasta).mkdir()
        (temas / pasta / "Ana Exemplo.jpg").write_bytes(pasta.encode())
    return temas


def test_arquiva_so_a_enviada_no_destino_da_turma_e_a_turma_fica(turma_ficticia, monkeypatch):
    import main as main_mod
    temas = _temas(turma_ficticia)
    turma = temas.parent
    monkeypatch.setattr("builtins.input", lambda _p, r=iter(["e", "s"]): next(r))

    assert main_mod.main(["--arquivar", *turma_ficticia]) == 0

    destinos = list((config_mod.RAIZ / "Arquivo morto" / "Escola Ficticia" / "Turma A").iterdir())
    assert len(destinos) == 1  # <data_hora>/
    assert [p.name for p in destinos[0].iterdir()] == ["ENVIADA - 100 - Velha"]
    assert (destinos[0] / "ENVIADA - 100 - Velha" / "Ana Exemplo.jpg").is_file()
    assert [p.name for p in temas.iterdir()] == ["100 - Nova"]  # não marcada não vai
    assert (turma / "alunos.csv").is_file()
    assert list((turma / "relatorios").glob("arquivamento_*.csv"))


def test_pasta_nao_marcada_nunca_e_oferecida(turma_ficticia, monkeypatch, capsys):
    import main as main_mod
    temas = raiz_redacoes() / "Escola Ficticia" / "Turma A" / "temas"
    (temas / "100 - Nova").mkdir()
    monkeypatch.setattr("builtins.input", lambda _p: pytest.fail("perguntou"))
    assert main_mod.main(["--arquivar", *turma_ficticia]) == 0
    assert "Nenhuma pasta \"ENVIADA - ...\"" in capsys.readouterr().out
    assert (temas / "100 - Nova").is_dir()


def test_arquivo_morto_nunca_sobrescreve(turma_ficticia, monkeypatch, capsys):
    import main as main_mod
    from modulos.base import relogio
    temas = _temas(turma_ficticia)
    quando = datetime(2026, 10, 29, 12, 0, 0)
    ja = config_mod.RAIZ / "Arquivo morto" / "Escola Ficticia" / "Turma A" / "2026-10-29_120000" / "ENVIADA - 100 - Velha"
    ja.mkdir(parents=True)
    (ja / "outra.jpg").write_bytes(b"antiga")
    monkeypatch.setattr("builtins.input", lambda _p, r=iter(["e", "s"]): next(r))
    with patch.object(relogio, "agora", return_value=quando):
        assert main_mod.main(["--arquivar", *turma_ficticia]) == 2
    assert "já existe" in capsys.readouterr().out
    assert (temas / "ENVIADA - 100 - Velha" / "Ana Exemplo.jpg").is_file()
    assert [p.name for p in ja.iterdir()] == ["outra.jpg"]


def test_arquivar_exige_turma():
    import main as main_mod
    assert main_mod.main(["--arquivar"]) == 2


# ─── exemplos/ ───────────────────────────────────────────────

def test_exemplo_e_inventado_e_sem_fotos():
    linhas = (EXEMPLO / "alunos.csv").read_text(encoding="utf-8").splitlines()
    assert linhas[0] == "Nome;Email;Senha"
    for linha in linhas[1:]:
        nome, email, senha = linha.split(";")
        assert email.endswith("@example.com")
        assert senha == "" or senha.startswith("senha-falsa-")
    arquivos = [p.name for p in (EXEMPLO / "temas").rglob("*") if p.is_file()]
    assert arquivos and set(arquivos) == {".gitkeep"}


def test_exemplo_funciona_como_turma(tmp_path):
    import shutil
    from modulos.base.config import Config
    from modulos.base.turma import aplicar_turma
    from modulos.dados.planilha_arquivos import carregar_alunos
    shutil.copytree(RAIZ_PROJETO / "exemplos" / "Escola Ficticia", raiz_redacoes() / "Escola Ficticia")
    cfg = Config()
    aplicar_turma(cfg, "Escola Ficticia", "Turma Exemplo")
    alunos = carregar_alunos(cfg)
    assert len(alunos) == 3 and sum(1 for a in alunos if not a.senha) == 1


# ─── .gitignore ──────────────────────────────────────────────

def _ignorados(caminhos):
    r = subprocess.run(["git", "-c", "core.ignorecase=false", "-c", "core.quotepath=false", "check-ignore", "--no-index", *caminhos],
                       cwd=RAIZ_PROJETO, capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 128:
        pytest.skip("sem git")
    return set(r.stdout.splitlines())


def test_gitignore_turmas_arquivo_morto_e_listas():
    privados = ["Redações plataforma/Escola X/Turma Y/alunos.csv",
                "Redações plataforma/Escola X/Turma Y/temas/100 - T/Ana.jpg",
                "Redações plataforma/Escola X/Turma Y/dados/pastas_aprovadas.csv",
                "Arquivo morto/Escola X/Turma Y/2026-10-29_120000/ENVIADA - T/Ana.jpg",
                "outra pasta/alunos.csv", "alunos.csv", "relatorios/copias/progresso_1.db",
                "x/progresso.db-journal", "dados/temas_site.20261029_120000.bak.csv", "logs/automacao.log",
                "exemplos/Escola Ficticia/Turma Exemplo/temas/100 - T/Ana.jpg"]
    publicos = ["exemplos/Escola Ficticia/Turma Exemplo/alunos.csv",
                "exemplos/Escola Ficticia/Turma Exemplo/temas/100 - Tema de exemplo/.gitkeep"]
    assert _ignorados(privados + publicos) == set(privados)


# ─── Auditoria pública ───────────────────────────────────────

def test_auditoria_aceita_so_a_lista_inventada_de_exemplos():
    assert nome_proibido("exemplos/Escola Ficticia/Turma Exemplo/alunos.csv") is None
    assert nome_proibido("exemplos/alunos.csv") is None
    assert nome_proibido("Redações plataforma/E/T/alunos.csv")
    assert nome_proibido("alunos.csv")
    assert nome_proibido("exemplos/E/T/dados/nomes_aprovados.csv")
    assert nome_proibido("exemplos/E/T/temas/100 - T/Ana.jpg")
    ficticia = "Nome;Email;Senha\nAna;ana@example.com;senha-falsa-1\n"
    assert auditar({"exemplos/E/T/alunos.csv": ficticia}, {}) == []
    real = "Nome;Email;Senha\nAna;ana@escola.com.br;x\n"
    assert auditar({"exemplos/E/T/alunos.csv": real}, {})


def test_auditoria_procura_nome_email_e_senha_das_turmas(turma_ficticia):
    alvos = alvos_locais(config_mod.RAIZ)
    achados = auditar({"README.md": "texto com senha-falsa-1 no meio", "docs/x.md": "ana@example.com"}, alvos)
    assert ("README.md", "senha do aluno 1 da turma 1") in achados
    assert ("docs/x.md", "e-mail do aluno 1 da turma 1") in achados
    assert all("senha-falsa" not in motivo for _, motivo in achados)  # nunca mostra o valor
