"""Configurações (T52): menu opção 11.

Guarda as escolhas no config.ini da raiz (o mesmo que carregar_config lê),
mexendo só na linha da opção: comentários e o resto do arquivo ficam.
Hoje: mostrar ou não o navegador enquanto envia/confere. `--sem-janela`
continua valendo numa execução só.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Callable

from modulos.base import config as config_mod
from modulos.base import tela

Entrada = Callable[[str], str]


def caminho_config() -> Path:
    return config_mod.RAIZ / "config.ini"


def gravar_opcao(caminho: Path, secao: str, chave: str, valor: str) -> None:
    """Troca (ou cria) ``chave = valor`` dentro de ``[secao]``."""
    caminho = Path(caminho)
    if not caminho.is_file():
        exemplo = caminho.with_name("config.example.ini")
        if exemplo.is_file():  # sem config.ini o script usava o exemplo: parte dele
            shutil.copy2(exemplo, caminho)
    linhas = caminho.read_text(encoding="utf-8").splitlines() if caminho.is_file() else []
    inicio = next((i for i, l in enumerate(linhas) if l.strip().lower() == f"[{secao}]"), None)
    if inicio is None:
        if linhas and linhas[-1].strip():
            linhas.append("")
        linhas += [f"[{secao}]", f"{chave} = {valor}"]
    else:
        fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i].lstrip().startswith("[")), len(linhas))
        padrao = re.compile(rf"^\s*{re.escape(chave)}\s*[=:]", re.IGNORECASE)
        achou = next((i for i in range(inicio + 1, fim) if padrao.match(linhas[i])), None)
        if achou is None:
            linhas.insert(inicio + 1, f"{chave} = {valor}")
        else:
            linhas[achou] = f"{chave} = {valor}"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def resumo_navegador(cfg=None) -> str:
    cfg = cfg or config_mod.carregar_config()
    return "navegador: escondido" if cfg.headless else "navegador: aparece"


def executar_configuracoes(caminho: Path | None = None, entrada: Entrada | None = None,
                           saida: Callable = print) -> int:
    """Mostra as configurações e troca a escolhida até a pessoa dar Enter."""
    caminho = Path(caminho or caminho_config())
    while True:
        cfg = config_mod.carregar_config(caminho if caminho.is_file() else None)
        tela.titulo("CONFIGURAÇÕES", saida)
        visivel = "sim" if not cfg.headless else "não"
        saida(f"  {tela.c('1)', 'tecla')} Mostrar o navegador enquanto envia ou confere: {tela.c(visivel, 'titulo')}")
        tela.status("fraco", "Aparecendo dá para acompanhar (bom enquanto testamos); escondido atrapalha menos.",
                    saida, recuo=5)
        saida("")
        escolha = tela.perguntar("  Número para trocar (Enter = voltar): ", entrada)
        if escolha != "1":
            if escolha:
                tela.erro("Opção inválida.", saida)
                continue
            return 0
        gravar_opcao(caminho, "plataforma", "headless", "false" if cfg.headless else "true")
        tela.ok("Navegador vai aparecer." if cfg.headless else "Navegador vai ficar escondido.", saida)
        tela.status("fraco", f"Salvo em {tela.caminho(caminho)}", saida)
