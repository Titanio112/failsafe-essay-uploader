"""Clique em enviar, confirmação e logout."""

from __future__ import annotations

from playwright.sync_api import Page
import time

from modulos.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.login import DOMINIO_ESPERADO
from modulos.lista_redacoes import ler_lista_redacoes


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
    
    Retorna True se confirmado, False se timeout/erro."""
    from datetime import datetime
    
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    inicio = time.time()
    
    while time.time() - inicio < timeout_segundos:
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)
            
            itens = ler_lista_redacoes(page)
            
            for item in itens:
                if item.codigo == codigo_tema and item.data == data_hoje:
                    if "pendente" in item.situacao.lower() or "processando" in item.situacao.lower():
                        # Se ainda está processando, espera mais
                        if "processando" in item.situacao.lower():
                            time.sleep(5)
                            continue
                        return True
                    elif "erro" in item.situacao.lower() or "cancelada" in item.situacao.lower():
                        return False
            
            time.sleep(5)
        except Exception:
            time.sleep(5)
    
    raise ConfirmacaoInconclusiva(f"Timeout ({timeout_segundos}s) aguardando confirmação do envio para tema {codigo_tema}")


def logout(page: Page) -> None:
    """Mantém compatibilidade sem navegar para a rota de logout.

    A navegação direta observada para /auth/users/sign_out retornou 404.
    Não existe seletor de logout confirmado no site real. O chamador deve
    encerrar o teste com context.close() e browser.close() no finally.
    """
    pass