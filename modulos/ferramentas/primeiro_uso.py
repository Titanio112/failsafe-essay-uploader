"""Primeiro uso (T38): `python main.py --preparar` cria o que falta e explica
onde colocar cada coisa. Nunca sobrescreve nada que já exista.

Estrutura (M3), com ``--escola`` e ``--turma``:
- ``Redações plataforma/<Escola>/<Turma>/alunos.csv``: Nome;Email;Senha;
- ``Redações plataforma/<Escola>/<Turma>/temas/``: uma subpasta por tema,
  um JPG por aluno;
- ``.env``: só o e-mail/senha da CONTA DE TESTE (aluno usa a senha do alunos.csv).
Sem turma, cria só a pasta das redações e o ``.env``, e explica como criar a turma.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from modulos.base import tela
from modulos.base.config import Config, RAIZ_PASTA_REDACOES_LEIAME
from modulos.base.turma import PASTA_GUIA
from modulos.dados.arquivos_csv import ler_texto

CABECALHO_ALUNOS = "Nome;Email;Senha\n"


def _tem_jpg(pasta: Path) -> bool:
    """JPG direto numa pasta de tema (subpasta dentro do tema não é lida)."""
    return pasta.is_dir() and any(f.suffix.lower() in (".jpg", ".jpeg") for f in pasta.glob("*/*") if f.is_file())


VARIAVEIS_ENV = ("ESQUEMA_EMAIL_TESTE", "ESQUEMA_SENHA_TESTE")  # M3: aluno usa a senha do alunos.csv


def _env_preenchido(env: Path) -> bool:
    """Bug 026: o .env existe E as variáveis têm valor que não é o de
    exemplo ("<definir-no-.env>"). Não lê nem mostra os valores além disso."""
    if not env.is_file():
        return False
    from dotenv import dotenv_values
    from modulos.base.config import eh_valor_de_exemplo
    valores = dotenv_values(env)
    return all((valores.get(v) or "").strip() and not eh_valor_de_exemplo(valores[v]) for v in VARIAVEIS_ENV)


def verificar(cfg: Config, env: Path) -> list[tuple[bool, str, str]]:
    """[(ok, item, o que fazer)] na ordem em que o Antônio resolve."""
    planilha, pasta = Path(cfg.planilha), Path(cfg.pasta_raiz)
    alunos_ok = planilha.is_file() and len(ler_texto(planilha).strip().splitlines()) > 1
    return [
        (alunos_ok, f"Lista de alunos: {planilha}",
         "abra o arquivo e coloque um aluno por linha: Nome;Email;Senha (e-mail e senha da plataforma; "
         "o nome igual ao que o site mostra no menu)"),
        (_tem_jpg(pasta), f"Redações: {pasta}",
         "crie uma subpasta por tema e coloque nela um JPG por aluno, com o nome do aluno"),
        (_env_preenchido(env), f"Senhas: {env}",
         "abra o .env e preencha ESQUEMA_EMAIL_TESTE e ESQUEMA_SENHA_TESTE (conta de teste)"),
    ]


def preparar(cfg: Config, raiz: Path, saida: Callable = print) -> int:
    """Cria pastas e arquivos-modelo que faltam. Retorna 0."""
    pasta, planilha, env = Path(cfg.pasta_raiz), Path(cfg.planilha), Path(raiz) / ".env"
    criados = []
    if not pasta.is_dir():
        pasta.mkdir(parents=True)
        criados.append(str(pasta))
    if cfg.turma:  # um só LEIA-ME por escola, na pasta da escola (nunca dentro de temas/); issue #57
        if cfg.escola:
            from modulos.ferramentas.assistente_inicial import LEIA_ME, TEXTO_ESCOLA
            leiame = pasta.parent.parent / LEIA_ME
            if not leiame.exists():
                leiame.write_text(TEXTO_ESCOLA.format(escola=cfg.escola, guia=PASTA_GUIA), encoding="utf-8")
                criados.append(str(leiame))
    else:
        leiame = pasta / "LEIA-ME.md"
        if not leiame.exists():
            leiame.write_text(RAIZ_PASTA_REDACOES_LEIAME, encoding="utf-8")
            criados.append(str(leiame))
    if cfg.turma and not planilha.exists():  # M3: lista só dentro da turma
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
    if not cfg.turma:
        tela.comando('python main.py --preparar --escola "<Escola>" --turma "<Turma>"',
                     "cria a turma: alunos.csv (Nome;Email;Senha) e temas/", saida)
        return 0
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
