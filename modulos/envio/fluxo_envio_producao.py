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
import sqlite3
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright

from modulos.base import tela
from modulos.base.config import Config, obter_senha
from modulos.site.login import login, confirmar_identidade, DOMINIO_ESPERADO
from modulos.site.formulario_envio import verificar_dominio_autorizado
from modulos.site.confirmacao import logout
from modulos.dados.planilha_arquivos import ResultadoConciliacao, mascarar_email
from modulos.envio.fila_producao import LoteAluno, montar_lote_producao
from modulos.envio.envio_item import enviar_item
from modulos.base.excecoes import CaptchaOuBloqueio
from modulos.base.trava import TravaOcupada, trava_de_envio
from modulos.base.copia_seguranca import copiar_caderno
from modulos.base.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, ERRO, REVISAO_MANUAL


log = logging.getLogger("automacao_redacoes")

PARAR_TUDO = "PARAR_TUDO"
FALHA_LOGIN = "FALHA_LOGIN"
# T48: logins seguidos que falham (senha padrão errada, CAPTCHA, conta
# travada) param a execução em vez de tentar aluno por aluno.
MAX_FALHAS_LOGIN_SEGUIDAS = 2


def _motivo_login(e: Exception) -> str:
    """Motivo legível (sem e-mail completo nem senha) de uma falha de login."""
    from modulos.base.excecoes import IdentidadeDivergente, LoginFalhou
    if isinstance(e, IdentidadeDivergente):
        return "o site abriu a conta de outra pessoa (identidade nao confere)"
    if isinstance(e, LoginFalhou):
        return "o site nao aceitou o login (senha do alunos.csv errada? conta bloqueada?)"
    return f"erro inesperado ({type(e).__name__})"


def _pausa(cfg: Config) -> None:
    """Pausa aleatória entre envios (T24, P7)."""
    time.sleep(random.uniform(cfg.pausa_envio_min_segundos, cfg.pausa_envio_max_segundos))


class Andamento:
    """T51: progresso ao vivo do envio ("23 de 61 redações · faltam ~19 min").
    A estimativa é o tempo médio por redação até agora (pausas incluídas)."""

    def __init__(self, total: int, saida=print, relogio=time.monotonic, unidade: str = "redações"):
        self.total, self.feitas = total, 0
        self._saida, self._relogio, self._unidade = saida, relogio, unidade
        self._inicio = relogio()

    def chegar_a(self, feitas: int) -> None:
        """Mostra a linha de progresso quando o número de feitas muda."""
        feitas = min(max(feitas, self.feitas), self.total)
        if feitas != self.feitas:
            self.feitas = feitas
            self._saida(tela.linha_progresso(self.feitas, self.total, self._relogio() - self._inicio,
                                             self._unidade))

    def avancar(self) -> None:
        self.chegar_a(self.feitas + 1)


def _marcar_aluno(progresso, lote: LoteAluno, estado: str, detalhe: str) -> None:
    if progresso:
        for item in lote.itens:
            progresso.marcar(lote.aluno.id, item.chave_progresso, estado,
                             pasta=item.codigo, detalhe=detalhe)


def _enviar_lote_aluno(page, cfg: Config, senha: str, lote: LoteAluno,
                       progresso, contagem: dict[str, int],
                       andamento: Optional[Andamento] = None) -> Optional[str]:
    """Envia os itens de um aluno. Retorna PARAR_TUDO para encerrar a execução.
    ``senha``: a da conta de teste ou, M3, a do próprio aluno (alunos.csv)."""
    aluno = lote.aluno
    try:
        page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        verificar_dominio_autorizado(page)
        login(page, cfg, aluno.email, senha)
        confirmar_identidade(page, aluno)  # M3: nome exato para todos
    except CaptchaOuBloqueio as e:
        log.error("Captcha/bloqueio no login de %s: %s. Parando a execucao.", aluno.nome, e)
        _marcar_aluno(progresso, lote, ERRO, f"Captcha/bloqueio no login: {e}")
        contagem[ERRO] += len(lote.itens)
        return PARAR_TUDO
    except Exception as e:
        motivo = _motivo_login(e)
        log.error("Login/identidade falhou para %s (%s): %s. Pulando aluno.",
                  aluno.nome, mascarar_email(aluno.email), motivo)
        _marcar_aluno(progresso, lote, ERRO, f"Login/identidade: {motivo}")
        contagem[ERRO] += len(lote.itens)
        return FALHA_LOGIN

    for n, item in enumerate(lote.itens, 1):
        if n > 1:
            _pausa(cfg)
        log.info("%s — item %d/%d: tema %s (%s)", aluno.nome, n, len(lote.itens),
                 item.codigo, item.chave_progresso)
        try:
            estado = enviar_item(page, aluno.id, item, progresso)
        except CaptchaOuBloqueio as e:
            estado = getattr(e, "estado", ERRO)
            contagem[estado] = contagem.get(estado, 0) + 1
            log.error("Captcha/bloqueio durante o envio (%s). Parando a execucao.", item.chave_progresso)
            return PARAR_TUDO
        contagem[estado] = contagem.get(estado, 0) + 1
        if andamento:
            andamento.avancar()
        if estado == REVISAO_MANUAL:
            log.error("Resultado inconclusivo apos clique (%s). Parando a execucao.", item.chave_progresso)
            return PARAR_TUDO
        if estado not in (ENVIADO, JA_ENVIADO):
            log.error("Item com %s; parando este aluno e seguindo para o proximo.", estado)
            return None
    return None


