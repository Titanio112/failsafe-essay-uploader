"""Item da fila de envio (modo teste e produção). A fila em si é montada
por fila_producao.montar_lote_producao (T40)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path



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
    # T44: sha256 do JPG, gravado no banco; o mesmo conteúdo com outro nome
    # não é enviado de novo.
    hash_arquivo: str = ""


def hash_do_arquivo(caminho: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()
