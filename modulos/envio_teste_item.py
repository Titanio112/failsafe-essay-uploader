"""Envio de UM item da fila de teste, com fail-closed (T18B-T18D).

Antes do clique, qualquer falha -> ERRO. Depois de iniciar o clique,
qualquer resultado inconclusivo -> REVISAO_MANUAL. Sem retry, sem 2º clique.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from modulos.lista_redacoes import ler_saldo_creditos, ler_lista_redacoes, detectar_ja_enviado
from modulos.formulario_envio import (
    abrir_formulario_envio,
    ler_combo_temas,
    selecionar_tema_por_codigo,
    selecionar_criterio,
    anexar_arquivo,
    aguardar_upload_aceito,
)
from modulos.confirmacao import clicar_enviar, aguardar_confirmacao
from modulos.fila_teste import ItemFilaTeste
from modulos.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL
from modulos.excecoes import CaptchaOuBloqueio, ConfirmacaoInconclusiva


log = logging.getLogger("automacao_redacoes")


def _codigo_tema_selecionado(page) -> Optional[str]:
    """Le o codigo (string exata) da opcao selecionada no combo de temas."""
    texto = page.locator(
        "select[name='wording[wording_proposal_id]'] option:checked"
    ).first.inner_text().strip()
    match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", texto)
    return match.group(1) if match else None


def enviar_item_teste(
    page,
    aluno_id: str,
    item: ItemFilaTeste,
    progresso: Optional[Progresso] = None,
) -> str:
    """Tenta enviar um item. Retorna o estado final gravado:
    ENVIADO ou JA_ENVIADO (pode seguir) / ERRO ou REVISAO_MANUAL (parar)."""

    def marcar(estado: str, detalhe: str) -> str:
        if progresso:
            progresso.marcar(aluno_id, item.arquivo, estado, pasta=item.codigo, detalhe=detalhe)
        return estado

    codigo = item.codigo
    clique_iniciado = False
    try:
        # 1. Saldo (fail-closed se None ou 0)
        saldo = ler_saldo_creditos(page)
        if saldo is None or saldo == 0:
            log.warning("Saldo de creditos indisponivel ou zero (%s). Abortando sem enviar.", saldo)
            return marcar(ERRO, f"Saldo indisponivel/zero: {saldo}")

        # 2. Duplicidade: mesmo dia + mesmo tema -> pula e segue
        ja_enviado, data_envio = detectar_ja_enviado(ler_lista_redacoes(page), codigo)
        if ja_enviado:
            log.info("Tema %s ja enviado em %s. Pulando.", codigo, data_envio)
            return marcar(JA_ENVIADO, "Ja enviado na lista remota")

        # 3. Formulario e codigo no combo (fail-closed)
        abrir_formulario_envio(page)
        codigos_disponiveis = {t[0] for t in ler_combo_temas(page)}
        if codigo not in codigos_disponiveis:
            log.error("Codigo %s nao encontrado no combo de temas do site. Disponiveis: %s",
                      codigo, sorted(codigos_disponiveis))
            return marcar(ERRO, f"Codigo nao existe no combo: {sorted(codigos_disponiveis)}")

        # 4. Selecionar tema e conferir o codigo selecionado (fail-closed)
        selecionado = selecionar_tema_por_codigo(page, codigo)
        codigo_selecionado = _codigo_tema_selecionado(page) if selecionado else None
        if codigo_selecionado != codigo:
            log.error("Tema nao selecionado/conferido: esperado %s, obtido %s",
                      codigo, codigo_selecionado)
            return marcar(ERRO, f"Tema selecionado diferente: {codigo_selecionado}")

        # 5. Criterio ENEM (fixo em selecionar_criterio), anexo e upload aceito
        selecionar_criterio(page)
        anexar_arquivo(page, str(item.caminho))
        if not aguardar_upload_aceito(page):
            log.error("Upload nao aceito para %s. Abortando sem enviar.", item.arquivo)
            return marcar(ERRO, "Upload nao aceito (sem sinal Arquivo carregado)")

        # 6. ENVIANDO antes do clique; clique unico
        marcar("ENVIANDO", "Upload aceito, clicando em enviar")
        clique_iniciado = True
        clicar_enviar(page)

        # 7. Confirmacao (Pendente, timeout 120s)
        if aguardar_confirmacao(page, codigo, timeout_segundos=120):
            log.info("Envio confirmado: tema %s -> Pendente", codigo)
            return marcar(ENVIADO, "Confirmado na lista remota")
        log.error("Timeout ou falha na confirmacao do envio para tema %s", codigo)
        return marcar(REVISAO_MANUAL, "Confirmacao inconclusiva apos clique")

    except CaptchaOuBloqueio as e:
        log.error("Captcha ou dominio bloqueado: %s", e)
        return marcar(REVISAO_MANUAL if clique_iniciado else ERRO, f"Captcha/bloqueio: {e}")
    except ConfirmacaoInconclusiva as e:
        log.error("Confirmacao inconclusiva apos clique: %s", e)
        return marcar(REVISAO_MANUAL, f"Confirmacao inconclusiva apos clique: {e}")
    except Exception as e:
        log.exception("Erro inesperado durante envio de teste: %s", e)
        return marcar(REVISAO_MANUAL if clique_iniciado else ERRO, f"Excecao: {type(e).__name__}")