# O que fazer com cada estado que pede ação (T47)
_ACAO = {
    REVISAO_MANUAL: ("Conferir no site", "abra o site NA CONTA DESTE ALUNO e veja se a redação deste tema "
                                         "chegou hoje; depois responda em: python main.py --resolver"),
    ERRO: ("Não enviadas", "nada foi enviado; resolva o motivo e rode de novo (ele tenta outra vez)"),
}


def mostrar_o_que_precisa_de_voce(lotes: list[LoteAluno], progresso: Progresso) -> int:
    """T47: no fim do envio, uma lista só com o que pede ação humana, aluno
    por aluno, com o motivo e o que fazer. Retorna quantos itens."""
    pendentes: dict[str, list] = {}
    nao_tentados = 0
    for lote in lotes:
        for item in lote.itens:
            registro = progresso.obter(lote.aluno.id, item.chave_progresso) or {}
            estado = registro.get("estado", "")
            if estado in _ACAO:
                pendentes.setdefault(estado, []).append((lote.aluno.nome, item, registro.get("detalhe", "")))
            elif estado not in (ENVIADO, JA_ENVIADO):
                nao_tentados += 1
    if not pendentes and not nao_tentados:
        return 0
    tela.secao("O que precisa de você")
    for estado in (REVISAO_MANUAL, ERRO):
        if estado not in pendentes:
            continue
        titulo, acao = _ACAO[estado]
        tela.status("aviso" if estado == REVISAO_MANUAL else "erro",
                    f"{titulo} ({len(pendentes[estado])}): {acao}")
        for nome, item, detalhe in pendentes[estado]:
            arquivo = tela.link_arquivo(Path(item.caminho).parent.parent, item.pasta, item.arquivo)  # T51
            tela.status("fraco", f"{nome} - tema {item.codigo} - {arquivo}: {detalhe}", recuo=6)
    if nao_tentados:
        tela.status("info", f"{nao_tentados} redação(ões) não chegaram a ser tentadas: vão na próxima execução.")
    return sum(len(v) for v in pendentes.values()) + nao_tentados


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
    lotes: Optional[list[LoteAluno]] = None,
) -> int:
    """Retorna 0 = tudo enviado/já enviado; 1 = houve ERRO/REVISAO_MANUAL ou
    parada; 2 = cancelado na confirmação ou produção bloqueada.

    ``conta_teste`` (T40): e-mail da conta de teste. O mesmo fluxo, mas só
    aceita lote em que TODOS os alunos são essa conta, pede ENVIAR TESTE e usa
    ESQUEMA_SENHA_TESTE. Assim a trava de produção não se aplica a ele.
    ``lotes`` (T42): lote já montado (ensaio); passa pelas mesmas travas."""
    from modulos.base import config as config_mod
    if not conta_teste and config_mod.PRODUCAO_BLOQUEADA:  # segunda trava, além da do main (22/10)
        tela.bloqueado(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA)
        return 2
    if lotes is None:
        lotes, ignorados = montar_lote_producao(
            resultado, Path(cfg.pasta_raiz), progresso,
            limite_alunos=limite_alunos, limite_redacoes=limite_redacoes,
        )
        for chave, motivo in ignorados:
            log.warning("Fora do lote: %s (%s)", chave, motivo)
    total = sum(len(lote.itens) for lote in lotes)
    if not total:
        tela.info("Nada para enviar agora.")
        return 0
    if conta_teste and any(l.aluno.email.casefold() != conta_teste.casefold() for l in lotes):
        tela.erro("Lote de teste com aluno que nao e a conta de teste. Nada foi enviado.")
        return 2
    if not conta_teste:
        # M3: sem senha no alunos.csv o aluno nem chega a fazer login
        for lote in (l for l in lotes if not l.aluno.senha):
            tela.erro(f"{lote.aluno.nome}: sem senha no alunos.csv da turma; "
                      f"{len(lote.itens)} redação(ões) dele(a) ficam fora deste envio.")
        lotes = [l for l in lotes if l.aluno.senha]
        total = sum(len(lote.itens) for lote in lotes)
        if not total:
            tela.info("Nada para enviar agora.")
            return 0

    rotulo = "teste" if conta_teste else "produção"
    palavra = "ENVIAR TESTE" if conta_teste else "ENVIAR"
    tela.titulo(f"ENVIO DE {rotulo.upper()}  ·  {len(lotes)} aluno(s), {total} redação(ões)")
    tela.secao(f"Lote de {rotulo}")
    for lote in lotes:
        print(f"  {tela.c(lote.aluno.nome, 'titulo')} {tela.c(f'<{mascarar_email(lote.aluno.email)}>', 'fraco')}")
        for item in lote.itens:
            tela.status("info", f"tema {item.codigo}: {item.chave_progresso}", recuo=4)
    tela.secao("Como funciona")
    tela.status("fraco", "Vai sozinho, aluno por aluno. O que já está no site hoje é pulado.")
    tela.status("fraco", "Erro antes do clique: nada é enviado e segue para o próximo aluno.")
    tela.status("fraco", "Dúvida depois do clique, CAPTCHA ou 2 logins falhando: para tudo e avisa.")
    print()
    confirmacao = tela.perguntar(
        f"  Digite {tela.c(palavra, 'tecla')} para confirmar o lote (qualquer outro texto cancela): ")
    if confirmacao != palavra:
        tela.aviso("Cancelado: nada foi enviado.")
        return 2
    tela.secao("Enviando")

    try:
        # M3: trava e cópias são globais (ao lado do caderno), não da turma
        with trava_de_envio(Path(cfg.banco_progresso).parent / "envio.trava"):
            return _enviar_com_navegador(cfg, lotes, progresso, conta_teste, rotulo)
    except TravaOcupada:
        tela.erro("Outro envio está rodando agora (outra janela?). Espere ele acabar. Nada foi enviado.")
        return 2


