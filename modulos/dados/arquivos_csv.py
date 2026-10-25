"""Leitura e escrita dos CSV que o Antônio edita à mão (T43).

O Excel no Windows salva "CSV" em cp1252 (sem UTF-8) e o Bloco de Notas
pode deixar a última linha sem quebra. Aqui fica o tratamento dos dois casos
para a lista de alunos e os arquivos de aprovação.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path


class CsvIlegivel(ValueError):
    """O cabeçalho do CSV não tem as colunas esperadas (bug 014)."""


def ler_linhas_ponto_e_virgula(caminho: Path, obrigatorias: list[str]) -> list[dict]:
    """Linhas de um CSV de aprovação (``;``), com chaves minúsculas e valores
    sem espaços; arquivo que não existe -> [].

    Bug 014: se o cabeçalho não tem as colunas ``obrigatorias`` (ex.: o Excel
    salvou com vírgula), levanta CsvIlegivel em vez de devolver linhas que
    ninguém aprovou e de deixar uma regravação apagar as aprovações."""
    if not Path(caminho).is_file():
        return []
    leitor = csv.DictReader(abrir_csv(caminho), delimiter=";")
    cabecalho = [(c or "").strip().lower() for c in (leitor.fieldnames or [])]
    if cabecalho and not set(obrigatorias) <= set(cabecalho):
        separador = " (salvo com vírgula? salve como CSV separado por ponto e vírgula)" \
            if "," in "".join(cabecalho) else ""
        raise CsvIlegivel(f"{Path(caminho).name}: cabeçalho sem as colunas {', '.join(obrigatorias)}"
                          f"{separador}")
    return [{k.strip().lower(): (v or "").strip() for k, v in linha.items() if k} for linha in leitor]


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
    """Antes de acrescentar linhas (sempre em UTF-8):
    - T48: arquivo que o Excel salvou em cp1252 é regravado inteiro em UTF-8
      (senão o arquivo fica misturado e os acentos viram "Ã§");
    - se o arquivo não termina em quebra de linha, põe uma (senão a 1ª
      linha nova gruda na última)."""
    caminho = Path(caminho)
    if not caminho.is_file() or caminho.stat().st_size == 0:
        return
    dados = caminho.read_bytes()
    try:
        dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        caminho.write_bytes(dados.decode("cp1252", errors="replace").encode("utf-8-sig"))
    with open(caminho, "rb") as f:
        f.seek(-1, 2)
        ultimo = f.read(1)
    if ultimo not in (b"\n", b"\r"):
        with open(caminho, "ab") as f:
            f.write(b"\r\n")
