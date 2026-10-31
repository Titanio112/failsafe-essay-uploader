"""Turma sem redações (issue #51): avisa e, se a pessoa quiser, mostra onde colocá-las.

Só olha a pasta ``temas/`` da turma; não cria, move nem envia nada. Quem chama decide
quando perguntar (só com pessoa no teclado).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from modulos.base import tela
from modulos.base.config import PASTA_REDACOES
from modulos.base.turma import PASTA_GUIA, pasta_da_turma
from modulos.ferramentas.pastas_enviadas import eh_pasta_enviada

Entrada = Callable[[str], str] | None
EXTENSOES = (".jpg", ".jpeg")


def contar_redacoes(escola: str, turma: str) -> int:
    """Fotos JPG nas pastas de tema da turma (a pasta-guia e as ``ENVIADA - ...`` não contam)."""
    temas = pasta_da_turma(escola, turma) / "temas"
    if not temas.is_dir():
        return 0
    total = 0
    for pasta in temas.iterdir():
        if not pasta.is_dir() or pasta.name.startswith(".") or pasta.name == PASTA_GUIA \
                or eh_pasta_enviada(pasta.name):
            continue
        total += sum(1 for f in pasta.iterdir() if f.is_file() and f.suffix.lower() in EXTENSOES)
    return total


def arvore(escola: str, turma: str) -> list[str]:
    """Desenho da estrutura de pastas, no estilo Markdown (├── e └──)."""
    return [
        f"{PASTA_REDACOES}/",
        f"└── {escola}/",
        f"    └── {turma}/",
        "        ├── alunos.csv",
        "        └── temas/",
        "            └── 100 - Nome do tema/        (código do tema, hífen e o nome)",
        "                ├── Ana Souza.jpg           (uma foto por aluno, com o nome dele)",
        "                └── Bruno Lima.jpg",
    ]


def _pergunta(entrada: Entrada, texto: str) -> str:
    return tela.perguntar(f"  {texto} ", entrada).lower()


def avisar_se_sem_redacoes(escola: str, turma: str, entrada: Entrada = None, saida: Callable = print) -> int:
    """Retorna quantas fotos há na turma ao sair (0 = segue para o menu sem redações)."""
    n = contar_redacoes(escola, turma)
    if n:
        return n
    tela.aviso("Não encontrei redações na pasta desta turma.", saida)
    while True:
        r = _pergunta(entrada, "Quer ver uma explicação rápida de onde colocá-las (e) ou continuar para o menu "
                               "mesmo sem redações (c)? [e/c]:")
        if r in ("c", ""):
            return 0
        if r == "e":
            break
        tela.erro("Digite e ou c.", saida)
    temas = pasta_da_turma(escola, turma) / "temas"
    tela.secao("Onde colocar as redações", saida)
    for linha in arvore(escola, turma):
        saida(f"    {linha}")
    saida("")
    tela.info(f"Pasta dos temas desta turma (Ctrl+clique abre): {tela.caminho(temas)}", saida)
    tela.status("fraco", "Dentro de temas/ já existe uma pasta-guia: renomeie para \"<código> - <tema>\" e solte as fotos.",
                saida, recuo=4)
    while True:
        r = _pergunta(entrada, "Você já colocou as redações lá? (s/n):")
        if r in ("n", "nao", "não", ""):
            tela.info("Tudo bem. Quando colocar, use \"Conferir as redações\" no menu.", saida)
            return 0
        if r not in ("s", "sim"):
            tela.erro("Responda s ou n.", saida)
            continue
        n = contar_redacoes(escola, turma)
        if n:
            tela.ok(f"Encontrei {n} foto(s). Vamos em frente.", saida)
            return n
        tela.aviso("Ainda não encontrei.", saida)
        r = _pergunta(entrada, "Tentar de novo (t) ou continuar para o menu sem redações (c)? [t/c]:")
        if r != "t":
            return 0
