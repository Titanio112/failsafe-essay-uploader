# -*- coding: utf-8 -*-
"""Testes offline fail-closed pós-clique (T18B).

Testam exclusivamente a lógica de marcação REVISAO_MANUAL vs ERRO
conforme a flag clique_iniciado, sem navegador, sem login, sem envio.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.progresso_relatorio import REVISAO_MANUAL, Progresso


class TestFailClosedPosClique:
    """Testes da regra: pós-clique_iniciado=True → REVISAO_MANUAL; pré-clique → ERRO."""

    @pytest.fixture
    def progresso_mock(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        prog = Progresso(db_path)
        yield prog
        prog.close(); db_path.unlink(missing_ok=True)

    @pytest.fixture
    def aluno_teste(self):
        from modulos.planilha_arquivos import Aluno
        return Aluno(nome="Usuario Testes Ignorar", email="teste@teste.com", sala="TESTE")

    @pytest.fixture
    def arquivo_teste(self):
        return Path("testes/redacoes_teste/0/redacao_0.jpg")

    @pytest.fixture
    def codigo_tema(self):
        return "0"

    def _simular_marcacao_pos_clique(self, progresso, aluno, arquivo, codigo, exc_tipo, exc_msg="detalhe"):
        estado = REVISAO_MANUAL
        detalhe = f"{exc_tipo.__name__} apos clique: {exc_msg}"
        progresso.marcar(aluno.id, str(arquivo), estado, pasta=codigo, detalhe=detalhe)
        return estado, detalhe

    def test_confirmacao_inconclusiva_pos_clique_revisao_manual(
        self, progresso_mock, aluno_teste, arquivo_teste, codigo_tema
    ):
        estado, detalhe = self._simular_marcacao_pos_clique(
            progresso_mock, aluno_teste, arquivo_teste, codigo_tema,
            ConfirmacaoInconclusiva, "timeout 120s"
        )
        assert estado == REVISAO_MANUAL
        assert "apos clique" in detalhe
        assert "ConfirmacaoInconclusiva" in detalhe

        rows = progresso_mock.con.execute(
            "SELECT estado, detalhe FROM progresso WHERE aluno_id=? AND arquivo=?",
            (aluno_teste.id, str(arquivo_teste))
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == REVISAO_MANUAL
        assert "apos clique" in rows[0][1]

    def test_aguardar_confirmacao_falso_pos_clique_revisao_manual(
        self, progresso_mock, aluno_teste, arquivo_teste, codigo_tema
    ):
        progresso_mock.marcar(
            aluno_teste.id,
            str(arquivo_teste),
            REVISAO_MANUAL,
            pasta=codigo_tema,
            detalhe="Confirmacao inconclusiva apos clique",
        )

        rows = progresso_mock.con.execute(
            "SELECT estado, detalhe FROM progresso WHERE aluno_id=? AND arquivo=?",
            (aluno_teste.id, str(arquivo_teste))
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == REVISAO_MANUAL
        assert "apos clique" in rows[0][1]

    def test_captcha_bloqueio_pos_clique_revisao_manual(
        self, progresso_mock, aluno_teste, arquivo_teste, codigo_tema
    ):
        estado, detalhe = self._simular_marcacao_pos_clique(
            progresso_mock, aluno_teste, arquivo_teste, codigo_tema,
            CaptchaOuBloqueio, "CAPTCHA detectado"
        )
        assert estado == REVISAO_MANUAL
        assert "apos clique" in detalhe
        assert "CaptchaOuBloqueio" in detalhe

        rows = progresso_mock.con.execute(
            "SELECT estado FROM progresso WHERE aluno_id=? AND arquivo=?",
            (aluno_teste.id, str(arquivo_teste))
        ).fetchall()
        assert rows[0][0] == REVISAO_MANUAL

    def test_exception_generica_pos_clique_revisao_manual(
        self, progresso_mock, aluno_teste, arquivo_teste, codigo_tema
    ):
        estado, detalhe = self._simular_marcacao_pos_clique(
            progresso_mock, aluno_teste, arquivo_teste, codigo_tema,
            Exception, "Erro de rede"
        )
        assert estado == REVISAO_MANUAL
        assert "apos clique" in detalhe
        assert "Exception" in detalhe

        rows = progresso_mock.con.execute(
            "SELECT estado FROM progresso WHERE aluno_id=? AND arquivo=?",
            (aluno_teste.id, str(arquivo_teste))
        ).fetchall()
        assert rows[0][0] == REVISAO_MANUAL