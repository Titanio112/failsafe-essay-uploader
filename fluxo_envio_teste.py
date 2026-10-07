"""Fluxo de envio de teste (conta de teste).

Reutiliza funcoes dos modulos: login, lista_redacoes, formulario_envio, confirmacao.
Nao duplica logica.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, sync_playwright

from config import Config, obter_email_teste, obter_senha
from planilha_arquivos import Aluno, descobrir_arquivos, extrair_codigo_do_arquivo
from login import login, confirmar_identidade, DOMINIO_ESPERADO
from lista_redacoes import ler_saldo_creditos, ler_lista_redacoes, detectar_ja_enviado
from formulario_envio import (
    verificar_dominio_autorizado,
    abrir_formulario_envio,
    ler_combo_temas,
    selecionar_tema_por_codigo,
    selecionar_criterio,
    anexar_arquivo,
    aguardar_upload_aceito,
)
from confirmacao import clicar_enviar, aguardar_confirmacao, logout
from progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL
from excecoes import CaptchaOuBloqueio


log = logging.getLogger("automacao_redacoes")


def executar_envio_teste(
    cfg: Config,
    progresso: Optional[Progresso] = None,
) -> int:
    """Executa envio de UMA redacao de teste.

    Retorna:
        0 = sucesso
        1 = erro/abortado
        2 = cancelado pelo usuario (confirmacao)
    """
    # 0. Carregar arquivo de teste
    arquivos = descobrir_arquivos(cfg)
    if not arquivos:
        log.error("Nenhum arquivo JPG encontrado em %s", cfg.pasta_raiz)
        return 1

    # Pegar o primeiro arquivo disponivel (ordem deterministica)
    pasta_tema = sorted(arquivos.keys())[0]
    arquivo = sorted(arquivos[pasta_tema])[0]
    # Código do tema vem da PASTA, não do arquivo
    from normalizacao import extrair_codigo_tema
    codigo_tema = extrair_codigo_tema(arquivo, pasta_tema)

    if not codigo_tema:
        log.error("Pasta sem codigo de tema no nome: %s", pasta_tema)
        return 1

    # Conta de teste
    email_teste = obter_email_teste()
    senha_teste = obter_senha("ESQUEMA_SENHA_TESTE")

    aluno_teste = Aluno(nome="Usuario Testes Ignorar", email=email_teste, sala="TESTE")

    email_mascarado = email_teste[:3] + "***" if len(email_teste) > 3 else "***"

    print(f"Arquivo: {arquivo}")
    print(f"Codigo do tema: {codigo_tema}")
    print(f"Conta: {email_mascarado}")
    print()
    confirmacao = input("Digite ENVIAR TESTE para confirmar (qualquer outro texto cancela): ").strip()
    if confirmacao != "ENVIAR TESTE":
        print("Cancelado pelo usuario.")
        return 2

    # Inicializar Playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Verificar dominio autorizado
            page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)

            # 2. Login
            log.info("Fazendo login com conta de teste...")
            login(page, cfg, email_teste, senha_teste)
            log.info("Login realizado: %s", email_mascarado)

            # 3. Confirmar identidade (modo teste)
            confirmar_identidade(page, aluno_teste, modo_teste=True)

            # 4. Ler saldo (fail-closed se None ou 0)
            saldo = ler_saldo_creditos(page)
            if saldo is None or saldo == 0:
                log.warning("Saldo de creditos indisponivel ou zero (%s). Abortando sem enviar.", saldo)
                if progresso:
                    progresso.marcar(
                        aluno_teste.id,
                        arquivo,
                        ERRO,
                        pasta=codigo_tema,
                        detalhe=f"Saldo indisponivel/zero: {saldo}",
                    )
                return 1

            # 5. Ler lista e checar duplicidade
            lista = ler_lista_redacoes(page)
            ja_enviado, data_envio = detectar_ja_enviado(lista, codigo_tema)
            if ja_enviado:
                log.info("Tema %s ja enviado em %s. Pulando.", codigo_tema, data_envio)
                if progresso:
                    progresso.marcar(
                        aluno_teste.id,
                        arquivo,
                        JA_ENVIADO,
                        pasta=codigo_tema,
                        detalhe="Ja enviado na lista remota",
                    )
                return 0

            # 6. Abrir formulario e ler combo de temas
            abrir_formulario_envio(page)
            temas_combo = ler_combo_temas(page)

            # 7. Validar que o codigo existe no combo (fail-closed)
            codigos_disponiveis = {t[0] for t in temas_combo}
            if codigo_tema not in codigos_disponiveis:
                log.error(
                    "Codigo %s nao encontrado no combo de temas do site. Disponiveis: %s",
                    codigo_tema,
                    sorted(codigos_disponiveis),
                )
                if progresso:
                    progresso.marcar(
                        aluno_teste.id,
                        arquivo,
                        ERRO,
                        pasta=codigo_tema,
                        detalhe=f"Codigo nao existe no combo: {sorted(codigos_disponiveis)}",
                    )
                return 1

            # 8. Selecionar tema, criterio ENEM, anexar arquivo
            selecionar_tema_por_codigo(page, codigo_tema)
            selecionar_criterio(page, "ENEM")
            anexar_arquivo(page, arquivo)

            # 9. Aguardar upload aceito
            aguardar_upload_aceito(page)

            # 10. Registrar ENVIANDO ANTES do clique (progresso)
            if progresso:
                progresso.marcar(
                    aluno_teste.id,
                    arquivo,
                    "ENVIANDO",
                    pasta=codigo_tema,
                    detalhe="Upload aceito, clicando em enviar",
                )

            # 11. Clicar em enviar
            clicar_enviar(page)

            # 12. Aguardar confirmacao (status "Pendente", timeout 120s)
            confirmado = aguardar_confirmacao(page, codigo_tema, timeout_segundos=120)

            if confirmado:
                log.info("Envio confirmado: tema %s -> Pendente", codigo_tema)
                if progresso:
                    progresso.marcar(
                        aluno_teste.id,
                        arquivo,
                        ENVIADO,
                        pasta=codigo_tema,
                        detalhe="Confirmado na lista remota",
                    )
                return 0
            else:
                log.error("Timeout ou falha na confirmacao do envio para tema %s", codigo_tema)
                if progresso:
                    progresso.marcar(
                        aluno_teste.id,
                        arquivo,
                        ERRO,
                        pasta=codigo_tema,
                        detalhe="Timeout/erro na confirmacao",
                    )
                return 1

        except CaptchaOuBloqueio as e:
            log.error("Captcha ou dominio bloqueado: %s", e)
            if progresso:
                progresso.marcar(
                    aluno_teste.id,
                    arquivo,
                    codigo_tema,
                    ERRO,
                    detalhe=f"Captcha/bloqueio: {e}",
                )
            return 1
        except Exception as e:
            log.exception("Erro inesperado durante envio de teste: %s", e)
            if progresso:
                progresso.marcar(
                    aluno_teste.id,
                    arquivo,
                    codigo_tema,
                    ERRO,
                    detalhe=f"Excecao: {type(e).__name__}",
                )
            return 1
        finally:
            # 13. Logout SEMPRE (mesmo em erro)
            try:
                logout(page)
            except Exception:
                pass  # logout e best-effort
            context.close()
            browser.close()

    return 1


if __name__ == "__main__":
    # Execucao direta para teste rapido
    from progresso_relatorio import configurar_logging

    configurar_logging()
    cfg = Config()
    cfg.pasta_raiz = Path("testes/redacoes_teste")
    cfg.headless = False
    cfg.slow_mo_ms = 500

    exit(executar_envio_teste(cfg))
