# -*- coding: utf-8 -*-
"""Testes offline fail-closed pós-clique (T18C) e pré-clique (T18D).

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

from modulos.base.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.base.progresso_relatorio import (
    ENVIADO, ERRO, JA_ENVIADO, REVISAO_MANUAL, Progresso
)
from modulos.base.config import Config


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
    def cfg(self, arquivo_teste, codigo_tema, tmp_path):
        # JPG falso real em disco: o fluxo exige o caminho completo existente (T18D-B)
        (tmp_path / codigo_tema).mkdir()
        (tmp_path / codigo_tema / arquivo_teste).write_bytes(b"jpg-falso")
        cfg = Config()
        cfg.pasta_raiz = tmp_path
        cfg.headless = True
        cfg.slow_mo_ms = 0
        return cfg

    @pytest.fixture
    def mocks_completos(self, codigo_tema):
        """Configura todos os mocks necessários para executar_envio_teste."""
        with patch("modulos.envio.fluxo_envio_teste.sync_playwright") as mock_pw, \
             patch("builtins.input", return_value="ENVIAR TESTE") as mock_input, \
             patch("modulos.envio.fluxo_envio_teste.obter_email_teste", return_value="teste@teste.com"), \
             patch("modulos.envio.fluxo_envio_teste.obter_senha", return_value="senha123"), \
             patch("modulos.envio.fluxo_envio_teste.descobrir_arquivos", autospec=True, return_value={"0": ["redacao_0.jpg"]}) as mock_descobrir, \
             patch("modulos.envio.fluxo_envio_teste.verificar_dominio_autorizado", autospec=True) as mock_dominio, \
             patch("modulos.envio.fluxo_envio_teste.login", autospec=True) as mock_login, \
             patch("modulos.envio.fluxo_envio_teste.confirmar_identidade", autospec=True) as mock_identidade, \
             patch("modulos.envio.envio_item.ler_saldo_creditos", autospec=True) as mock_saldo, \
             patch("modulos.envio.envio_item.ler_lista_redacoes", autospec=True) as mock_lista, \
             patch("modulos.envio.envio_item.contar_tema_hoje", autospec=True) as mock_dup, \
             patch("modulos.envio.envio_item.abrir_formulario_envio", autospec=True) as mock_abrir, \
             patch("modulos.envio.envio_item.ler_combo_temas", autospec=True) as mock_combo, \
             patch("modulos.envio.envio_item.selecionar_tema_por_codigo", autospec=True) as mock_sel_tema, \
             patch("modulos.envio.envio_item.selecionar_criterio", autospec=True) as mock_sel_crit, \
             patch("modulos.envio.envio_item.anexar_arquivo", autospec=True) as mock_anexar, \
             patch("modulos.envio.envio_item.aguardar_upload_aceito", autospec=True) as mock_upload, \
             patch("modulos.envio.envio_item.clicar_enviar", autospec=True) as mock_clicar, \
             patch("modulos.envio.envio_item.aguardar_confirmacao", autospec=True) as mock_confirma, \
             patch("modulos.envio.fluxo_envio_teste.logout", autospec=True) as mock_logout:

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
            mock_dup.return_value = 0  # T35: nenhuma linha do tema hoje no site
            mock_combo.return_value = [(codigo_tema, f"{codigo_tema} - Tema Teste")]
            mock_sel_tema.return_value = True
            # Opção selecionada no combo, lida por _codigo_tema_selecionado
            mock_page.locator.return_value.first.inner_text.return_value = (
                f"{codigo_tema} - Tema Teste"
            )
            mock_upload.return_value = True  # upload aceito
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
                "input": mock_input,
                "descobrir": mock_descobrir,
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
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

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert self._contar_clicar_enviar(mocks) == 0  # NÃO deve ter clicado

    # ---- Casos PRÉ-CLIQUE achados na 1ª execução da T19 (T18D) ----

    def test_criterio_e_anexo_com_argumentos_corretos(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """T18D A/B: selecionar_criterio(page) e anexo com caminho completo"""
        mocks = mocks_completos

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        mocks["sel_crit"].assert_called_once_with(mocks["page"])
        caminho = str(cfg.pasta_raiz / codigo_tema / arquivo_teste)
        mocks["anexar"].assert_called_once_with(mocks["page"], caminho)

    def test_arquivo_inexistente_aborta_sem_login(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """T18D B: JPG não existe no disco -> retorna 1, sem login e sem clique"""
        mocks = mocks_completos
        (cfg.pasta_raiz / codigo_tema / arquivo_teste).unlink()

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        assert executar_envio_teste(cfg, progresso=progresso_mock) == 1

        assert mocks["login"].call_count == 0
        assert self._contar_clicar_enviar(mocks) == 0

    def test_upload_nao_aceito_erro_sem_clique(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """T18D C: aguardar_upload_aceito retorna False -> ERRO, sem clique"""
        mocks = mocks_completos
        mocks["upload"].return_value = False

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert estado["pasta"] == codigo_tema
        assert "Upload nao aceito" in estado["detalhe"]  # parou no upload, não antes
        assert mocks["anexar"].call_count == 1
        assert self._contar_clicar_enviar(mocks) == 0

    def test_tema_nao_selecionado_erro_sem_clique(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """T18D D: selecionar_tema_por_codigo retorna False -> ERRO, sem clique"""
        mocks = mocks_completos
        mocks["sel_tema"].return_value = False

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert "Tema selecionado diferente" in estado["detalhe"]
        assert self._contar_clicar_enviar(mocks) == 0
        assert mocks["anexar"].call_count == 0

    def test_tema_selecionado_diferente_erro_sem_clique(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """T18D D: combo ficou com outro tema (ex.: fallback por value) -> ERRO, sem clique"""
        mocks = mocks_completos
        # "00" != "0": códigos são strings distintas
        mocks["page"].locator.return_value.first.inner_text.return_value = "00 - Outro Tema"

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ERRO
        assert "Tema selecionado diferente" in estado["detalhe"]
        assert self._contar_clicar_enviar(mocks) == 0
        assert mocks["anexar"].call_count == 0

    # ---- Fila com vários itens (T21) ----

    def _fila_dois_itens(self, cfg, mocks):
        """Itens: tema "0" (redacao_0.jpg) e tema "00" (redacao_00.jpg)."""
        (cfg.pasta_raiz / "00").mkdir()
        (cfg.pasta_raiz / "00" / "redacao_00.jpg").write_bytes(b"jpg-falso")
        mocks["descobrir"].return_value = {"0": ["redacao_0.jpg"], "00": ["redacao_00.jpg"]}
        mocks["combo"].return_value = [("0", "0 - Tema Teste"), ("00", "00 - Outro")]

    def test_fila_pula_ja_enviado_e_envia_o_proximo(
        self, progresso_mock, cfg, arquivo_teste, mocks_completos
    ):
        """T21: 1º já enviado hoje -> pula e segue; 2º é enviado; 1 confirmação só"""
        mocks = mocks_completos
        self._fila_dois_itens(cfg, mocks)
        mocks["dup"].side_effect = [1, 0]  # T35: 1º tema já tem 1 linha hoje
        mocks["page"].locator.return_value.first.inner_text.return_value = "00 - Outro"

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        assert executar_envio_teste(cfg, progresso=progresso_mock) == 0

        assert mocks["input"].call_count == 1
        assert self._contar_clicar_enviar(mocks) == 1
        assert self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)["estado"] == JA_ENVIADO
        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", "redacao_00.jpg")
        assert estado["estado"] == ENVIADO
        assert estado["pasta"] == "00"

    def test_fila_para_no_primeiro_inconclusivo(
        self, progresso_mock, cfg, arquivo_teste, mocks_completos
    ):
        """T21: 1º fica REVISAO_MANUAL -> execução para; 2º nem é tentado"""
        mocks = mocks_completos
        self._fila_dois_itens(cfg, mocks)
        mocks["confirma"].return_value = False

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        assert executar_envio_teste(cfg, progresso=progresso_mock) == 1

        assert self._contar_clicar_enviar(mocks) == 1
        assert self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)["estado"] == REVISAO_MANUAL
        assert self._ler_estado_banco(progresso_mock, "teste@teste.com", "redacao_00.jpg") is None

    def test_fila_para_no_primeiro_erro_pre_clique(
        self, progresso_mock, cfg, arquivo_teste, mocks_completos
    ):
        """T21: 1º com código fora do combo -> ERRO, execução para, 0 cliques"""
        mocks = mocks_completos
        self._fila_dois_itens(cfg, mocks)
        mocks["combo"].return_value = [("00", "00 - Outro")]  # "0" não existe

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        assert executar_envio_teste(cfg, progresso=progresso_mock) == 1

        assert self._contar_clicar_enviar(mocks) == 0
        assert self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)["estado"] == ERRO
        assert self._ler_estado_banco(progresso_mock, "teste@teste.com", "redacao_00.jpg") is None

    def test_fila_cancelada_nao_faz_login(
        self, progresso_mock, cfg, mocks_completos
    ):
        """T21: texto diferente de ENVIAR TESTE -> retorna 2, sem login, sem clique"""
        mocks = mocks_completos
        mocks["input"].return_value = "enviar teste"

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        assert executar_envio_teste(cfg, progresso=progresso_mock) == 2

        assert mocks["login"].call_count == 0
        assert self._contar_clicar_enviar(mocks) == 0

    # ---- Caso SUCESSO ----

    def test_confirmacao_ok_enviado(
        self, progresso_mock, cfg, arquivo_teste, codigo_tema, mocks_completos
    ):
        """Caso 6: confirmação OK -> ENVIADO"""
        mocks = mocks_completos
        mocks["confirma"].return_value = True  # confirmação OK

        from modulos.envio.fluxo_envio_teste import executar_envio_teste
        executar_envio_teste(cfg, progresso=progresso_mock)

        estado = self._ler_estado_banco(progresso_mock, "teste@teste.com", arquivo_teste)
        assert estado is not None
        assert estado["estado"] == ENVIADO
        assert estado["pasta"] == codigo_tema
        assert self._contar_clicar_enviar(mocks) == 1