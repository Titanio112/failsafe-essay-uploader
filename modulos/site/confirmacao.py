"""Clique em enviar, confirmação e logout."""

from __future__ import annotations

from playwright.sync_api import Page
import logging
import time

from modulos.base.excecoes import BotaoEnviarAusente, CaptchaOuBloqueio, ConfirmacaoInconclusiva
from modulos.site.login import DOMINIO_ESPERADO, verificar_dominio_autorizado
from modulos.site.lista_redacoes import ler_lista_redacoes, situacoes_tema_hoje

log = logging.getLogger("automacao_redacoes")

def clicar_enviar(page: Page) -> None:
    """Clica uma única vez no botão 'Enviar resposta'.

    T44: depois do clique espera o envio do formulário sair de /wordings/new
    antes de qualquer outra navegação (ir direto para a lista poderia
    interromper o envio). Se a página não mudar em 30 s, segue: a
    confirmação na lista decide."""
    from playwright.sync_api import TimeoutError as PWTimeoutError
    btn = page.locator("input[type='submit'][value='Enviar resposta'][name='commit']").first
    if btn.count() == 0:
        raise BotaoEnviarAusente("input[value='Enviar resposta']")  # T48: antes do clique
    btn.click()
    try:
        page.wait_for_url(lambda url: "/wordings/new" not in url, timeout=30000)
    except PWTimeoutError:
        log.warning("Pagina continuou no formulario 30 s apos o clique; conferindo na lista.")


def _contar(situacoes: list[str], palavra: str) -> int:
    return sum(1 for s in situacoes if palavra in s)


# Situações já vistas no site (as linhas antigas podem andar de uma para outra)
_SITUACOES_CONHECIDAS = ("pendente", "processando", "corrigid", "erro")


def _desconhecidas(situacoes: list[str]) -> int:
    return sum(1 for s in situacoes if not any(p in s for p in _SITUACOES_CONHECIDAS))


def aguardar_confirmacao(page: Page, codigo_tema: str, timeout_segundos: int = 120,
                         linhas_esperadas: int = 1, antes: list[str] | None = None,
                         data_hoje: str | None = None) -> bool:
    """Aguarda confirmação do envio na lista remota.
    
    Recarrega /minhas-redacoes a cada 5s até:
    - Nova linha com o código e data de hoje aparecer como "Pendente"
    - Timeout
    
    Retorna True se confirmado, False se erro/cancelada. Bug 008: linha nova
    numa situação nunca observada (ex.: "Recusada") não é sucesso: espera e,
    no fim do prazo, ConfirmacaoInconclusiva (REVISAO_MANUAL).

    T27: se no fim do prazo a linha nova (código + hoje) ainda estiver em
    "Processando arquivo", conta como RECEBIDA (True): antes do envio a
    lista não tinha esse tema hoje, então a linha só pode ser a nossa.
    Sem linha nenhuma no prazo -> ConfirmacaoInconclusiva.

    T35: ``linhas_esperadas`` = linhas desse tema hoje antes do clique + 1.
    Só conta como recebida quando a lista chega a esse número (vale para
    várias redações do mesmo tema no mesmo dia).

    T44: ``antes`` = situações das linhas desse tema hoje ANTES do clique.
    Só a linha nova é julgada: uma redação anterior do dia já "Corrigida"
    não impede a confirmação, e um "erro" antigo não vira falso erro.
    ``data_hoje`` vem de quem contou antes do clique (mesmo dia nas duas
    pontas). CAPTCHA/domínio estranho na espera sobe na hora."""
    from modulos.base import relogio

    data_hoje = data_hoje or relogio.data_site()
    antes = antes or []
    inicio = time.time()
    viu_processando = False
    viu_desconhecida = False

    while time.time() - inicio < timeout_segundos:
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)

            do_dia = situacoes_tema_hoje(ler_lista_redacoes(page), codigo_tema, data_hoje)
            if len(do_dia) >= linhas_esperadas:
                # T48: a linha nova é a que fez a contagem subir. Uma linha
                # antiga que muda de situação (corrigida) durante a espera
                # não atrapalha; só um "erro" a mais ou "processando" a mais
                # contam como notícia da linha nova.
                if _contar(do_dia, "erro") > _contar(antes, "erro"):
                    return False
                if _contar(do_dia, "processando") > _contar(antes, "processando"):
                    viu_processando = True
                elif _desconhecidas(do_dia) > _desconhecidas(antes):
                    # Bug 008: situação nunca observada (ex.: "Recusada")
                    # não é sucesso: espera e, no fim do prazo, inconclusiva.
                    viu_desconhecida = True
                else:
                    return True
        except CaptchaOuBloqueio:
            raise
        except Exception as e:
            log.warning("Lista ainda nao conferida (%s); tentando de novo.", type(e).__name__)
        time.sleep(5)

    if viu_desconhecida:
        raise ConfirmacaoInconclusiva(f"Linha nova do tema {codigo_tema} com situacao desconhecida "
                                      f"apos {timeout_segundos}s; conferir no site")
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