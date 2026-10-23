"""Visual do terminal (T41): TODA a aparência da saída mora aqui.

Para mudar o visual (cores, símbolos, largura, linhas, barras), mexa só neste
arquivo. O resto do código diz apenas O QUE mostrar, com o papel de cada
linha (ok, aviso, erro...), e nunca escreve códigos de cor.

Cores só aparecem num terminal de verdade (nunca em teste nem em arquivo);
a variável de ambiente NO_COLOR desliga.
"""

from __future__ import annotations

import logging
import os
import sys
import textwrap
from typing import Callable, Iterable

# ─── Tudo que é visual ───────────────────────────────────────

LARGURA = 80

# Códigos ANSI das cores
CORES = {
    "verde": "32", "amarelo": "33", "vermelho": "31", "cinza": "90",
    "ciano": "36", "magenta": "35", "negrito": "1",
}

# Papel de cada pedaço da tela -> cor
PAPEIS = {
    "ok": "verde", "aviso": "amarelo", "erro": "vermelho", "bloqueado": "vermelho",
    "info": "ciano", "fraco": "cinza", "titulo": "negrito", "linha": "ciano",
    "tecla": "ciano", "pasta": "magenta",
}

# Símbolo no começo das linhas de status
SIMBOLOS = {
    "ok": "✔", "aviso": "⚠", "erro": "✘", "bloqueado": "⛔", "info": "•",
    "fraco": "·", "seta": "→", "pasta": "📁",
}

# Linhas dos títulos
LINHA_GROSSA = "═"
LINHA_FINA = "─"

# Barras de semelhança: verde a partir de VERDE_A_PARTIR, amarela a partir de AMARELO_A_PARTIR
VERDE_A_PARTIR = 85.0
AMARELO_A_PARTIR = 60.0
BARRA_CHEIA, BARRA_VAZIA, BARRA_TAMANHO = "█", "░", 10

# Estado da conciliação/envio -> papel (cor e símbolo da linha)
PAPEL_DO_ESTADO = {
    "EXATO_UNICO": "ok", "ENVIADO": "ok", "JA_ENVIADO": "info",
    "SUGESTAO_FUZZY": "aviso", "AMBIGUO": "aviso", "ARQUIVO_SEM_ALUNO": "aviso",
    "SEM_CODIGO": "aviso", "REVISAO_MANUAL": "aviso",
    "CODIGO_INVALIDO": "erro", "SIMULADO": "erro", "ERRO": "erro",
    "ALUNO_SEM_ARQUIVO": "fraco",
}

# Estado -> como aparece na tela (T50): palavras do dia a dia, não códigos
ROTULO_DO_ESTADO = {
    "EXATO_UNICO": "pronto", "SUGESTAO_FUZZY": "nome parecido", "AMBIGUO": "mais de um aluno",
    "ARQUIVO_SEM_ALUNO": "sem aluno", "ALUNO_SEM_ARQUIVO": "aluno sem arquivo",
    "SEM_CODIGO": "pasta sem tema", "CODIGO_INVALIDO": "tema fora do site",
    "SIMULADO": "tema repetido no site", "REVISAO_MANUAL": "decidir à mão",
    "ENVIADO": "enviada", "JA_ENVIADO": "já estava no site", "ERRO": "não enviada (erro)",
}


def rotulo(estado: str) -> str:
    return ROTULO_DO_ESTADO.get(estado, estado)


# ─── Cores ligadas/desligadas ────────────────────────────────

_cores = {"ativas": False}
Saida = Callable[[str], None]


def ativar_cores() -> None:
    """Liga as cores se a saída é um terminal de verdade."""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return
    if os.name == "nt":
        os.system("")  # liga as sequências ANSI no console do Windows
    _cores["ativas"] = True


def c(texto: str, papel: str) -> str:
    """Pinta o texto com a cor do papel (ou com a cor de nome igual)."""
    if not _cores["ativas"]:
        return texto
    cor = CORES.get(PAPEIS.get(papel, papel))
    return f"\033[{cor}m{texto}\033[0m" if cor else texto


# ─── Blocos da tela ──────────────────────────────────────────

def titulo(texto: str, saida: Saida = print) -> None:
    """Título grande, no começo de cada comando."""
    saida("")
    saida(c(LINHA_GROSSA * LARGURA, "linha"))
    saida(c(f" {texto}", "titulo"))
    saida(c(LINHA_GROSSA * LARGURA, "linha"))


def cabecalho(texto: str, saida: Saida = print) -> None:
    """Cabeçalho de um item (pasta, nome, aluno)."""
    saida("")
    saida(c(LINHA_FINA * LARGURA, "linha"))
    saida(c(f" {texto}", "titulo"))
    saida(c(LINHA_FINA * LARGURA, "linha"))


