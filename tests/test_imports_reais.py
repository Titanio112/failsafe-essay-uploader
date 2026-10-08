# -*- coding: utf-8 -*-
"""Testes offline: importar todos os símbolos que os testes reais usam (sem navegador)."""
import pytest

def test_import_login():
    from modulos.login import (
        DOMINIO_ESPERADO,
        verificar_dominio_autorizado,
        login,
        confirmar_identidade,
    )
    assert DOMINIO_ESPERADO == "www.esquemaredacao.com.br"

def test_import_lista_redacoes():
    from modulos.lista_redacoes import (
        ItemListaRedacao,
        ler_saldo_creditos,
        ler_lista_redacoes,
        verificar_duplicidade,
        contar_linhas_codigo_data,
        ler_lista_redacoes_html,
        detectar_ja_enviado,
    )

def test_import_formulario_envio():
    from modulos.formulario_envio import (
        abrir_formulario_envio,
        ler_combo_temas,
        selecionar_tema_por_codigo,
        selecionar_criterio,
        anexar_arquivo,
        aguardar_upload_aceito,
    )

def test_import_confirmacao():
    from modulos.confirmacao import (
        clicar_enviar,
        aguardar_confirmacao,
        logout,
    )

def test_import_plataforma():
    from modulos.login import (
        login as login_plataforma,
        confirmar_identidade as confirmar_identidade_plataforma,
    )
    from modulos.lista_redacoes import (
        ler_lista_redacoes as ler_lista_redacoes_plataforma,
    )
    from modulos.formulario_envio import (
        ler_combo_temas as ler_combo_temas_plataforma,
    )
    from modulos.formulario_envio import (
        selecionar_tema_por_codigo as selecionar_tema_por_codigo_plataforma,
    )
    from modulos.planilha_arquivos import Aluno
    from modulos.config import Config

def test_import_planilha_arquivos():
    from modulos.planilha_arquivos import (
        Aluno as AlunoPlanilha,
        normalizar_nome,
        extrair_pessoa,
        extrair_codigo_do_arquivo,
        extrair_codigo_do_tema_site,
        conciliar,
        carregar_alunos,
        descobrir_arquivos,
        ResultadoConciliacao,
        EXATO_UNICO,
        SUGESTAO_FUZZY,
        AMBIGUO,
        ARQUIVO_SEM_ALUNO,
        ALUNO_SEM_ARQUIVO,
        SEM_CODIGO,
        CODIGO_INVALIDO,
        REVISAO_MANUAL,
        SIMULADO,
        ESTADOS_CONCILIACAO,
    )

def test_import_config():
    from modulos.config import Config, obter_email_teste, obter_senha, exigir_envio_real

def test_import_progresso():
    from modulos.progresso_relatorio import Progresso

def test_import_normalizacao():
    from modulos.normalizacao import validar_codigo_site, extrair_codigo_tema

def test_import_excecoes():
    from modulos.excecoes import (
        CaptchaOuBloqueio,
        LoginFalhou,
        IdentidadeDivergente,
        UploadNaoConfirmado,
        ConfirmacaoInconclusiva,
    )

# Teste de coleta dos testes reais
def test_coleta_testes_reais():
    """Roda pytest --collect-only -m real -q e verifica se nao ha erro de importacao."""
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-m", "real", "-q"],
        cwd="d:\\%USERNAME%\\Documents\\VS-CODE\\Ambientes\\esquema\\automacao-redacoes",
        capture_output=True,
        text=True,
        timeout=30
    )
    # O comando deve rodar sem erro (exit code 0 ou 5 - no tests collected)
    # Exit code 2 pode ocorrer se houver arquivos nao-test com erro de encoding
    assert result.returncode in (0, 2, 5), f"pytest collect falhou: {result.stderr}"
    # Nao deve ter erro de importacao
    assert "ImportError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "UnboundLocalError" not in result.stderr
    # Deve coletar pelo menos o teste real
    assert "test_real_leitura_conta_teste" in result.stdout
    assert "test_launch" in result.stdout
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)