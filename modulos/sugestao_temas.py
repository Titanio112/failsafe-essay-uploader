"""Sugere o código do tema para pastas sem código (T26). Só sugere.

As pastas reais vêm como "3B - <título>"; "3B" não é código (regra), então
nada seria enviado. Aqui o título é comparado com ``dados/temas_site.csv``
(colunas codigo,texto) e o dry-run mostra o tema mais parecido para o
Antônio renomear a pasta para "<código> - <título>". Nunca renomeia nada.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from rapidfuzz import fuzz

from modulos.normalizacao import extrair_codigo_tema, normalizar_nome

SCORE_MINIMO = 60.0   # abaixo disso: nenhum tema parecido
SCORE_PROVAVEL = 85.0  # a partir disso: provável; entre os dois: fraco, conferir
_PREFIXO_TURMA = re.compile(r"^\s*\w{1,3}\s*-\s*")


def ler_temas_site(caminho: Path) -> list[tuple[str, str]]:
    """[(codigo, texto)] do CSV; vazio se não existir."""
    if not Path(caminho).is_file():
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return [(l["codigo"], l.get("texto", "")) for l in csv.DictReader(f) if l.get("codigo")]


def _titulo(texto: str) -> str:
    """Tira "3B - " / "100- " do começo e normaliza."""
    return normalizar_nome(_PREFIXO_TURMA.sub("", texto, count=1))


def sugerir_codigos(pastas: list[str], temas: list[tuple[str, str]]) -> list[tuple[str, str, str, float]]:
    """Para cada pasta SEM código: (pasta, codigo, texto_do_tema, score).
    Score abaixo de SCORE_MINIMO -> codigo vazio (nenhum tema parecido)."""
    sugestoes = []
    for pasta in sorted(pastas):
        if extrair_codigo_tema("", pasta):
            continue
        titulo = _titulo(pasta)
        melhor = max(((fuzz.token_set_ratio(titulo, _titulo(texto)), codigo, texto)
                      for codigo, texto in temas), default=(0.0, "", ""))
        score, codigo, texto = melhor
        if score < SCORE_MINIMO:
            codigo, texto = "", ""
        sugestoes.append((pasta, codigo, texto, round(score, 1)))
    return sugestoes


# ─── Pastas aprovadas (T28) ──────────────────────────────────
# dados/pastas_aprovadas.csv (;): pasta;codigo;tema;aprovado;semelhanca
# O dry-run acrescenta sugestões com "aprovado" vazio; o Antônio confere
# (pode trocar o código à mão) e escreve "sim". Sem renomear pastas.

COLUNAS_PASTAS = ["pasta", "codigo", "tema", "aprovado", "semelhanca"]
_RESPOSTAS_SIM = {"sim", "s", "x", "ok", "yes"}


def _ler_pastas(caminho: Path) -> list[dict]:
    if not Path(caminho).is_file():
        return []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in linha.items() if k}
                for linha in csv.DictReader(f, delimiter=";")]


def carregar_codigos_pasta(caminho: Path) -> dict[str, str]:
    """{pasta: codigo} das linhas com aprovado=sim e código preenchido."""
    return {
        linha["pasta"]: linha["codigo"]
        for linha in _ler_pastas(caminho)
        if linha.get("aprovado", "").lower() in _RESPOSTAS_SIM and linha.get("pasta") and linha.get("codigo")
    }


def registrar_sugestoes_pasta(sugestoes: list[tuple[str, str, str, float]], caminho: Path) -> int:
    """Acrescenta as pastas ainda não listadas (mesmo sem tema parecido: o
    código pode ser digitado à mão). Nunca altera linhas existentes."""
    caminho = Path(caminho)
    ja_tem = {linha.get("pasta", "") for linha in _ler_pastas(caminho)}
    novas = [
        {"pasta": pasta, "codigo": codigo, "tema": texto, "aprovado": "",
         "semelhanca": f"{score:.0f}%" if codigo else "nenhum tema parecido"}
        for pasta, codigo, texto, score in sugestoes if pasta not in ja_tem
    ]
    if novas:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        novo = not caminho.is_file()
        with open(caminho, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS_PASTAS, delimiter=";")
            if novo:
                escritor.writeheader()
            escritor.writerows(novas)
    return len(novas)
