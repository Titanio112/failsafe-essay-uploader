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

from modulos.base.config import Config, obter_senha
from modulos.site.login import login, confirmar_identidade, DOMINIO_ESPERADO
from modulos.site.formulario_envio import verificar_dominio_autorizado
from modulos.site.confirmacao import logout
from modulos.dados.planilha_arquivos import ResultadoConciliacao, mascarar_email
from modulos.envio.fila_producao import LoteAluno, montar_lote_producao
from modulos.envio.envio_item import enviar_item
from modulos.base.excecoes import CaptchaOuBloqueio
from modulos.base.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL


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


def gravar_relatorio_envio(lotes: list[LoteAluno], progresso: Progresso, pasta: Path) -> Path:
    """relatorios/envio_<data_hora>.csv com o estado final de cada item do
    lote, lido do banco (T27). Item sem tentativa fica com o estado anterior
    (ex.: A_ENVIAR)."""
    import csv
    from datetime import datetime
    caminho = Path(pasta) / f"envio_{datetime.now():%Y%m%d_%H%M%S}.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["aluno", "email_mascarado", "arquivo", "tema", "estado", "detalhe", "atualizado_em"])
        for lote in lotes:
            for item in lote.itens:
                registro = progresso.obter(lote.aluno.id, item.chave_progresso) or {}
                escritor.writerow([
                    lote.aluno.nome, mascarar_email(lote.aluno.email), item.chave_progresso,
                    item.codigo, registro.get("estado", "NAO_TENTADO"),
                    registro.get("detalhe", ""), registro.get("atualizado_em", ""),
                ])
    return caminho


def executar_envio_producao(
    cfg: Config,
    resultado: ResultadoConciliacao,
    progresso: Optional[Progresso] = None,
    limite_alunos: Optional[int] = None,
    limite_redacoes: Optional[int] = None,
    conta_teste: Optional[str] = None,
) -> int:
    """Retorna 0 = tudo enviado/já enviado; 1 = houve ERRO/REVISAO_MANUAL ou
    parada; 2 = cancelado na confirmação ou produção bloqueada.

    ``conta_teste`` (T40): e-mail da conta de teste. O mesmo fluxo, mas só
    aceita lote em que TODOS os alunos são essa conta, pede ENVIAR TESTE e usa
    ESQUEMA_SENHA_TESTE. Assim a trava de produção não se aplica a ele."""
    from modulos.base import config as config_mod
    if not conta_teste and config_mod.PRODUCAO_BLOQUEADA:  # segunda trava, além da do main (22/10)
        print(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA)
        return 2
    lotes, ignorados = montar_lote_producao(
        resultado, Path(cfg.pasta_raiz), progresso,
        limite_alunos=limite_alunos, limite_redacoes=limite_redacoes,
    )
    for chave, motivo in ignorados:
        log.warning("Fora do lote: %s (%s)", chave, motivo)
    total = sum(len(lote.itens) for lote in lotes)
    if not total:
        print("Nada para enviar nesta execucao.")
        return 0
    if conta_teste and any(l.aluno.email.casefold() != conta_teste.casefold() for l in lotes):
        print("[ERRO] Lote de teste com aluno que nao e a conta de teste. Nada foi enviado.")
        return 2

    rotulo = "teste" if conta_teste else "producao"
    palavra = "ENVIAR TESTE" if conta_teste else "ENVIAR"
    print(f"Lote de {rotulo}: {len(lotes)} aluno(s), {total} redacao(oes).")
    print("Ja enviados hoje (mesmo tema) serao pulados. ERRO para so o aluno;")
    print("resultado inconclusivo apos o clique para a execucao inteira.")
    for lote in lotes:
        print(f"  {lote.aluno.nome} <{mascarar_email(lote.aluno.email)}>")
        for item in lote.itens:
            print(f"    tema {item.codigo}: {item.chave_progresso}")
    print()
    try:
        confirmacao = input(f"Digite {palavra} para confirmar o lote (qualquer outro texto cancela): ").strip()
    except (EOFError, OSError):
        confirmacao = ""  # sem terminal para digitar: cancela
    if confirmacao != palavra:
        print("Cancelado pelo usuario.")
        return 2

    senha = obter_senha("ESQUEMA_SENHA_TESTE" if conta_teste else "ESQUEMA_SENHA_PADRAO")
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
    print(f"Resumo do envio de {rotulo}:")
    for estado in (ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL):
        print(f"  {estado}: {contagem.get(estado, 0)}")
    if parou:
        print("Execucao PARADA antes do fim. Confira REVISAO_MANUAL no site antes de rodar de novo.")
    if progresso:
        print(f"Relatorio do envio: {gravar_relatorio_envio(lotes, progresso, cfg.pasta_relatorios)}")
    return 1 if parou or contagem[ERRO] or contagem[REVISAO_MANUAL] else 0
