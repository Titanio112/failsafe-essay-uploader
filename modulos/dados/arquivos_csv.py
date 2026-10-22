"""Leitura e escrita dos CSV que o Antônio edita à mão (T43).

O Excel no Windows salva "CSV" em cp1252 (sem UTF-8) e o Bloco de Notas
pode deixar a última linha sem quebra. Aqui fica o tratamento dos dois casos
para a lista de alunos e os arquivos de aprovação.
"""

from __future__ import annotations

import io
from pathlib import Path


def ler_texto(caminho: Path) -> str:
    """Conteúdo do arquivo: UTF-8 (com ou sem BOM); se não for, cp1252 (Excel)."""
    dados = Path(caminho).read_bytes()
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("cp1252", errors="replace")


def abrir_csv(caminho: Path) -> io.StringIO:
    """Como ``open(..., newline="")``, mas aceita o CSV salvo pelo Excel."""
    return io.StringIO(ler_texto(caminho), newline="")


def garantir_quebra_final(caminho: Path) -> None:
    """Antes de acrescentar linhas: se o arquivo não termina em quebra de
    linha, põe uma (senão a 1ª linha nova gruda na última)."""
    caminho = Path(caminho)
    if not caminho.is_file() or caminho.stat().st_size == 0:
        return
    with open(caminho, "rb") as f:
        f.seek(-1, 2)
        ultimo = f.read(1)
    if ultimo not in (b"\n", b"\r"):
        with open(caminho, "ab") as f:
            f.write(b"\r\n")
