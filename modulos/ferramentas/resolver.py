"""Resolver as redações em REVISAO_MANUAL (T49): `python main.py --resolver`.

REVISAO_MANUAL = o script clicou em Enviar mas não conseguiu confirmar na
lista do site. Ele nunca reenvia sozinho (poderia duplicar). A pessoa olha
o site na conta do aluno e responde aqui:

- ``s`` (chegou): vira ENVIADO e nunca mais é enviada;
- ``n`` (não chegou): vira ERRO e vai de novo na próxima execução;
- Enter: deixa como está.

A data do registro não muda (a contagem "de hoje" continua certa) e cada
resposta fica em relatorios/resolucoes_<data>.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

from modulos.base import relogio, tela
from modulos.base.progresso_relatorio import ENVIADO, ERRO, REVISAO_MANUAL, Progresso
from modulos.dados.planilha_arquivos import mascarar_email

Entrada = Callable[[str], str]
COLUNAS_LOG = ["aluno", "arquivo", "tema", "antes", "depois", "resposta", "quando"]


def executar_resolver(banco: Path, pasta_relatorios: Path, nomes: dict[str, str] | None = None,
                      entrada: Entrada | None = None, saida: Callable = print,
                      pasta_raiz: Path | None = None) -> int:
    """``nomes``: {aluno_id: nome} para mostrar o nome em vez do e-mail.
    Retorna quantos itens foram resolvidos."""
    nomes = nomes or {}
    tela.titulo("RESOLVER REVISÕES  ·  o script não envia nada aqui", saida)
    if not Path(banco).is_file():
        tela.info("Ainda não há caderno de envios: nada para resolver.", saida)
        return 0
    with Progresso(banco) as prog:
        pendentes = prog.con.execute(
            "SELECT aluno_id, arquivo, pasta, detalhe, atualizado_em FROM progresso "
            "WHERE estado = ? ORDER BY atualizado_em", (REVISAO_MANUAL,)).fetchall()
        if not pendentes:
            tela.ok("Nenhuma redação em revisão manual.", saida)
            return 0
        tela.texto("Para cada uma: abra o site NA CONTA DO ALUNO, em Minhas redações, e veja se a "
                   "redação desse tema aparece na data indicada.", saida)
        log_csv = Path(pasta_relatorios) / f"resolucoes_{relogio.agora():%Y%m%d_%H%M%S}.csv"
        resolvidos = 0
        for n, (aluno_id, arquivo, tema, detalhe, quando) in enumerate(pendentes, 1):
            data = _data_br(quando)
            tela.cabecalho(f"{n} de {len(pendentes)}:  {nomes.get(aluno_id, mascarar_email(aluno_id))}", saida)
            caminho = arquivo.removeprefix("ensaio/")
            raiz_foto = _raiz_da_foto(pasta_raiz, aluno_id, arquivo, nomes)
            if raiz_foto and "/" in caminho:  # T51: Ctrl+clique abre a foto
                caminho = tela.link_arquivo(raiz_foto, *caminho.split("/", 1))
            saida(f"  Arquivo: {caminho}")
            saida(f"  Tema:    {tema}    Enviado em: {data}")
            saida(tela.c(f"  Motivo:  {detalhe}", "fraco"))
            foto = _foto(pasta_raiz, aluno_id, arquivo, nomes)
            opcoes = [("s", "chegou no site (marca como enviada)"),
                      ("n", "não chegou (vai de novo na próxima vez)")]
            if foto:
                opcoes.append(("v", "ver a foto"))
            tela.menu(opcoes + [("Enter", "deixar para depois"), ("q", "sair")], saida)
            resposta = tela.perguntar("  > ", entrada).lower()
            while resposta == "v" and foto:  # T52: abre no visualizador do Windows
                motivo = tela.abrir(foto)
                if motivo:
                    tela.erro(f"Não abriu a foto: {motivo}", saida)
                resposta = tela.perguntar("  > ", entrada).lower()
            if resposta == "q":
                break
            if resposta not in ("s", "n"):
                continue
            novo = ENVIADO if resposta == "s" else ERRO
            texto = ("resolvido a mao: chegou no site" if novo == ENVIADO
                     else "resolvido a mao: nao chegou; vai de novo")
            # Só estado e detalhe: a data fica a do envio (contagem do dia)
            prog.con.execute("UPDATE progresso SET estado = ?, detalhe = ? WHERE aluno_id = ? AND arquivo = ?",
                             (novo, texto, aluno_id, arquivo))
            prog.con.commit()
            _registrar(log_csv, [nomes.get(aluno_id, aluno_id), arquivo, tema, REVISAO_MANUAL, novo,
                                 resposta, relogio.agora().isoformat(timespec="seconds")])
            tela.status("ok" if novo == ENVIADO else "aviso",
                        "Marcada como enviada." if novo == ENVIADO else "Liberada para enviar de novo.", saida)
            resolvidos += 1
    tela.secao("Fim", saida)
    tela.status("ok", f"{resolvidos} de {len(pendentes)} resolvida(s).", saida)
    if resolvidos:
        tela.info(f"Registro: {tela.caminho(log_csv)}", saida)
    return resolvidos


def _raiz_da_foto(pasta_raiz, aluno_id: str, arquivo: str, nomes: dict) -> Path | None:
    """T56: registro do modo teste (conta de teste, sem "ensaio/") mora em
    testes/redacoes_teste, não na pasta real: abrir a real mostraria a foto
    de outra pessoa com o mesmo nome de pasta/arquivo."""
    if not pasta_raiz:
        return None
    from modulos.base.config import NOME_CONTA_TESTE, PASTA_TESTE, RAIZ
    if nomes.get(aluno_id) == NOME_CONTA_TESTE and not arquivo.startswith("ensaio/"):
        return RAIZ / PASTA_TESTE
    return Path(pasta_raiz)


def _foto(pasta_raiz, aluno_id: str, arquivo: str, nomes: dict) -> Path | None:
    """A foto do registro, só se o arquivo existe (senão não oferece o "v")."""
    raiz = _raiz_da_foto(pasta_raiz, aluno_id, arquivo, nomes)
    foto = raiz / arquivo.removeprefix("ensaio/") if raiz else None
    return foto if foto and foto.is_file() else None


def _data_br(quando: str) -> str:
    from datetime import datetime
    try:
        return datetime.fromisoformat(quando).astimezone(relogio.FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return quando or "?"


def _registrar(log_csv: Path, linha: list) -> None:
    log_csv.parent.mkdir(parents=True, exist_ok=True)
    novo = not log_csv.is_file()
    with open(log_csv, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        if novo:
            escritor.writerow(COLUNAS_LOG)
        escritor.writerow(linha)
