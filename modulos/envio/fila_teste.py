"""Monta a fila de envio do modo teste (sem navegador)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modulos.dados.normalizacao import extrair_codigo_tema


@dataclass
class ItemFilaTeste:
    """Um arquivo liberado para tentar envio (modo teste ou produção)."""
    pasta: str
    arquivo: str
    codigo: str
    caminho: Path
    # Chave no banco de progresso; vazia = nome do arquivo (modo teste).
    # Produção usa "pasta/arquivo", a mesma chave do dry-run.
    chave_progresso: str = ""
    # T35: quantos arquivos o aluno tem neste código (todas as pastas).
    # Se o site já tem esse tanto hoje, tudo já foi enviado.
    total_mesmo_tema: int = 1


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
