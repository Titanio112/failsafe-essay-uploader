"""Envio de UM item (modo teste e produção), com fail-closed (T18B-T18D).

Antes do clique, qualquer falha -> ERRO. Depois de iniciar o clique,
qualquer resultado inconclusivo -> REVISAO_MANUAL. Sem retry, sem 2º clique.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from modulos.base import relogio
from modulos.site.lista_redacoes import (
    contar_tema_hoje,
    ler_lista_redacoes,
    ler_saldo_creditos,
    situacoes_tema_hoje,
)
from modulos.site.formulario_envio import (
    abrir_formulario_envio,
    ler_combo_temas,
    selecionar_tema_por_codigo,
    selecionar_criterio,
    anexar_arquivo,
    aguardar_upload_aceito,
)
from modulos.site.confirmacao import clicar_enviar, aguardar_confirmacao
from modulos.envio.fila_teste import ItemFilaTeste
from modulos.base.progresso_relatorio import (
    Progresso, ENVIADO, ENVIANDO, JA_ENVIADO, ERRO, REVISAO_MANUAL,
)
from modulos.base.excecoes import BotaoEnviarAusente, CaptchaOuBloqueio, ConfirmacaoInconclusiva


log = logging.getLogger("automacao_redacoes")

# Estados em que o item (ou a mesma foto) já não pode ir de novo
_JA_REGISTRADO = {ENVIADO, JA_ENVIADO, REVISAO_MANUAL, ENVIANDO}


def _ja_registrado(progresso: Optional[Progresso], aluno_id: str, item: ItemFilaTeste) -> Optional[str]:
    """Estado do caderno que impede o envio deste item AGORA (já dentro da
    trava), ou None. Confere a chave do item e a mesma foto (sha256)."""
    if not progresso:
        return None
    chave = item.chave_progresso or item.arquivo
    registro = progresso.obter(aluno_id, chave)
    if registro and registro["estado"] in _JA_REGISTRADO:
        return registro["estado"]
    mesma_foto = progresso.registro_do_conteudo(aluno_id, item.hash_arquivo, exceto=chave)
    return mesma_foto["estado"] if mesma_foto else None


def _codigo_tema_selecionado(page) -> Optional[str]:
    """Le o codigo (string exata) da opcao selecionada no combo de temas."""
    texto = page.locator(
        "select[name='wording[wording_proposal_id]'] option:checked"
    ).first.inner_text().strip()
    match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", texto)
    return match.group(1) if match else None


def enviar_item(
    page,
    aluno_id: str,
    item: ItemFilaTeste,
    progresso: Optional[Progresso] = None,
) -> str:
    """Tenta enviar um item. Retorna o estado final gravado:
    ENVIADO ou JA_ENVIADO (pode seguir) / ERRO ou REVISAO_MANUAL (parar).
    CAPTCHA/bloqueio: grava o estado e levanta CaptchaOuBloqueio (com
    ``.estado``) para o fluxo parar tudo (T44)."""

    def marcar(estado: str, detalhe: str) -> str:
        if progresso:
            chave = item.chave_progresso or item.arquivo
            progresso.marcar(aluno_id, chave, estado, pasta=item.codigo, detalhe=detalhe,
                             hash_arquivo=item.hash_arquivo)
        return estado

    codigo = item.codigo
    clique_iniciado = False
    try:
        # 0a. Bug 007: o lote é montado antes da trava de envio. Se outra
        #     janela já mandou este item (ou a mesma foto com outro nome)
        #     depois disso, o caderno diz agora: não envia de novo.
        ja = _ja_registrado(progresso, aluno_id, item)
        if ja:
            log.warning("%s: o caderno ja tem %s para este item. Nao envia de novo.",
                        item.chave_progresso or item.arquivo, ja)
            return REVISAO_MANUAL if ja in (REVISAO_MANUAL, ENVIANDO) else JA_ENVIADO

        # 0. T44: um "hoje" só (Brasília) para a contagem e a confirmação;
        #    perto da meia-noite os dois poderiam ser dias diferentes.
        if relogio.perto_da_meia_noite():
            log.warning("Perto da meia-noite: nao envia agora (a contagem do dia ficaria errada).")
            return marcar(ERRO, "Perto da meia-noite (23:55-00:05): rode de novo depois")
        data_hoje = relogio.data_site()

        # 1. Saldo (fail-closed se None ou 0)
        saldo = ler_saldo_creditos(page)
        if saldo is None or saldo == 0:
            log.warning("Saldo de creditos indisponivel ou zero (%s). Abortando sem enviar.", saldo)
            return marcar(ERRO, "Sem créditos na conta" if saldo == 0 else "Não consegui ler o saldo de créditos")

        # 2. Duplicidade por contagem (T35): linhas do tema HOJE no site x
        #    arquivos deste aluno/tema que o caderno (banco) marcou hoje.
        #    Com 1 arquivo no tema vale a regra antiga: tem hoje -> já enviado.
        lista = ler_lista_redacoes(page)
        no_site = contar_tema_hoje(lista, codigo, data_hoje)
        antes = situacoes_tema_hoje(lista, codigo, data_hoje)
        no_caderno = progresso.enviados_hoje(aluno_id, codigo) if progresso else 0
        # T48: o caderno pode ter envios de hoje que não estão neste lote
        # (ensaio e modo teste na mesma conta, arquivo enviado e depois tirado
        # da pasta): este item ainda não foi, então o total é ao menos +1.
        total = max(item.total_mesmo_tema, no_caderno + 1, 1)
        if no_site >= total:
            log.info("Tema %s: site ja tem %d hoje (de %d). Pulando.", codigo, no_site, total)
            return marcar(JA_ENVIADO, f"Ja enviado na lista remota ({no_site} hoje de {total})")
        if no_site != no_caderno:
            log.error("Tema %s: site tem %d hoje, caderno tem %d. Nao envia; conferir a mao.",
                      codigo, no_site, no_caderno)
            return marcar(ERRO, f"Contagem diverge: o site tem {no_site} deste tema hoje e o caderno {no_caderno} "
                                "(alguém enviou pelo site? confira a conta; amanhã a contagem zera)")

        # 3. Formulario e codigo no combo (fail-closed)
        abrir_formulario_envio(page)
        codigos_combo = [t[0] for t in ler_combo_temas(page)]
        codigos_disponiveis = set(codigos_combo)
        if codigos_combo.count(codigo) > 1:
            # Bug 001: ex. 0000 = dois Simulados; selecionar pegaria o 1º às cegas
            log.error("Codigo %s aparece %dx no combo. Nao envia (revisao manual).",
                      codigo, codigos_combo.count(codigo))
            return marcar(ERRO, f"Codigo {codigo} repetido no combo (revisao manual)")
        if codigo not in codigos_disponiveis:
            log.error("Codigo %s nao encontrado no combo de temas do site. Disponiveis: %s",
                      codigo, sorted(codigos_disponiveis))
            return marcar(ERRO, f"O tema {codigo} não aparece na lista de temas desta conta")

        # 4. Selecionar tema e conferir o codigo selecionado (fail-closed)
        selecionado = selecionar_tema_por_codigo(page, codigo)
        codigo_selecionado = _codigo_tema_selecionado(page) if selecionado else None
        if codigo_selecionado != codigo:
            log.error("Tema nao selecionado/conferido: esperado %s, obtido %s",
                      codigo, codigo_selecionado)
            return marcar(ERRO, f"Não consegui marcar o tema {codigo} no formulário")

        # 5. Criterio ENEM conferido (T44), anexo e upload aceito
        if not selecionar_criterio(page):
            log.error("Criterio ENEM nao selecionado/conferido. Abortando sem enviar.")
            return marcar(ERRO, "Criterio ENEM nao conferido")
        anexar_arquivo(page, str(item.caminho))
        if not aguardar_upload_aceito(page):
            log.error("Upload nao aceito para %s. Abortando sem enviar.", item.arquivo)
            return marcar(ERRO, "Upload nao aceito (sem sinal Arquivo carregado)")

        # 6. ENVIANDO antes do clique; clique unico
        marcar("ENVIANDO", "Upload aceito, clicando em enviar")
        clique_iniciado = True
        clicar_enviar(page)

        # 7. Confirmacao (Pendente, timeout 120s)
        if aguardar_confirmacao(page, codigo, timeout_segundos=120, linhas_esperadas=no_site + 1,
                                antes=antes, data_hoje=data_hoje):
            log.info("Envio confirmado: tema %s -> Pendente", codigo)
            return marcar(ENVIADO, "Confirmado na lista remota")
        log.error("Timeout ou falha na confirmacao do envio para tema %s", codigo)
        return marcar(REVISAO_MANUAL, "Confirmacao inconclusiva apos clique")

    except CaptchaOuBloqueio as e:
        # T44 (P6): CAPTCHA/bloqueio PARA A EXECUÇÃO INTEIRA, não só o aluno.
        # Grava o estado e sobe a exceção (com o estado) para o fluxo parar.
        log.error("Captcha ou dominio bloqueado: %s", e)
        e.estado = marcar(REVISAO_MANUAL if clique_iniciado else ERRO, f"Captcha/bloqueio: {e}")
        raise
    except BotaoEnviarAusente as e:
        log.error("Botao Enviar nao encontrado: nada foi clicado (%s).", e)
        return marcar(ERRO, "Botao Enviar resposta nao encontrado (nada foi clicado)")
    except ConfirmacaoInconclusiva as e:
        log.error("Confirmacao inconclusiva apos clique: %s", e)
        return marcar(REVISAO_MANUAL, f"Confirmacao inconclusiva apos clique: {e}")
    except Exception as e:
        log.exception("Erro inesperado durante envio de teste: %s", e)
        return marcar(REVISAO_MANUAL if clique_iniciado else ERRO, f"Excecao: {type(e).__name__}")
