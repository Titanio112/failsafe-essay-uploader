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

from modulos.dados.arquivos_csv import CsvIlegivel, abrir_csv, garantir_quebra_final, ler_linhas_ponto_e_virgula
from modulos.dados.normalizacao import extrair_codigo_do_tema_site, extrair_codigo_tema, normalizar_nome

SCORE_MINIMO = 60.0   # abaixo disso: nenhum tema parecido
SCORE_PROVAVEL = 85.0  # a partir disso: provável; entre os dois: fraco, conferir
# Bug 029: turma em qualquer forma ("3B - ", "3-B - ", "3 B - ", "3_B ",
# "2º ano - ") ou código ("100- ") antes do título
_PREFIXO_TURMA = re.compile(r"^\s*(?:\d{1,2}\s*[-_ ]?\s*[A-Za-z](?![A-Za-zÀ-ÿ])|\d{1,2}\s*[ºª°]\s*ano|\w{1,3})"
                            r"\s*[-_ ]\s*", re.IGNORECASE)


def ler_temas_site(caminho: Path) -> list[tuple[str, str]]:
    """[(codigo, texto)] do CSV; vazio se não existir."""
    if not Path(caminho).is_file():
        return []
    return [(l["codigo"], l.get("texto", "")) for l in csv.DictReader(abrir_csv(caminho)) if l.get("codigo")]


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
    return ler_linhas_ponto_e_virgula(caminho, ["pasta", "codigo", "aprovado"])


def carregar_codigos_pasta(caminho: Path) -> dict[str, str]:
    """{pasta: codigo} das linhas com aprovado=sim e código preenchido.

    T43: se a coluna ``tema`` começa por outro código, a linha é ignorada
    (o Excel transforma "000" em "0", e "0" também é um tema do site).
    Bug 010: com a coluna ``tema`` vazia não há como conferir; a linha
    também é ignorada (com aviso)."""
    from modulos.base import tela
    try:
        linhas = _ler_pastas(caminho)
    except CsvIlegivel as e:
        tela.aviso(f"pastas_aprovadas: {e}; nenhuma pasta aprovada foi lida.")
        return {}
    codigos = {}
    for linha in linhas:
        pasta, codigo = linha.get("pasta"), linha.get("codigo")
        if linha.get("aprovado", "").lower() not in _RESPOSTAS_SIM or not pasta or not codigo:
            continue
        do_tema = extrair_codigo_do_tema_site(linha.get("tema", ""))
        if not do_tema:
            tela.aviso(f"pastas_aprovadas: '{pasta}' tem codigo {codigo} sem o tema escrito; ignorada. "
                       "Preencha a coluna tema como no site (ex.: 000- DISSERTATIVO ARGUMENTATIVO) "
                       "ou aprove em \"Revisar temas e nomes\".")
            continue
        if do_tema != codigo:
            tela.aviso(f"pastas_aprovadas: '{pasta}' tem codigo {codigo} mas o tema e {do_tema} "
                       "(o Excel tira os zeros?); ignorada. Corrija o codigo ou o tema.")
            continue
        codigos[pasta] = codigo
    return codigos


def aprovar_pasta(caminho: Path, pasta: str, codigo: str, tema: str) -> None:
    """Grava pasta -> código com aprovado=sim (T29, revisão interativa).
    Atualiza a linha da pasta se já existir; as outras ficam como estão.
    Bug 014: arquivo com cabeçalho estranho -> CsvIlegivel, sem regravar
    (regravar trocaria as aprovações antigas por linhas vazias)."""
    caminho = Path(caminho)
    linhas = _ler_pastas(caminho)
    nova = {"pasta": pasta, "codigo": codigo, "tema": tema, "aprovado": "sim", "semelhanca": "revisao interativa"}
    for i, linha in enumerate(linhas):
        if linha.get("pasta") == pasta:
            linhas[i] = nova
            break
    else:
        linhas.append(nova)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_PASTAS, delimiter=";", extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows({c: l.get(c, "") for c in COLUNAS_PASTAS} for l in linhas)


def registrar_sugestoes_pasta(sugestoes: list[tuple[str, str, str, float]], caminho: Path) -> int:
    """Acrescenta as pastas ainda não listadas (mesmo sem tema parecido: o
    código pode ser digitado à mão). Nunca altera linhas existentes."""
    caminho = Path(caminho)
    try:
        ja_tem = {linha.get("pasta", "") for linha in _ler_pastas(caminho)}
    except CsvIlegivel as e:
        from modulos.base import tela
        tela.aviso(f"pastas_aprovadas: {e}; sugestoes novas nao gravadas (o arquivo ficou como esta).")
        return 0
    novas = [
        {"pasta": pasta, "codigo": codigo, "tema": texto, "aprovado": "",
         "semelhanca": f"{score:.0f}%" if codigo else "nenhum tema parecido"}
        for pasta, codigo, texto, score in sugestoes if pasta not in ja_tem
    ]
    if novas:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        novo = not caminho.is_file()
        garantir_quebra_final(caminho)
        with open(caminho, "a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS_PASTAS, delimiter=";")
            if novo:
                escritor.writeheader()
            escritor.writerows(novas)
    return len(novas)
