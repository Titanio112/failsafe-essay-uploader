"""Fluxo de envio de produção (contas dos alunos).

Mostra o lote (fila_producao), pede ENVIAR uma vez, e para cada aluno:
contexto novo do navegador -> login -> identidade -> envio item a item
com envio_item (mesmo fail-closed do modo teste).

Falhas (T24, P6): login/identidade -> itens do aluno ERRO, segue para o
próximo aluno; ERRO num item -> para esse aluno; REVISAO_MANUAL ou
Captcha/bloqueio -> para a execução inteira.
"""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from modulos.config import Config, obter_senha
from modulos.login import login, confirmar_identidade, DOMINIO_ESPERADO
from modulos.formulario_envio import verificar_dominio_autorizado
from modulos.confirmacao import logout
from modulos.planilha_arquivos import ResultadoConciliacao, mascarar_email
from modulos.fila_producao import LoteAluno, montar_lote_producao
from modulos.envio_item import enviar_item
from modulos.excecoes import CaptchaOuBloqueio
from modulos.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL


log = logging.getLogger("automacao_redacoes")

PARAR_TUDO = "PARAR_TUDO"


def _pausa(cfg: Config) -> None:
    """Pausa aleatória entre envios (T24, P7)."""
    time.sleep(random.uniform(cfg.pausa_envio_min_segundos, cfg.pausa_envio_max_segundos))


def _marcar_aluno(progresso, lote: LoteAluno, estado: str, detalhe: str) -> None:
    if progresso:
        for item in lote.itens:
            progresso.marcar(lote.aluno.id, item.chave_progresso, estado,
                             pasta=item.codigo, detalhe=detalhe)


def _enviar_lote_aluno(page, cfg: Config, senha: str, lote: LoteAluno,
                       progresso, contagem: dict[str, int]) -> Optional[str]:
    """Envia os itens de um aluno. Retorna PARAR_TUDO para encerrar a execução."""
    aluno = lote.aluno
    try:
        page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        verificar_dominio_autorizado(page)
        login(page, cfg, aluno.email, senha)
        confirmar_identidade(page, aluno)
    except CaptchaOuBloqueio as e:
        log.error("Captcha/bloqueio no login de %s: %s. Parando a execucao.", aluno.nome, e)
        _marcar_aluno(progresso, lote, ERRO, f"Captcha/bloqueio no login: {e}")
        contagem[ERRO] += len(lote.itens)
        return PARAR_TUDO
    except Exception as e:
        log.error("Login/identidade falhou para %s (%s): %s. Pulando aluno.",
                  aluno.nome, mascarar_email(aluno.email), type(e).__name__)
        _marcar_aluno(progresso, lote, ERRO, f"Login/identidade: {type(e).__name__}")
        contagem[ERRO] += len(lote.itens)
        return None

    for n, item in enumerate(lote.itens, 1):
        if n > 1:
            _pausa(cfg)
        log.info("%s — item %d/%d: tema %s (%s)", aluno.nome, n, len(lote.itens),
                 item.codigo, item.chave_progresso)
        estado = enviar_item(page, aluno.id, item, progresso)
        contagem[estado] = contagem.get(estado, 0) + 1
        if estado == REVISAO_MANUAL:
            log.error("Resultado inconclusivo apos clique (%s). Parando a execucao.", item.chave_progresso)
            return PARAR_TUDO
        if estado not in (ENVIADO, JA_ENVIADO):
            log.error("Item com %s; parando este aluno e seguindo para o proximo.", estado)
            return None
    return None


def executar_envio_producao(
    cfg: Config,
    resultado: ResultadoConciliacao,
    progresso: Optional[Progresso] = None,
    limite_alunos: Optional[int] = None,
    limite_redacoes: Optional[int] = None,
) -> int:
    """Retorna 0 = tudo enviado/já enviado; 1 = houve ERRO/REVISAO_MANUAL ou
    parada; 2 = cancelado na confirmação."""
    lotes, ignorados = montar_lote_producao(
        resultado, Path(cfg.pasta_raiz), progresso,
        max_por_aluno=cfg.max_envios_por_aluno,
        limite_alunos=limite_alunos, limite_redacoes=limite_redacoes,
    )
    for chave, motivo in ignorados:
        log.warning("Fora do lote: %s (%s)", chave, motivo)
    total = sum(len(lote.itens) for lote in lotes)
    if not total:
        print("Nada para enviar nesta execucao.")
        return 0

    print(f"Lote de producao: {len(lotes)} aluno(s), {total} redacao(oes).")
    print("Ja enviados hoje (mesmo tema) serao pulados. ERRO para so o aluno;")
    print("resultado inconclusivo apos o clique para a execucao inteira.")
    for lote in lotes:
        print(f"  {lote.aluno.nome} <{mascarar_email(lote.aluno.email)}>")
        for item in lote.itens:
            print(f"    tema {item.codigo}: {item.chave_progresso}")
    print()
    confirmacao = input("Digite ENVIAR para confirmar o lote (qualquer outro texto cancela): ").strip()
    if confirmacao != "ENVIAR":
        print("Cancelado pelo usuario.")
        return 2

    senha = obter_senha("ESQUEMA_SENHA_PADRAO")
    contagem = {ENVIADO: 0, JA_ENVIADO: 0, ERRO: 0, REVISAO_MANUAL: 0}
    parou = False

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        try:
            for n, lote in enumerate(lotes, 1):
                if n > 1:
                    _pausa(cfg)
                log.info("Aluno %d/%d: %s", n, len(lotes), lote.aluno.nome)
                # Um contexto por aluno: nada de sessão de um aluno no outro (P5)
                context = browser.new_context()
                page = context.new_page()
                try:
                    if _enviar_lote_aluno(page, cfg, senha, lote, progresso, contagem) == PARAR_TUDO:
                        parou = True
                        break
                finally:
                    try:
                        logout(page)
                    except Exception:
                        pass  # logout e best-effort
                    context.close()
        finally:
            browser.close()

    print()
    print("Resumo do envio de producao:")
    for estado in (ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL):
        print(f"  {estado}: {contagem.get(estado, 0)}")
    if parou:
        print("Execucao PARADA antes do fim. Confira REVISAO_MANUAL no site antes de rodar de novo.")
    return 1 if parou or contagem[ERRO] or contagem[REVISAO_MANUAL] else 0
