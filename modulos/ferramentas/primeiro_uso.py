"""Primeiro uso (T38): `python main.py --preparar` cria o que falta e explica
onde colocar cada coisa. Nunca sobrescreve nada que já exista.

Estrutura padrão (na raiz do projeto):
- ``Redações plataforma/``: uma subpasta por tema, um JPG por aluno;
- ``dados/dados_alunos.csv``: lista de alunos (Nome;Email);
- ``.env``: e-mail/senha da conta de teste e senha padrão dos alunos.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from modulos.base import tela
from modulos.base.config import Config, RAIZ_PASTA_REDACOES_LEIAME

CABECALHO_ALUNOS = "Nome;Email\n"


def _tem_jpg(pasta: Path) -> bool:
    return pasta.is_dir() and any(f.suffix.lower() in (".jpg", ".jpeg") for f in pasta.rglob("*") if f.is_file())


def verificar(cfg: Config, env: Path) -> list[tuple[bool, str, str]]:
    """[(ok, item, o que fazer)] na ordem em que o Antônio resolve."""
    planilha, pasta = Path(cfg.planilha), Path(cfg.pasta_raiz)
    alunos_ok = planilha.is_file() and len(planilha.read_text(encoding="utf-8-sig").strip().splitlines()) > 1
    return [
        (alunos_ok, f"Lista de alunos: {planilha}",
         "abra o arquivo e coloque um aluno por linha: Nome;Email (o e-mail da plataforma)"),
        (_tem_jpg(pasta), f"Redações: {pasta}",
         "crie uma subpasta por tema e coloque nela um JPG por aluno, com o nome do aluno"),
        (env.is_file(), f"Senhas: {env}",
         "abra o .env e preencha ESQUEMA_EMAIL_TESTE, ESQUEMA_SENHA_TESTE e ESQUEMA_SENHA_PADRAO"),
    ]


def preparar(cfg: Config, raiz: Path, saida: Callable = print) -> int:
    """Cria pastas e arquivos-modelo que faltam. Retorna 0."""
    pasta, planilha, env = Path(cfg.pasta_raiz), Path(cfg.planilha), Path(raiz) / ".env"
    criados = []
    if not pasta.is_dir():
        pasta.mkdir(parents=True)
        criados.append(str(pasta))
    leiame = pasta / "LEIA-ME.md"
    if not leiame.exists():
        leiame.write_text(RAIZ_PASTA_REDACOES_LEIAME, encoding="utf-8")
        criados.append(str(leiame))
    if not planilha.exists():
        planilha.parent.mkdir(parents=True, exist_ok=True)
        planilha.write_text(CABECALHO_ALUNOS, encoding="utf-8")
        criados.append(str(planilha))
    exemplo = Path(raiz) / ".env.example"
    if not env.exists() and exemplo.is_file():
        shutil.copy(exemplo, env)
        criados.append(str(env))

    tela.titulo("PREPARAR  ·  primeiro uso", saida)
    tela.secao("Criado agora", saida)
    for c in criados:
        tela.ok(f"criado: {c}", saida)
    if not criados:
        tela.info("nada a criar: tudo ja existe.", saida)
    mostrar_guia(cfg, env, saida)
    return 0


def mostrar_guia(cfg: Config, env: Path, saida: Callable = print) -> bool:
    """Mostra o que está pronto e o que falta. Retorna True se está tudo pronto."""
    itens = verificar(cfg, env)
    tela.secao("O que o script precisa", saida)
    for ok, item, fazer in itens:
        tela.status("ok" if ok else "erro", item, saida)
        if not ok:
            tela.status("fraco", fazer, saida, recuo=6)
    pronto = all(ok for ok, _, _ in itens[:2])  # .env só é preciso para entrar no site
    saida("")
    tela.comando("python main.py", "pronto para o dry-run" if pronto
                 else "depois de resolver o que tem ✘", saida)
    return pronto
