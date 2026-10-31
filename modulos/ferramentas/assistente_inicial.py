"""Primeiro uso guiado (issue #34): cria escolas e turmas perguntando, com LEIA-ME.md em cada pasta.

Só roda quando não existe nenhuma turma (``listar_escolas()`` vazio) e quem chama
tem terminal. Só cria pastas e arquivos-modelo; nunca abre o site nem lê senha.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from modulos.base import tela
from modulos.base.config import PASTA_REDACOES, RAIZ_PASTA_REDACOES_LEIAME
from modulos.base.turma import PLANILHA, TurmaInvalida, _validar_nome, listar_escolas, pasta_da_turma, raiz_redacoes

Entrada = Callable[[str], str] | None
LEIA_ME = "LEIA-ME.md"
CABECALHO = "Nome;Email;Senha\n"
MAX_ITENS = 99

TEXTO_ESCOLA = """# Escola: {escola}

Cada pasta aqui dentro é uma **turma** desta escola. Para criar outra turma, rode `python main.py`
e escolha "12) Primeiro uso", ou crie a pasta com um `alunos.csv` dentro.
"""
TEXTO_TURMA = """# Turma: {escola} / {turma}

- `alunos.csv`: um aluno por linha, no formato `Nome;Email;Senha` (e-mail e senha da plataforma).
  Aluno sem senha não entra no site. Este arquivo nunca vai para o GitHub.
- `temas/`: uma pasta por tema, com as fotos das redações dentro.
- As pastas `dados/`, `relatorios/` e `logs/` aparecem sozinhas quando o script roda.
"""
TEXTO_TEMAS = """# Pasta temas/

Crie **uma pasta por tema** e ponha dentro as fotos (JPG) das redações:

    temas/<código> - <nome do tema>/<Nome do aluno>.jpg

- O **código** é o número no começo do nome da pasta (ex.: `100 - Filiação`). Ele tem de existir na plataforma.
- Cada foto leva o nome do aluno, como está na lista (`Ana Souza.jpg`).
- Pasta "ENVIADA - ..." é ignorada (tema já enviado).
"""
TEXTO_TEMA_EXEMPLO = """# Exemplo de pasta de tema

