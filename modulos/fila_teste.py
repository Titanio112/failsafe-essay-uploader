"""Monta a fila de envio do modo teste (sem navegador)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modulos.normalizacao import extrair_codigo_tema


@dataclass
class ItemFilaTeste:
    """Um arquivo de teste liberado para tentar envio."""
    pasta: str
    arquivo: str
    codigo: str
    caminho: Path


def montar_fila_teste(
    pasta_raiz: Path,
    arquivos_por_pasta: dict[str, list[str]],
) -> tuple[list[ItemFilaTeste], list[tuple[str, str]]]:
    """Retorna (fila, ignorados).

    Ordem: pastas e arquivos em ordem alfabética. Um arquivo por código
    (códigos são strings: "0" != "00"); os demais do mesmo código ficam
    fora (revisão manual). Pasta sem código ou arquivo inexistente: fora.
    ignorados = [(pasta/arquivo, motivo)].
    """
    fila: list[ItemFilaTeste] = []
    ignorados: list[tuple[str, str]] = []
    codigos_na_fila: set[str] = set()

    for pasta in sorted(arquivos_por_pasta):
        for arquivo in sorted(arquivos_por_pasta[pasta]):
            rotulo = f"{pasta}/{arquivo}"
            codigo = extrair_codigo_tema(arquivo, pasta)
            caminho = Path(pasta_raiz) / pasta / arquivo
            if not codigo:
                ignorados.append((rotulo, "sem codigo de tema (revisao manual)"))
            elif codigo in codigos_na_fila:
                ignorados.append((rotulo, f"codigo {codigo} repetido (revisao manual)"))
            elif not caminho.is_file():
                ignorados.append((rotulo, "arquivo nao encontrado"))
            else:
                codigos_na_fila.add(codigo)
                fila.append(ItemFilaTeste(pasta, arquivo, codigo, caminho))

    return fila, ignorados
