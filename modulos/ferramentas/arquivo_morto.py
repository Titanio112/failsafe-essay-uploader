"""Arquivo morto (T57): `python main.py --arquivar` (menu 11).

M3: só pastas de tema marcadas "ENVIADA - ..." (T60: marcadas depois de
conferir TODAS as fotos no site) saem da pasta ``temas/`` da turma e vão
para ``Arquivo morto/<Escola>/<Turma>/<data_hora>/<pasta>``, na raiz do
projeto. Pasta não marcada nunca vai. alunos.csv, dados/, relatorios/ e o
caderno ficam onde estão. Nada é apagado nem sobrescrito: para trazer de
volta, é só mover a pasta de novo. Cada movimento fica em
relatorios/arquivamento_<data>.csv. Não roda durante um envio (mesma trava).
"""

from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path
from typing import Callable

from modulos.base import relogio, tela
from modulos.ferramentas.pastas_enviadas import PREFIXO, eh_pasta_enviada

PASTA_ARQUIVO = "Arquivo morto"
Entrada = Callable[[str], str]


def pastas_de_tema(pasta_raiz: Path) -> list[tuple[Path, int]]:
    """[(pasta, nº de fotos)] só das pastas de tema marcadas "ENVIADA - " (M3)."""
    raiz = Path(pasta_raiz)
    if not raiz.is_dir():
        return []
    pastas = [p for p in raiz.iterdir() if p.is_dir() and not p.is_symlink() and eh_pasta_enviada(p.name)]
    return [(p, sum(1 for f in p.rglob("*") if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg")))
            for p in sorted(pastas, key=lambda p: p.name)]


def _escolher(pastas: list[tuple[Path, int]], entrada: Entrada | None, saida: Callable) -> list[Path] | None:
    for i, (pasta, fotos) in enumerate(pastas, 1):
        saida(f"    {tela.c(f'{i})', 'tecla')} {tela.link(pasta.name, pasta, pasta=True)}  "
              f"{tela.c(f'({fotos} foto(s))', 'fraco')}{tela.c('  ✔ conferida no site', 'ok')}")
    resposta = tela.perguntar("  Quais arquivar? (e ou t = todas, números com vírgula, Enter = nenhuma): ",
                              entrada).lower()
    if not resposta:
        return []
    if resposta in ("e", "t", "todas"):  # todas aqui já são "ENVIADA - " (M3)
        return [p for p, _ in pastas]
    try:
        numeros = sorted({int(x) for x in resposta.replace(" ", "").split(",") if x})
    except ValueError:
        return None
    if not numeros or any(n < 1 or n > len(pastas) for n in numeros):
        return None
    return [pastas[n - 1][0] for n in numeros]


def _mover(pasta: Path, alvo: Path) -> str:
    """Bug 016: "ok" (movida), "nada" (nada mudou) ou "original incompleta".

    No mesmo disco só renomeia: com uma foto aberta o Windows recusa e nada
    muda (o shutil.move copiava tudo e apagava a origem pela metade). Em
    outro disco copia, confere e só então tira a origem."""
    try:
        os.rename(pasta, alvo)
        return "ok"
    except OSError:
        if os.path.splitdrive(os.path.abspath(pasta))[0].lower() == \
                os.path.splitdrive(os.path.abspath(alvo))[0].lower():
            return "nada"
    try:
        shutil.copytree(pasta, alvo)
    except OSError:
        shutil.rmtree(alvo, ignore_errors=True)  # só a cópia incompleta; a origem fica
        return "nada"
    origem = sorted(p.relative_to(pasta) for p in pasta.rglob("*") if p.is_file())
    copia = sorted(p.relative_to(alvo) for p in alvo.rglob("*") if p.is_file())
    if origem != copia:
        shutil.rmtree(alvo, ignore_errors=True)
        return "nada"
    try:
        shutil.rmtree(pasta)
        return "ok"
    except OSError:
        return "original incompleta"


def executar_arquivar(pasta_raiz: Path, destino_turma: Path, pasta_relatorios: Path,
                      entrada: Entrada | None = None, saida: Callable = print, trava: Path | None = None) -> int:
    """0 = arquivou (ou nada a fazer); 2 = cancelado/erro.
    ``destino_turma``: ``Arquivo morto/<Escola>/<Turma>``; ``trava``: a global do envio."""
    from modulos.base.trava import TravaOcupada, trava_de_envio
    tela.titulo("ARQUIVO MORTO  ·  nada é apagado", saida)
    pastas = pastas_de_tema(pasta_raiz)
    if not pastas:
        tela.info(f"Nenhuma pasta \"{PREFIXO}...\" em {tela.caminho(pasta_raiz)}.", saida)
        tela.status("fraco", "Só vai para o arquivo morto a pasta com TODAS as fotos conferidas no site: "
                    "a conferência (menu 5) oferece marcar essas pastas.", saida)
        return 0
    tela.texto("Pastas com todas as fotos conferidas no site. O que for para o arquivo morto o script não "
               "vê mais; a lista de alunos, os dados e os relatórios da turma ficam.", saida)
    escolhidas = _escolher(pastas, entrada, saida)
    if escolhidas is None:
        tela.erro("Resposta inválida: nada foi movido.", saida)
        return 2
    if not escolhidas:
        tela.info("Nada foi movido.", saida)
        return 0
    destino = Path(destino_turma) / f"{relogio.agora():%Y-%m-%d_%H%M%S}"
    tela.status("fraco", f"Destino: {destino}", saida)
    if tela.perguntar(f"  Mover {len(escolhidas)} pasta(s)? (s/n): ", entrada).lower() not in ("s", "sim"):
        tela.info("Nada foi movido.", saida)
        return 0
    log_csv = Path(pasta_relatorios) / f"arquivamento_{relogio.agora():%Y%m%d_%H%M%S}.csv"
    movidas = 0
    try:
        with trava_de_envio(trava or Path(pasta_relatorios) / "envio.trava"):
            destino.mkdir(parents=True, exist_ok=True)
            log_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
                escritor = csv.writer(f, delimiter=";")
                escritor.writerow(["origem", "destino"])
                for pasta in escolhidas:
                    alvo = destino / pasta.name
                    if alvo.exists():  # nunca sobrescreve
                        tela.erro(f"Não movi {pasta.name}: já existe {alvo}.", saida)
                        continue
                    situacao = _mover(pasta, alvo)
                    if situacao == "nada":
                        tela.erro(f"Não movi {pasta.name}: alguma foto está aberta? Feche e tente de novo. "
                                  "A pasta ficou como estava.", saida)
                        continue
                    escritor.writerow([str(pasta), str(alvo)] + ([situacao] if situacao != "ok" else []))
                    f.flush()
                    movidas += 1
                    if situacao == "ok":
                        tela.ok(f"Arquivada: {pasta.name}", saida)
                    else:
                        tela.aviso(f"{pasta.name}: copiada inteira para o arquivo morto, mas a original não "
                                   "saiu toda (foto aberta?). Feche e apague o que sobrou dela à mão.", saida)
    except TravaOcupada:
        tela.erro("Um envio está rodando agora (outra janela?). Espere ele acabar. Nada foi movido.", saida)
        return 2
    tela.secao("Fim", saida)
    tela.status("ok" if movidas == len(escolhidas) else "aviso", f"{movidas} de {len(escolhidas)} pasta(s) no arquivo morto: {tela.caminho(destino)}", saida)
    tela.status("fraco", "Para trazer de volta, mova a pasta de novo para a pasta das redações.", saida)
    tela.status("fraco", "Dica: nas redações novas use nomes de pasta novos (o caderno lembra pasta/arquivo).",
                saida)
    return 0 if movidas == len(escolhidas) else 2
