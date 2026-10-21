# -*- coding: utf-8 -*-
"""Testes offline fail-closed pós-clique (T18C).

Testam a lógica de marcação REVISAO_MANUAL vs ERRO
exercitando o código de produção executar_envio_teste
com mocks completos, sem navegador, sem login, sem envio.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.progresso_relatorio import (
    ENVIADO, ERRO, REVISAO_MANUAL, Progresso
)
from modulos.config import Config


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
    def arquivo_teste(self):
        return "redacao_0.jpg"

    @pytest.fixture
    def codigo_tema(self):
        return "0"

    @pytest.fixture
    def cfg(self, arquivo_teste):
        cfg = Config()
        cfg.pasta_raiz = Path("testes/redacoes_teste")
        cfg.headless = True
        cfg.slow_mo_ms = 0
        return cfg

    @pytest.fixture
    def mocks_completos(self, codigo_tema):
        """Configura todos os mocks necessários para executar_envio_teste."""
        with patch("modulos.fluxo_envio_teste.sync_playwright") as mock_pw, \
             patch("builtins.input", return_value="ENVIAR TESTE"), \
             patch("modulos.fluxo_envio_teste.obter_email_teste", return_value="teste@teste.com"), \
             patch("modulos.fluxo_envio_teste.obter_senha", return_value="senha123"), \
             patch("modulos.fluxo_envio_teste.descobrir_arquivos", return_value={"0": ["redacao_0.jpg"]}), \
             patch("modulos.fluxo_envio_teste.verificar_dominio_autorizado") as mock_dominio, \
             patch("modulos.fluxo_envio_teste.login") as mock_login, \
             patch("modulos.fluxo_envio_teste.confirmar_identidade") as mock_identidade, \
             patch("modulos.fluxo_envio_teste.ler_saldo_creditos") as mock_saldo, \
             patch("modulos.fluxo_envio_teste.ler_lista_redacoes") as mock_lista, \
             patch("modulos.fluxo_envio_teste.detectar_ja_enviado") as mock_dup, \
             patch("modulos.fluxo_envio_teste.abrir_formulario_envio") as mock_abrir, \
             patch("modulos.fluxo_envio_teste.ler_combo_temas") as mock_combo, \
             patch("modulos.fluxo_envio_teste.selecionar_tema_por_codigo") as mock_sel_tema, \
             patch("modulos.fluxo_envio_teste.selecionar_criterio") as mock_sel_crit, \
             patch("modulos.fluxo_envio_teste.anexar_arquivo") as mock_anexar, \
             patch("modulos.fluxo_envio_teste.aguardar_upload_aceito") as mock_upload, \
             patch("modulos.fluxo_envio_teste.clicar_enviar") as mock_clicar, \
             patch("modulos.fluxo_envio_teste.aguardar_confirmacao") as mock_confirma, \
             patch("modulos.fluxo_envio_teste.logout") as mock_logout:

            # Configurar playwright mock
            mock_page = MagicMock()
            mock_context = MagicMock()
            mock_context.new_page.return_value = mock_page
            mock_browser = MagicMock()
            mock_browser.new_context.return_value = mock_context
            mock_pw_instance = MagicMock()
            mock_pw_instance.chromium.launch.return_value = mock_browser
            mock_pw.return_value.__enter__.return_value = mock_pw_instance

            # Configurar retornos padrão (sucesso)
            mock_saldo.return_value = 999  # saldo disponível
            mock_lista.return_value = []
            mock_dup.return_value = (False, None)
            mock_combo.return_value = [(codigo_tema, f"{codigo_tema} - Tema Teste")]
            mock_confirma.return_value = True  # confirmação OK

            yield {
                "pw": mock_pw,
                "page": mock_page,
                "dominio": mock_dominio,
                "login": mock_login,
                "identidade": mock_identidade,
                "saldo": mock_saldo,
                "lista": mock_lista,
                "dup": mock_dup,
                "abrir": mock_abrir,
                "combo": mock_combo,
                "sel_tema": mock_sel_tema,
                "sel_crit": mock_sel_crit,
                "anexar": mock_anexar,
                "upload": mock_upload,
                "clicar": mock_clicar,
                "confirma": mock_confirma,
                "logout": mock_logout,
            }

    def _ler_estado_banco(self, progresso, aluno_id, arquivo):
        """Lê o estado gravado no banco de progresso."""
        row = progresso.con.execute(
            "SELECT estado, pasta, detalhe FROM progresso WHERE aluno_id=? AND arquivo=?",
            (aluno_id, str(arquivo))
        ).fetchone()
        if row:
            return {"estado": row[0], "pasta": row[1], "detalhe": row[2]}
        return None

    def _contar_clicar_enviar(self, mocks):
        """Retorna quantas vezes clicar_enviar foi chamado."""
        return mocks["clicar"].call_count

    # ---- Casos POST-CLIQUE (clique_iniciado=True) -> REVISAO_MANUAL ----

    def test_aguardar_confirmacao_retorna_false_revisao_manual(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 1: aguardar_confirmacao retorna False -> REVISAO_MANUAL"""
        mocks = mocks_completos
        mocks["confirma"].return_value = False  # Falha na confirmação

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == REVISAO_MANUAL
        assert estado["pasta"] == codigo_tema  # pasta deve ser código do tema, NÃO o estado
        assert self._contar_clicar_enviar(mocks) == 1

    def test_aguardar_confirmacao_levanta_confirmacao_inconclusiva_revisao_manual(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 2: aguardar_confirmacao levanta ConfirmacaoInconclusiva -> REVISAO_MANUAL"""
        mocks = mocks_completos
        mocks["confirma"].side_effect = ConfirmacaoInconclusiva("timeout 120s")

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == REVISAO_MANUAL
        assert estado["pasta"] == codigo_tema  # pasta deve ser código do tema, NÃO o estado
        assert self._contar_clicar_enviar(mocks) == 1

    def test_clicar_enviar_levanta_captcha_bloqueio_revisao_manual(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 3: clicar_enviar levanta CaptchaOuBloqueio -> REVISAO_MANUAL"""
        mocks = mocks_completos
        mocks["clicar"].side_effect = CaptchaOuBloqueio("CAPTCHA detectado")

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == REVISAO_MANUAL
        assert estado["pasta"] == codigo_tema  # pasta deve ser código do tema, NÃO o estado
        assert self._contar_clicar_enviar(mocks) == 1

    def test_aguardar_confirmacao_levanta_exception_generica_revisao_manual(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 4: aguardar_confirmacao levanta Exception genérica -> REVISAO_MANUAL"""
        mocks = mocks_completos
        mocks["confirma"].side_effect = Exception("Erro de rede")

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == REVISAO_MANUAL
        assert estado["pasta"] == codigo_tema  # pasta deve ser código do tema, NÃO o estado
        assert self._contar_clicar_enviar(mocks) == 1

    # ---- Casos PRÉ-CLIQUE (clique_iniciado=False) -> ERRO ----

    def test_falha_antes_do_clique_saldo_indisponivel_erro(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 5: falha ANTES do clique (saldo indisponível) -> ERRO"""
        mocks = mocks_completos
        mocks["saldo"].return_value = 0  # saldo zero -> falha antes do clique

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert estado["pasta"] == codigo_tema
        assert self._contar_clicar_enviar(mocks) == 0  # NÃO deve ter clicado

    def test_falha_antes_do_clique_codigo_invalido_erro(
        self, progresso_mock, cfg, arquivo_teste, mocks_completos
    ):
        """Caso 5b: falha ANTES do clique (código não existe no combo) -> ERRO"""
        mocks = mocks_completos
        mocks["combo"].return_value = [("1", "1 - Outro Tema")]  # código "0" não existe

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert self._contar_clicar_enviar(mocks) == 0  # NÃO deve ter clicado

    # ---- Caso SUCESSO ----

    def test_confirmacao_ok_enviado(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 6: confirmação OK -> ENVIADO"""
        mocks = mocks_completos
        mocks["confirma"].return_value = True  # confirmação OK

        from modulos.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ENVIADO
        assert estado["pasta"] == codigo_tema
        assert self._contar_clicar_enviar(mocks) == 1