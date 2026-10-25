"""Funções de normalização e extração de códigos."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Set


_PONTUACAO_RE = re.compile(r"[^\w\s]", re.UNICODE)
_ESPACOS_RE = re.compile(r"\s+")

# Regex para código do tema no ARQUIVO (pasta): número seguido de
# separador (espaço, _, ., -) ou fim
# Ex.: "000 Simulado", "001_Carta", "002.Red", "003-Narração", "004" -> código "000", "001", "002", "003", "004"
# "3B ..." NÃO é código (não tem separador após o número)
PADRAO_CODIGO_ARQUIVO = re.compile(r"^\s*(\d+)(?=[\s_.-]|$)")

# Regex para código do tema no COMBO DO SITE: número seguido de " - " ou espaço ou fim
# Ex.: "0- Narração", "00- Carta", "000- DISSERTATIVO" -> "0", "00", "000"
PADRAO_CODIGO_TEMA_SITE = re.compile(r"^\s*(\d+)(?=\s*-|\s|$)")


def normalizar_nome(texto: str) -> str:
    """Normaliza nome para comparação: remove acentos, pontuação, casefold, espaços."""
    if not texto:
        return ""
    decomposto = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    minusculo = sem_acento.casefold()
    sem_pontuacao = _PONTUACAO_RE.sub(" ", minusculo)
    sem_apostrofo = sem_pontuacao.replace("'", " ").replace("'", " ")
    return _ESPACOS_RE.sub(" ", sem_apostrofo).strip()


_NUMERO_FINAL_RE = re.compile(r"(\s+\d+)+$")


def sem_numero_final(norm: str) -> str:
    """T43: "ana souza 2" / "ana souza (2)" -> "ana souza": página 2 ou cópia
    do Windows identificam o mesmo aluno (e viram duplicata na pasta)."""
    return _NUMERO_FINAL_RE.sub("", norm) or norm


def extrair_pessoa(nome_arquivo: str) -> str:
    """Extrai a parte do nome da pessoa do arquivo (remove código prefixo e ' - Red')."""
    stem = Path(nome_arquivo).stem
    codigo_match = PADRAO_CODIGO_ARQUIVO.match(stem)
    if codigo_match:
        pos_fim_codigo = codigo_match.end()
        resto = stem[pos_fim_codigo:].lstrip(" _.-")
    else:
        # SEM separador (espaço, _, ., -) ou fim → NÃO é código, o stem inteiro é a pessoa
        resto = stem
    pessoa, sep, depois = resto.partition(MARCADOR_PESSOA)
    # Bug 011: "Ana Souza - Red 2" / "- Redação (2)" / "- Red - Copia" é
    # página 2 ou cópia, como "Ana Souza 2": o número volta para o fim do
    # nome e a conciliação manda para REVISAO_MANUAL (T43/T48).
    if sep:
        numero = re.search(r"\d+", depois)
        if numero or re.search(r"c[oó]pia", depois, re.IGNORECASE):
            pessoa = f"{pessoa} {numero.group(0) if numero else 2}"
    # T43: "Ana_Souza" (celular/WhatsApp) -> "Ana Souza"; normalizar_nome mantém o "_"
    return pessoa.replace("_", " ").strip()


def extrair_codigo_do_arquivo(nome_arquivo: str) -> str | None:
    """Extrai o código do tema do nome do arquivo/pasta."""
    stem = Path(nome_arquivo).stem
    match = PADRAO_CODIGO_ARQUIVO.match(stem)
    return match.group(1) if match else None


def extrair_codigo_do_tema_site(texto_combo: str) -> str | None:
    """Extrai o código do tema do texto do combo do site."""
    if not texto_combo:
        return None
    match = PADRAO_CODIGO_TEMA_SITE.match(texto_combo)
    return match.group(1) if match else None


def extrair_codigo_tema(nome_arquivo: str, pasta: str = "") -> str | None:
    """Extrai código do tema do arquivo. Se houver conflito arquivo vs pasta, retorna None para sinalizar REVISAO_MANUAL."""
    stem = Path(nome_arquivo).stem
    match_arquivo = PADRAO_CODIGO_ARQUIVO.match(stem)
    codigo_arquivo = match_arquivo.group(1) if match_arquivo else None

    codigo_pasta = None
    if pasta:
        match_pasta = PADRAO_CODIGO_ARQUIVO.match(pasta)
        if match_pasta:
            codigo_pasta = match_pasta.group(1)

    # Detectar conflito: ambos existem e são diferentes
    conflito_pasta_arquivo = (
        codigo_arquivo is not None and
        codigo_pasta is not None and
        codigo_arquivo != codigo_pasta
    )

    if conflito_pasta_arquivo:
        return None

    # Código efetivo (prioridade: arquivo > pasta)
    return codigo_arquivo or codigo_pasta


MARCADOR_PESSOA = " - Red"


def validar_codigo_site(codigo: str, codigos_site: Set[str]) -> bool:
    """Valida se o código existe no combo do site."""
    return codigo in codigos_site