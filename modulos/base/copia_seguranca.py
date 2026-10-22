"""Cópia de segurança do caderno de envios (T47).

O banco ``relatorios/progresso.db`` é o caderno: diz o que já foi enviado.
Sem ele a checagem do dia (site x caderno) dá ERRO em tudo e a trava de
"mesma foto" some. Antes de cada envio o script guarda uma cópia em
``relatorios/copias/`` e mantém só as mais recentes.

Para voltar uma cópia: feche o script, apague (ou renomeie) o
``relatorios/progresso.db`` e copie a cópia escolhida para esse nome.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from modulos.base import relogio

MANTER = 30  # cópias mais recentes; as mais antigas são apagadas
PREFIXO = "progresso_"


def copiar_caderno(con: sqlite3.Connection, pasta: Path, manter: int = MANTER) -> Path:
    """Copia o banco aberto (API de backup do SQLite: segura com o banco em
    uso) para ``pasta/progresso_AAAAMMDD_HHMMSS_micro.db``. Retorna o caminho."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    # Microssegundos no nome: a ordem alfabética é a ordem de criação
    # (a limpeza abaixo apaga as primeiras da lista).
    destino = pasta / f"{PREFIXO}{relogio.agora():%Y%m%d_%H%M%S_%f}.db"
    copia = sqlite3.connect(destino)
    try:
        con.backup(copia)
    finally:
        copia.close()
    for antiga in sorted(pasta.glob(f"{PREFIXO}*.db"))[:-max(manter, 1)]:
        antiga.unlink(missing_ok=True)
    return destino
