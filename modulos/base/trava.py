"""Um envio por vez (T44).

Duas janelas rodando --envio-real ao mesmo tempo leriam a mesma contagem do
dia antes de qualquer clique e mandariam a mesma redação duas vezes. A trava
é um arquivo travado pelo sistema operacional: se o programa cair, o
Windows solta a trava sozinho (não fica "trava velha" para apagar à mão).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


class TravaOcupada(RuntimeError):
    """Outro envio está rodando."""


@contextmanager
def trava_de_envio(caminho: Path):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    arquivo = open(caminho, "a+b")
    try:
        try:
            if os.name == "nt":
                import msvcrt
                arquivo.seek(0)
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            raise TravaOcupada(str(caminho)) from e
        try:
            yield
        finally:
            if os.name == "nt":
                import msvcrt
                arquivo.seek(0)
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        arquivo.close()
