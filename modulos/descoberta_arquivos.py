"""Descoberta de arquivos JPG nas pastas de temas."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Set

from modulos.config import Config
from modulos.normalizacao import extrair_codigo_tema


# Extensões permitidas (apenas .jpg, case-insensitive)
EXTENSOES_PERMITIDAS: Set[str] = {".jpg"}


def _emitir_aviso(mensagem: str) -> None:
    aviso = f"[AVISO] {mensagem}"
    print(aviso)
    warnings.warn(aviso, UserWarning, stacklevel=3)


def descobrir_arquivos(config: Config) -> Dict[str, List[str]]:
    """Descobre arquivos JPG nas pastas de temas.

    Retorna dict: {nome_pasta: [arquivo1.jpg, arquivo2.jpg, ...]}
    Pastas sem JPG válidos não entram no dict.
    """
    raiz = config.pasta_raiz
    if not raiz.exists():
        return {}

    resultado: Dict[str, List[str]] = {}

    for pasta in sorted(raiz.iterdir()):
        if not pasta.is_dir():
            continue

        arquivos: List[str] = []
        for f in sorted(pasta.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in EXTENSOES_PERMITIDAS:
                _emitir_aviso(f"Arquivo ignorado (extensão não permitida): {pasta.name}/{f.name} (ext: {ext})")
                continue
            arquivos.append(f.name)

        if arquivos:
            resultado[pasta.name] = arquivos

    return resultado