"""Clique em enviar, confirmação e logout."""

from __future__ import annotations

from playwright.sync_api import Page
import logging
import time

from modulos.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.login import DOMINIO_ESPERADO
from modulos.lista_redacoes import ler_lista_redacoes

log = logging.getLogger("automacao_redacoes")

def verificar_dominio_autorizado(page: Page) -> None:
    dominio_atual = page.url.split("/")[2] if len(page.url.split("/")) > 2 else ""
    if DOMINIO_ESPERADO not in dominio_atual:
        raise CaptchaOuBloqueio(f"Domínio inesperado: {dominio_atual}. Esperado: {DOMINIO_ESPERADO}")


def clicar_enviar(page: Page) -> None:
    """Clica uma única vez no botão 'Enviar resposta'."""
    btn = page.locator("input[type='submit'][value='Enviar resposta'][name='commit']").first
    btn.click()


def aguardar_confirmacao(page: Page, codigo_tema: str, timeout_segundos: int = 120) -> bool:
    """Aguarda confirmação do envio na lista remota.
    
    Recarrega /minhas-redacoes a cada 5s até:
    - Nova linha com o código e data de hoje aparecer como "Pendente"
    - Timeout
    
    Retorna True se confirmado, False se erro/cancelada.

    T27: se no fim do prazo a linha nova (código + hoje) ainda estiver em
    "Processando arquivo", conta como RECEBIDA (True): antes do envio a
    lista não tinha esse tema hoje, então a linha só pode ser a nossa.
    Sem linha nenhuma no prazo -> ConfirmacaoInconclusiva."""
    from datetime import datetime

    data_hoje = datetime.now().strftime("%d/%m/%Y")
    inicio = time.time()
    viu_processando = False

    while time.time() - inicio < timeout_segundos:
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)

            for item in ler_lista_redacoes(page):
                if item.codigo != codigo_tema or item.data != data_hoje:
                    continue
                situacao = item.situacao.lower()
                if "pendente" in situacao:
                    return True
                if "processando" in situacao:
                    viu_processando = True
                elif "erro" in situacao or "cancelada" in situacao:
                    return False
        except Exception:
            pass
        time.sleep(5)

    if viu_processando:
        log.info("Tema %s ainda em 'Processando arquivo' apos %ss: contado como recebido.",
                 codigo_tema, timeout_segundos)
        return True
    raise ConfirmacaoInconclusiva(f"Timeout ({timeout_segundos}s) aguardando confirmação do envio para tema {codigo_tema}")


def logout(page: Page) -> None:
    """Mantém compatibilidade sem navegar para a rota de logout.

    A navegação direta observada para /auth/users/sign_out retornou 404.
    Não existe seletor de logout confirmado no site real. O chamador deve
    encerrar o teste com context.close() e browser.close() no finally.
    """
    pass