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
    "fraco": "·", "seta": "→", "pasta": "📁", "progresso": "▶",
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
    """Caminho curto: relativo à pasta atual quando estiver dentro dela.
    T53: num terminal de verdade é link (Ctrl+clique abre o relatório/pasta)."""
    from pathlib import Path
    try:
        texto = str(Path(p).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        texto = str(p)
    return link(texto, p, pasta=Path(p).is_dir())


# ─── Link clicável para arquivo (T51) ────────────────────────
# Windows Terminal e outros terminais modernos: Ctrl+clique abre o arquivo.
# Sem terminal de verdade (teste, arquivo) sai só o texto.

def _no_vscode() -> bool:
    return os.environ.get("TERM_PROGRAM", "").lower() == "vscode"


def uri_de(alvo, pasta: bool = False) -> str:
    """Endereço do link para ``alvo`` ("" = sem link).

    T52: o Windows lê "%C3%A7" (ç em UTF-8) como dois caracteres, então
    file:///.../Reda%C3%A7%C3%B5es nunca abria. No terminal do VS Code o link
    é vscode://file/... (o próprio VS Code abre a foto, sem passar pelo
    Windows); pasta ali não vira link (abriria uma janela nova do VS Code).
    Nos outros terminais: file:/// com as letras acentuadas sem codificar.
    """
    from pathlib import Path
    from urllib.parse import quote
    try:
        caminho = Path(alvo).resolve()
        caminho.as_uri()  # caminho relativo/estranho -> ValueError
    except ValueError:
        return ""
    posix = caminho.as_posix()
    if _no_vscode():
        return "" if pasta else "vscode://file/" + quote(posix, safe="/:")
    # quote codifica espaço, %, #, ?; as letras acentuadas voltam como estão
    return "file:///" + "".join(ch if ord(ch) > 127 else quote(ch, safe="/:") for ch in posix)


def link(texto: str, alvo, pasta: bool = False) -> str:
    """``texto`` vira um link para o arquivo/pasta ``alvo`` (Ctrl+clique)."""
    if not _cores["ativas"]:
        return texto
    uri = uri_de(alvo, pasta)
    if not uri:
        return texto
    return f"\033]8;;{uri}\033\\{texto}\033]8;;\033\\"


def link_arquivo(pasta_raiz, pasta: str, arquivo: str) -> str:
    """"pasta/arquivo" com o arquivo clicável (abre a foto) e a pasta
    clicável (abre a pasta no Explorador)."""
    from pathlib import Path
    raiz = Path(pasta_raiz)
    return f"{link(pasta, raiz / pasta, pasta=True)}/{link(arquivo, raiz / pasta / arquivo)}"


def abrir(alvo) -> str:
    """T52: abre a foto/pasta no programa padrão do Windows (sem depender do
    terminal). Retorna "" se abriu ou o motivo de não ter aberto."""
    from pathlib import Path
    caminho = Path(alvo)
    if not caminho.exists():
        return "não encontrado"
    try:
        if hasattr(os, "startfile"):
            os.startfile(str(caminho))  # type: ignore[attr-defined]
        else:  # fora do Windows
            import subprocess
            subprocess.Popen(["xdg-open" if sys.platform != "darwin" else "open", str(caminho)])
    except OSError as e:
        return f"{type(e).__name__}: {e}"
    return ""


# ─── Progresso do envio (T51) ────────────────────────────────

def tempo(segundos: float) -> str:
    """90 -> "1 min 30 s"; 3700 -> "1 h 2 min"."""
    segundos = int(max(segundos, 0))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h} h {m} min"
    if m:
        return f"{m} min {s:02d} s" if m < 10 else f"{m} min"
    return f"{s} s"


def linha_progresso(feitas: int, total: int, passou: float, unidade: str = "redações") -> str:
    """"▶ 23 de 61 redações  █████░░░░░  38%  ·  passou 12 min  ·  faltam ~19 min"."""
    total = max(total, 1)
    porcento = feitas / total * 100
    cheio = round(porcento / 100 * BARRA_TAMANHO)
    barra_txt = c(BARRA_CHEIA * cheio, "ok") + c(BARRA_VAZIA * (BARRA_TAMANHO - cheio), "fraco")
    restante = f"faltam ~{tempo(passou / feitas * (total - feitas))}" if feitas else "calculando o tempo..."
    if feitas >= total:
        restante = "terminado"
    return (f"  {c(SIMBOLOS['progresso'], 'info')} {feitas} de {total} {unidade}  {barra_txt}  "
            f"{porcento:3.0f}%  {c('·', 'fraco')}  passou {tempo(passou)}  {c('·', 'fraco')}  {restante}")


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
