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
    """Pergunta direto cada configuração (T53: o Antônio digitou "não" na
    tela antiga, que pedia o número da opção). Enter = deixa como está."""
    caminho = Path(caminho or caminho_config())
    cfg = config_mod.carregar_config(caminho if caminho.is_file() else None)
    tela.titulo("CONFIGURAÇÕES", saida)
    atual = "sim" if not cfg.headless else "não"
    saida(f"  Mostrar o navegador enquanto envia ou confere? Agora: {tela.c(atual, 'titulo')}")
    tela.status("fraco", "Aparecendo dá para acompanhar (bom enquanto testamos); escondido atrapalha menos.",
                saida, recuo=4)
    while True:
        resposta = tela.perguntar(f"  s = mostrar, n = esconder (Enter = deixar \"{atual}\"): ", entrada).lower()
        if resposta in ("", "s", "sim", "n", "nao", "não"):
            break
        tela.erro("Responda s ou n (ou Enter para deixar como está).", saida)
    if not resposta:
        tela.info(f"Nada mudou: navegador {'aparece' if atual == 'sim' else 'escondido'}.", saida)
        return 0
    esconder = resposta.startswith("n")
    gravar_opcao(caminho, "plataforma", "headless", "true" if esconder else "false")
    tela.ok("Pronto: o navegador vai ficar escondido." if esconder else "Pronto: o navegador vai aparecer.", saida)
    tela.status("fraco", f"Salvo em {tela.caminho(caminho)} (vale para os próximos envios e conferências).",
                saida)
    return 0