def _enviar_com_navegador(cfg: Config, lotes: list[LoteAluno], progresso, conta_teste, rotulo: str) -> int:
    from modulos.base import relogio
    if relogio.perto_da_meia_noite():  # T48: uma vez, antes de abrir o navegador
        tela.erro("Perto da meia-noite (23:55 a 00:05): a contagem do dia ficaria errada. "
                  "Rode de novo daqui a alguns minutos. Nada foi enviado.")
        return 2
    if progresso:
        # T47: cópia do caderno ANTES de qualquer clique; sem cópia, não envia
        try:
            copia = copiar_caderno(progresso.con, Path(cfg.banco_progresso).parent / "copias")
        except (OSError, sqlite3.Error) as e:
            tela.erro(f"Não consegui guardar a cópia de segurança do caderno ({type(e).__name__}). "
                      "Nada foi enviado.")
            return 2
        tela.info(f"Cópia de segurança do caderno: {tela.caminho(copia)}")
    senha_teste = obter_senha("ESQUEMA_SENHA_TESTE") if conta_teste else ""
    contagem = {ENVIADO: 0, JA_ENVIADO: 0, ERRO: 0, REVISAO_MANUAL: 0}
    parou = False
    falhas_login = 0
    andamento = Andamento(sum(len(lote.itens) for lote in lotes))
    feitas_antes = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        try:
            for n, lote in enumerate(lotes, 1):
                if n > 1:
                    _pausa(cfg)
                log.info("Aluno %d de %d: %s", n, len(lotes), lote.aluno.nome)
                # Um contexto por aluno: nada de sessão de um aluno no outro (P5)
                context = browser.new_context()
                page = context.new_page()
                try:
                    resultado = _enviar_lote_aluno(page, cfg, senha_teste if conta_teste else lote.aluno.senha,
                                                   lote, progresso, contagem, andamento=andamento)
                    # Itens pulados (login falhou, erro parou o aluno) também contam como "passados"
                    feitas_antes += len(lote.itens)
                    if resultado != PARAR_TUDO:
                        andamento.chegar_a(feitas_antes)
                    falhas_login = falhas_login + 1 if resultado == FALHA_LOGIN else 0
                    if resultado == PARAR_TUDO or falhas_login >= MAX_FALHAS_LOGIN_SEGUIDAS:
                        if falhas_login >= MAX_FALHAS_LOGIN_SEGUIDAS:
                            log.error("%d logins seguidos falharam. Parando a execucao "
                                      "(confira as senhas do alunos.csv e o site).", falhas_login)
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

    tela.secao(f"Resumo do envio de {rotulo}")
    tela.contagens([("Enviadas", contagem.get(ENVIADO, 0), "ok"),
                    ("Já estavam no site", contagem.get(JA_ENVIADO, 0), "info"),
                    ("Não enviadas (erro)", contagem.get(ERRO, 0), "erro"),
                    ("Conferir no site", contagem.get(REVISAO_MANUAL, 0), "aviso")])
    if parou:
        tela.erro("Envio PARADO antes do fim. Veja abaixo o que precisa de você antes de rodar de novo.")
    elif not contagem[ERRO] and not contagem[REVISAO_MANUAL]:
        tela.ok("Tudo certo.")
    if progresso:
        mostrar_o_que_precisa_de_voce(lotes, progresso)
        tela.info(f"Relatorio do envio: {tela.caminho(gravar_relatorio_envio(lotes, progresso, cfg.pasta_relatorios))}")
    return 1 if parou or contagem[ERRO] or contagem[REVISAO_MANUAL] else 0
