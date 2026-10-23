"""Configurações (T52): menu opção 12.

Guarda as escolhas no config.ini da raiz (o mesmo que carregar_config lê),
mexendo só na linha da opção: comentários e o resto do arquivo ficam.
Hoje: mostrar ou não o navegador enquanto envia/confere. `--sem-janela`
continua valendo numa execução só.
"""

from __future__ import annotations

import configparser
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
    """Troca (ou cria) ``chave = valor`` dentro de ``[secao]``.

    T56: acha a seção como o configparser acha (``[plataforma] ; nota`` vale;
    ``[Plataforma]`` é outra seção). Se o arquivo ficar ilegível, volta o
    texto de antes e levanta ConfigInvalida (nunca diz "pronto" à toa)."""
    caminho = Path(caminho)
    if not caminho.is_file():
        exemplo = caminho.with_name("config.example.ini")
        if exemplo.is_file():  # sem config.ini o script usava o exemplo: parte dele
            shutil.copy2(exemplo, caminho)
    antes = caminho.read_text(encoding="utf-8-sig") if caminho.is_file() else None
    linhas = antes.splitlines() if antes is not None else []

    def _cabecalho(linha: str) -> str | None:
        m = configparser.ConfigParser.SECTCRE.match(linha.strip())
        return m.group("header") if m else None

    inicio = next((i for i, l in enumerate(linhas) if _cabecalho(l) == secao), None)
    if inicio is None:
        if linhas and linhas[-1].strip():
            linhas.append("")
        linhas += [f"[{secao}]", f"{chave} = {valor}"]
    else:
        fim = next((i for i in range(inicio + 1, len(linhas)) if _cabecalho(linhas[i]) is not None), len(linhas))
        padrao = re.compile(rf"^\s*{re.escape(chave)}\s*[=:]", re.IGNORECASE)
        achou = next((i for i in range(inicio + 1, fim) if padrao.match(linhas[i])), None)
        if achou is None:
            linhas.insert(inicio + 1, f"{chave} = {valor}")
        else:
            linhas[achou] = f"{chave} = {valor}"
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    try:
        config_mod._ler_ini(caminho)
    except (configparser.Error, ValueError) as e:
        if antes is None:
            caminho.unlink()
        else:
            caminho.write_text(antes, encoding="utf-8")
        raise config_mod.ConfigInvalida(f"{caminho.name} ficaria com erro ({e}); nada mudou.") from e


def resumo_navegador(cfg=None) -> str:
    try:  # T56: o menu nunca quebra por causa do config.ini
        cfg = cfg or config_mod.carregar_config()
    except config_mod.ConfigInvalida:
        return "config.ini com erro"
    return "navegador: escondido" if cfg.headless else "navegador: aparece"


def executar_configuracoes(caminho: Path | None = None, entrada: Entrada | None = None,
                           saida: Callable = print) -> int:
    """Pergunta direto cada configuração (T53: o Antônio digitou "não" na
    tela antiga, que pedia o número da opção). Enter = deixa como está."""
    caminho = Path(caminho or caminho_config())
    tela.titulo("CONFIGURAÇÕES", saida)
    try:
        cfg = config_mod.carregar_config(caminho if caminho.is_file() else None)
    except config_mod.ConfigInvalida as e:
        tela.erro(f"O {tela.caminho(caminho)} tem um erro: {e}", saida)
        tela.status("fraco", "Abra o arquivo e corrija (ou apague para voltar ao padrão).", saida)
        return 2
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
    try:
        gravar_opcao(caminho, "plataforma", "headless", "true" if esconder else "false")
    except (config_mod.ConfigInvalida, OSError) as e:
        tela.erro(f"Não salvei: {e}", saida)
        return 2
    tela.ok("Pronto: o navegador vai ficar escondido." if esconder else "Pronto: o navegador vai aparecer.", saida)
    tela.status("fraco", f"Salvo em {tela.caminho(caminho)} (vale para os próximos envios e conferências).",
                saida)
    return 0
