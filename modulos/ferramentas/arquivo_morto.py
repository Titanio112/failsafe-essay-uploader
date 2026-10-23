"""Arquivo morto (T57): `python main.py --arquivar` (menu 11).

Tira da pasta das redações as pastas de tema que já foram enviadas (por
exemplo as antigas, mandadas à mão) e guarda em ``Arquivo morto/<data_hora>/``
na raiz do projeto, com a mesma estrutura. Nada é apagado: para trazer de
volta, é só mover a pasta de novo. Cada movimento fica em
relatorios/arquivamento_<data>.csv. Não roda durante um envio (mesma trava).
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Callable

from modulos.base import relogio, tela

PASTA_ARQUIVO = "Arquivo morto"
Entrada = Callable[[str], str]


def pastas_de_tema(pasta_raiz: Path) -> list[tuple[Path, int]]:
    """[(pasta, nº de fotos)] das subpastas (o LEIA-ME da raiz fica)."""
    raiz = Path(pasta_raiz)
    if not raiz.is_dir():
        return []
    return [(p, sum(1 for f in p.rglob("*") if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg")))
            for p in sorted(raiz.iterdir()) if p.is_dir() and not p.name.startswith(".")]


def _escolher(pastas: list[tuple[Path, int]], entrada: Entrada | None, saida: Callable) -> list[Path] | None:
    for i, (pasta, fotos) in enumerate(pastas, 1):
        saida(f"    {tela.c(f'{i})', 'tecla')} {tela.link(pasta.name, pasta, pasta=True)}  "
              f"{tela.c(f'({fotos} foto(s))', 'fraco')}")
    resposta = tela.perguntar("  Quais arquivar? (t = todas, números com vírgula, Enter = nenhuma): ",
                              entrada).lower()
    if not resposta:
        return []
    if resposta in ("t", "todas"):
        return [p for p, _ in pastas]
    try:
        numeros = sorted({int(x) for x in resposta.replace(" ", "").split(",") if x})
    except ValueError:
        return None
    if not numeros or any(n < 1 or n > len(pastas) for n in numeros):
        return None
    return [pastas[n - 1][0] for n in numeros]


def executar_arquivar(pasta_raiz: Path, raiz_projeto: Path, pasta_relatorios: Path,
                      entrada: Entrada | None = None, saida: Callable = print) -> int:
    """0 = arquivou (ou nada a fazer); 2 = cancelado/erro."""
    from modulos.base.trava import TravaOcupada, trava_de_envio
    tela.titulo("ARQUIVO MORTO  ·  nada é apagado", saida)
    pastas = pastas_de_tema(pasta_raiz)
    if not pastas:
        tela.info(f"Nenhuma pasta de tema em {tela.caminho(pasta_raiz)}.", saida)
        return 0
    tela.texto("Pastas de tema que podem ir para o arquivo morto. Arquive só o que já foi enviado "
               "(no site ou pelo script); o que for para lá o script não vê mais.", saida)
    escolhidas = _escolher(pastas, entrada, saida)
    if escolhidas is None:
        tela.erro("Resposta inválida: nada foi movido.", saida)
        return 2
    if not escolhidas:
        tela.info("Nada foi movido.", saida)
        return 0
    destino = Path(raiz_projeto) / PASTA_ARQUIVO / f"{relogio.agora():%Y-%m-%d_%H%M%S}"
    tela.status("fraco", f"Destino: {destino}", saida)
    if tela.perguntar(f"  Mover {len(escolhidas)} pasta(s)? (s/n): ", entrada).lower() not in ("s", "sim"):
        tela.info("Nada foi movido.", saida)
        return 0
    log_csv = Path(pasta_relatorios) / f"arquivamento_{relogio.agora():%Y%m%d_%H%M%S}.csv"
    movidas = 0
    try:
        with trava_de_envio(Path(pasta_relatorios) / "envio.trava"):
            destino.mkdir(parents=True, exist_ok=True)
            log_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
                escritor = csv.writer(f, delimiter=";")
                escritor.writerow(["origem", "destino"])
                for pasta in escolhidas:
                    alvo = destino / pasta.name
                    try:
                        shutil.move(str(pasta), str(alvo))
                    except OSError as e:
                        tela.erro(f"Não movi {pasta.name} ({type(e).__name__}): arquivo aberto?", saida)
                        continue
                    escritor.writerow([str(pasta), str(alvo)])
                    f.flush()
                    movidas += 1
                    tela.ok(f"Arquivada: {pasta.name}", saida)
    except TravaOcupada:
        tela.erro("Um envio está rodando agora (outra janela?). Espere ele acabar. Nada foi movido.", saida)
        return 2
    tela.secao("Fim", saida)
    tela.status("ok", f"{movidas} de {len(escolhidas)} pasta(s) no arquivo morto: {tela.caminho(destino)}", saida)
    tela.status("fraco", "Para trazer de volta, mova a pasta de novo para a pasta das redações.", saida)
    tela.status("fraco", "Dica: nas redações novas use nomes de pasta novos (o caderno lembra pasta/arquivo).",
                saida)
    return 0 if movidas == len(escolhidas) else 2
