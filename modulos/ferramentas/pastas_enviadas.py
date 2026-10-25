"""Pastas já enviadas (T60, issue 030).

No fim da conferência no site (menu 5), a pasta em que TODAS as fotos foram
conferidas e estão no site pode ser marcada: vira "ENVIADA - <nome>". Quem
abre a pasta das redações vê na hora o que já foi. O script ignora essas
pastas em tudo (envio, revisão, conferência), então a troca de nome não abre
caminho para reenvio. O arquivo morto (menu 11) oferece primeiro as marcadas.
Nada é apagado; cada marcação vai para relatorios/pastas_enviadas_<data>.csv
e, para desmarcar, basta tirar o "ENVIADA - " do nome.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

from modulos.base import relogio, tela

PREFIXO = "ENVIADA - "


def eh_pasta_enviada(nome: str) -> bool:
    return nome.casefold().startswith(PREFIXO.casefold())


def pastas_prontas(resultado, conferencias) -> list[str]:
    """Pastas em que toda foto da pasta foi conferida (conta lida) e está
    "no site". Foto sem aluno/tema, em revisão, faltando, em parte, outro
    tema ou cancelada deixa a pasta de fora."""
    from modulos.site.conferencia_site import NO_SITE
    no_site = {(item.pasta, item.arquivo) for conf in conferencias if not conf.erro and conf.lista is not None
               for item, estado, _ in conf.linhas if estado == NO_SITE}
    por_pasta: dict[str, list[str]] = {}
    for item in resultado.itens:
        if item.pasta and item.arquivo:
            por_pasta.setdefault(item.pasta, []).append(item.arquivo)
    return sorted(pasta for pasta, arquivos in por_pasta.items()
                  if arquivos and all((pasta, a) in no_site for a in arquivos))


def marcar_pastas_enviadas(pasta_raiz: Path, pastas: list[str], pasta_relatorios: Path,
                           entrada: Callable[[str], str] | None = None, saida: Callable = print) -> int:
    """Pergunta (s/n) e renomeia as pastas para "ENVIADA - <nome>". Retorna quantas."""
    if not pastas:
        return 0
    tela.secao("Pastas com tudo no site", saida)
    for pasta in pastas:
        tela.ok(pasta, saida)
    if tela.perguntar(f"  Marcar {len(pastas)} pasta(s) como \"{PREFIXO}...\"? Depois o arquivo morto (menu 11) "
                      "oferece guardar essas primeiro. (s/n): ", entrada).lower() not in ("s", "sim"):
        tela.info("Nenhuma pasta foi marcada.", saida)
        return 0
    log_csv = Path(pasta_relatorios) / f"pastas_enviadas_{relogio.agora():%Y%m%d_%H%M%S}.csv"
    log_csv.parent.mkdir(parents=True, exist_ok=True)
    marcadas = 0
    with open(log_csv, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["origem", "destino"])
        for pasta in pastas:
            origem, destino = Path(pasta_raiz) / pasta, Path(pasta_raiz) / f"{PREFIXO}{pasta}"
            if destino.exists():
                tela.erro(f"Não marquei {pasta}: já existe {destino.name}.", saida)
                continue
            try:
                origem.rename(destino)
            except OSError as e:
                tela.erro(f"Não marquei {pasta} ({type(e).__name__}): foto aberta? Feche e rode a opção 5 de novo.",
                          saida)
                continue
            escritor.writerow([str(origem), str(destino)])
            f.flush()
            marcadas += 1
    tela.status("ok" if marcadas == len(pastas) else "aviso",
                f"{marcadas} de {len(pastas)} pasta(s) marcada(s). Log: {tela.caminho(log_csv)}", saida)
    tela.status("fraco", f"Para desmarcar, tire o \"{PREFIXO}\" do nome da pasta.", saida)
    return marcadas
