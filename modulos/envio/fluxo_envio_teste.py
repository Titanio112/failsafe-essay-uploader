"""Fluxo de envio de teste (conta de teste).

Percorre a fila de teste (fila_teste) e envia cada item com
envio_item. Uma confirmacao ENVIAR TESTE para a fila toda;
qualquer ERRO ou REVISAO_MANUAL para a execucao.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from modulos.base.config import Config, obter_email_teste, obter_senha
from modulos.dados.planilha_arquivos import Aluno, descobrir_arquivos
from modulos.site.login import login, confirmar_identidade, DOMINIO_ESPERADO
from modulos.site.formulario_envio import verificar_dominio_autorizado
from modulos.site.confirmacao import logout
from modulos.envio.fila_teste import montar_fila_teste
from modulos.envio.envio_item import enviar_item
from modulos.base.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO


log = logging.getLogger("automacao_redacoes")


def executar_envio_teste(
    cfg: Config,
    progresso: Optional[Progresso] = None,
) -> int:
    """Executa o envio de teste de todos os itens liberados da fila.

    Retorna:
        0 = todos enviados ou ja enviados
        1 = erro/abortado (parou no primeiro problema)
        2 = cancelado pelo usuario (confirmacao)
    """
    # 0. Montar a fila (1 arquivo por codigo, ordem alfabetica)
    arquivos = descobrir_arquivos(cfg)
    if not arquivos:
        log.error("Nenhum arquivo JPG encontrado em %s", cfg.pasta_raiz)
        return 1

    fila, ignorados = montar_fila_teste(Path(cfg.pasta_raiz), arquivos)
    for rotulo, motivo in ignorados:
        log.warning("Fora da fila: %s (%s)", rotulo, motivo)
    if not fila:
        log.error("Nenhum arquivo de teste liberado para envio.")
        return 1

    # Conta de teste
    email_teste = obter_email_teste()
    senha_teste = obter_senha("ESQUEMA_SENHA_TESTE")

    aluno_teste = Aluno(nome="Usuario Testes Ignorar", email=email_teste)

    email_mascarado = email_teste[:3] + "***" if len(email_teste) > 3 else "***"

    print(f"Conta: {email_mascarado}")
    print(f"Fila de teste ({len(fila)}), na ordem; ja enviados hoje serao pulados:")
    for n, item in enumerate(fila, 1):
        print(f"  {n}. tema {item.codigo}: {item.pasta}/{item.arquivo}")
    print("Qualquer erro ou resultado inconclusivo para a execucao.")
    print()
    confirmacao = input("Digite ENVIAR TESTE para confirmar a fila (qualquer outro texto cancela): ").strip()
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

            # 4. Um item por vez; ERRO/REVISAO_MANUAL para a execucao
            for n, item in enumerate(fila, 1):
                log.info("Item %d/%d: tema %s (%s)", n, len(fila), item.codigo, item.arquivo)
                estado = enviar_item(page, aluno_teste.id, item, progresso)
                if estado not in (ENVIADO, JA_ENVIADO):
                    log.error("Execucao parada no item %d/%d: %s", n, len(fila), estado)
                    return 1
            log.info("Fila de teste concluida (%d item(ns)).", len(fila))
            return 0

        except Exception as e:
            # Falha antes de qualquer item (dominio, login, identidade): nada clicado
            log.exception("Erro antes do envio de teste: %s", e)
            return 1
        finally:
            # 5. Logout SEMPRE (mesmo em erro)
            try:
                logout(page)
            except Exception:
                pass  # logout e best-effort
            context.close()
            browser.close()

    return 1


if __name__ == "__main__":
    # Execucao direta para teste rapido
    from modulos.base.progresso_relatorio import configurar_logging

    configurar_logging()
    cfg = Config()
    cfg.pasta_raiz = Path("testes/redacoes_teste")
    cfg.headless = False
    cfg.slow_mo_ms = 500

    exit(executar_envio_teste(cfg))