Ponha aqui as fotos desta turma neste tema, uma por aluno (`Aluno Exemplo.jpg`).
O número no começo do nome da pasta (100) é o código do tema na plataforma; troque pelo código real.
"""


def _sim(entrada: Entrada, texto: str) -> bool | None:
    """True/False para Sim/Não; None se a pessoa só apertou Enter (cancela)."""
    while True:
        r = tela.perguntar(f"  {texto} (Sim/Não): ", entrada).lower()
        if not r:
            return None
        if r in ("s", "sim"):
            return True
        if r in ("n", "nao", "não"):
            return False
        tela.erro("Responda Sim ou Não.")


def _numero(entrada: Entrada, texto: str) -> int | None:
    while True:
        r = tela.perguntar(f"  {texto} ", entrada)
        if not r:
            return None
        if r.isdecimal() and 1 <= int(r) <= MAX_ITENS:
            return int(r)
        tela.erro(f"Digite um número de 1 a {MAX_ITENS}.")


def _nome(entrada: Entrada, texto: str, o_que: str, usados: set[str]) -> str | None:
    while True:
        r = tela.perguntar(f"  {texto} ", entrada)
        if not r:
            return None
        try:
            _validar_nome(r, o_que)
        except TurmaInvalida as e:
            tela.erro(str(e))
            continue
        if r.casefold() in usados:
            tela.erro(f"{r!r} já foi usado. Escolha outro nome.")
            continue
        return r


def _escrever(arquivo: Path, texto: str, criados: list[Path]) -> None:
    if not arquivo.exists():
        arquivo.write_text(texto, encoding="utf-8")
        criados.append(arquivo)


def criar_turma(escola: str, turma: str, criados: list[Path], exemplo: bool = False) -> Path:
    """Cria Redações plataforma/<escola>/<turma>/ (alunos.csv, temas/, LEIA-ME.md em cada nível)."""
    pasta = pasta_da_turma(escola, turma, criar=True)
    temas = pasta / "temas"
    temas.mkdir(parents=True, exist_ok=True)
    if exemplo:  # aluno inventado e SEM senha: nunca entra no site
        tema = temas / "100 - Exemplo de tema"
        tema.mkdir(exist_ok=True)
        _escrever(tema / LEIA_ME, TEXTO_TEMA_EXEMPLO, criados)
    _escrever(pasta / PLANILHA, CABECALHO + ("Aluno Exemplo;aluno.exemplo@example.com;\n" if exemplo else ""), criados)
    _escrever(raiz_redacoes() / LEIA_ME, RAIZ_PASTA_REDACOES_LEIAME, criados)
    _escrever(pasta.parent / LEIA_ME, TEXTO_ESCOLA.format(escola=escola), criados)
    _escrever(pasta / LEIA_ME, TEXTO_TURMA.format(escola=escola, turma=turma), criados)
    _escrever(temas / LEIA_ME, TEXTO_TEMAS, criados)
    return pasta


def _perguntar_estrutura(entrada: Entrada) -> list[tuple[str, list[str]]] | None:
    """[(escola, [turmas])] ou None se cancelou."""
    n_escolas = _numero(entrada, "São quantas escolas?")
    if n_escolas is None:
        return None
    estrutura, escolas_usadas = [], set()
    for i in range(1, n_escolas + 1):
        tela.secao(f"Escola {i} de {n_escolas}")
        escola = _nome(entrada, f"Qual o nome da escola {i}?", "Escola", escolas_usadas)
        if escola is None:
            return None
        escolas_usadas.add(escola.casefold())
        n_turmas = _numero(entrada, f"São quantas turmas na {escola}?")
        if n_turmas is None:
            return None
        turmas: set[str] = set()
        lista = []
        for j in range(1, n_turmas + 1):
            turma = _nome(entrada, f"Nome da turma {j} de {n_turmas} ({escola}):", "Turma", turmas)
            if turma is None:
                return None
            turmas.add(turma.casefold())
            lista.append(turma)
        estrutura.append((escola, lista))
    return estrutura


def _resumo(criadas: list[tuple[str, str]], criados: list[Path]) -> bool:
    """Valida o que foi criado e mostra escolas, turmas, links e o próximo passo. True = tudo certo."""
    tela.titulo("RESUMO  ·  primeiro uso")
    tudo_certo = True
    tela.secao("Escolas e turmas")
    escolas = list(dict.fromkeys(e for e, _ in criadas))
    for escola in escolas:
        tela.info(f"{escola}")
        for e, turma in (c for c in criadas if c[0] == escola):
            pasta = pasta_da_turma(e, turma)
            ok = (pasta / PLANILHA).is_file() and (pasta / "temas").is_dir()
            tudo_certo &= ok
            tela.status("ok" if ok else "erro", f"{turma}  →  {tela.caminho(pasta)}", recuo=6)
    tela.secao("Arquivos criados (Ctrl+clique abre)")
    for arquivo in criados:
        tela.status("fraco", tela.caminho(arquivo), recuo=4)
    tela.secao("Como colocar as redações")
    for linha in (
        "1. Abra a pasta da turma e preencha o alunos.csv: Nome;Email;Senha, um aluno por linha.",
        "2. Dentro de temas/, crie uma pasta por tema: \"100 - Nome do tema\" (o número do começo é o código do tema).",
        "3. Ponha as fotos JPG dentro da pasta do tema, uma por aluno, com o nome do aluno: Ana Souza.jpg.",
        "4. Rode python main.py, escolha a escola e a turma e use \"1) Conferir as redações\" (não envia nada).",
    ):
        tela.status("fraco", linha, recuo=4)
    tela.status("ok" if tudo_certo else "erro",
                "Tudo certo." if tudo_certo else "Algo ficou faltando: veja os itens ✘ acima.")
    return tudo_certo


def executar_assistente(entrada: Entrada = None) -> bool:
    """Passo a passo do primeiro uso. True = criou ao menos uma turma."""
    tela.titulo("PRIMEIRO USO  ·  vamos montar as pastas")
    primeira = _sim(entrada, "É a primeira vez que você está executando?")
    if not primeira:
        tela.aviso(f"Nenhuma turma encontrada. Cada turma é uma pasta \"{PASTA_REDACOES}/<Escola>/<Turma>/\" "
                   "com alunos.csv. Se as suas pastas já existem, confira se estão nesse formato.")
        tela.comando('python main.py --preparar --escola "<Escola>" --turma "<Turma>"', "cria uma turma")
        return False
    agora = _sim(entrada, "Você deseja já configurar as escolas e as turmas agora?")
    if agora is None:
        return False
    criados: list[Path] = []
    if agora:
        estrutura = _perguntar_estrutura(entrada)
        if estrutura is None:
            tela.aviso("Cancelado. Nada foi criado.")
            return False
        criadas = []
        for escola, turmas in estrutura:
            for turma in turmas:
                criar_turma(escola, turma, criados)
                criadas.append((escola, turma))
    else:
        tela.info("Vou criar só uma escola de exemplo, para você ver como as pastas ficam.")
        criar_turma("Escola Teste", "Turma Exemplo", criados, exemplo=True)
        criadas = [("Escola Teste", "Turma Exemplo")]
    _resumo(criadas, criados)
    return bool(listar_escolas())