def secao(texto: str, saida: Saida = print) -> None:
    """Separador de seção: "── Texto ──────"."""
    saida("")
    inicio = f"{LINHA_FINA * 2} {texto} "
    saida(c(inicio, "titulo") + c(LINHA_FINA * max(3, LARGURA - len(inicio)), "linha"))


def status(papel: str, texto: str, saida: Saida = print, recuo: int = 2) -> None:
    """Linha com símbolo e cor do papel: ok, aviso, erro, bloqueado, info, fraco."""
    simbolo = SIMBOLOS.get(papel, SIMBOLOS["info"])
    saida(" " * recuo + c(f"{simbolo} {texto}", papel))


def ok(texto: str, saida: Saida = print) -> None:
    status("ok", texto, saida)


def aviso(texto: str, saida: Saida = print) -> None:
    status("aviso", texto, saida)


def erro(texto: str, saida: Saida = print) -> None:
    status("erro", texto, saida)


def info(texto: str, saida: Saida = print) -> None:
    status("info", texto, saida)


def bloqueado(texto: str, saida: Saida = print) -> None:
    for linha in texto.splitlines():
        status("bloqueado", linha, saida)


def texto(linhas: str, saida: Saida = print, recuo: int = 2) -> None:
    """Parágrafo simples, quebrado na largura da tela."""
    for linha in textwrap.wrap(linhas, width=LARGURA - recuo):
        saida(" " * recuo + linha)


def comando(texto_cmd: str, explicacao: str = "", saida: Saida = print) -> None:
    """Dica de comando: "→ python main.py --revisar  (explicação)"."""
    extra = c(f"  ({explicacao})", "fraco") if explicacao else ""
    saida(f"  {c(SIMBOLOS['seta'], 'info')} {c(texto_cmd, 'tecla')}{extra}")


def contagens(pares: Iterable[tuple[str, int, str]], saida: Saida = print) -> None:
    """Rótulo: número, alinhados. Papel do número: ok/aviso/erro; zero fica fraco."""
    pares = list(pares)
    largura = max((len(r) for r, _, _ in pares), default=0)
    for rotulo, valor, papel in pares:
        saida(f"  {rotulo + ':':<{largura + 1}} {c(str(valor), papel if valor else 'fraco')}")


def menu(opcoes: list[tuple[str, str]], saida: Saida = print) -> None:
    """Menu "O que fazer?", uma tecla por linha."""
    saida("")
    saida(c("  O que fazer?", "titulo"))
    for tecla, descricao in opcoes:
        saida(f"    {c(f'{tecla:<8}', 'tecla')} = {descricao}")


def perguntar(prompt: str, entrada: Callable[[str], str] | None = None) -> str:
    """input() que nunca trava: sem terminal ou Ctrl+C -> "" (cancela)."""
    try:
        return (entrada or input)(prompt).strip()
    except (EOFError, OSError, KeyboardInterrupt):
        return ""


def caminho(p) -> str:
    """Caminho curto: relativo à pasta atual quando estiver dentro dela."""
    from pathlib import Path
    try:
        return str(Path(p).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


# ─── Barras de semelhança ────────────────────────────────────

def papel_score(score: float) -> str:
    return "ok" if score >= VERDE_A_PARTIR else "aviso" if score >= AMARELO_A_PARTIR else "fraco"


def barra(score: float) -> str:
    cheio = round(max(0.0, min(score, 100.0)) / 100 * BARRA_TAMANHO)
    return c(BARRA_CHEIA * cheio, papel_score(score)) + c(BARRA_VAZIA * (BARRA_TAMANHO - cheio), "fraco")


def porcentagem(score: float) -> str:
    return c(f"{score:3.0f}%", papel_score(score))


# ─── Log no terminal ─────────────────────────────────────────

class FormatoTerminal(logging.Formatter):
    """Linhas de log no terminal: "  18:27:41 • mensagem" (cor pelo nível).
    O arquivo de log continua com o formato completo (data, nível)."""

    _PAPEL = {logging.WARNING: "aviso", logging.ERROR: "erro", logging.CRITICAL: "erro"}

    def format(self, registro: logging.LogRecord) -> str:
        papel = self._PAPEL.get(registro.levelno, "info")
        hora = c(self.formatTime(registro, "%H:%M:%S"), "fraco")
        mensagem = registro.getMessage()
        if registro.exc_info:
            mensagem += "\n" + self.formatException(registro.exc_info)
        return f"  {hora} {c(SIMBOLOS[papel], papel)} {c(mensagem, papel) if papel != 'info' else mensagem}"
