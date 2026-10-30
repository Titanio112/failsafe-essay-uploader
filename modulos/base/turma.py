"""Escola e turma (M3): um lugar só resolve os caminhos da turma.

Estrutura (dentro de ``Redações plataforma/``)::

    <Escola>/<Turma>/alunos.csv        Nome;Email;Senha
    <Escola>/<Turma>/temas/<Tema>/     um JPG por aluno
    <Escola>/<Turma>/dados/            aprovações e temas_site.csv da turma
    <Escola>/<Turma>/relatorios/       relatórios da turma
    <Escola>/<Turma>/logs/             log da turma

Caderno (``relatorios/progresso.db``), trava e cópias continuam globais, na
raiz do projeto. Os algoritmos não mudam: só os caminhos do ``Config``.
Nada de cair num padrão: sem turma válida, recusa.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from modulos.base import config as config_mod

PLANILHA = "alunos.csv"
# Pasta de exemplo dentro de temas/: a pessoa troca o nome pelo tema. Enquanto tiver este nome, o script a ignora.
PASTA_GUIA = "Renomeie_Para_O_Tema_E_Coloque_As_Redacoes_Aqui"
_PROIBIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class TurmaInvalida(RuntimeError):
    """Escola/turma inexistente, nome inválido ou caminho que sai da turma."""


def raiz_redacoes() -> Path:
    return config_mod.RAIZ / config_mod.PASTA_REDACOES


def _eh_link(p: Path) -> bool:
    """Link simbólico ou junction do Windows: levaria para fora da turma."""
    return p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())


def _subpastas(pasta: Path) -> list[Path]:
    if not pasta.is_dir() or _eh_link(pasta):
        return []
    return sorted((p for p in pasta.iterdir()
                   if p.is_dir() and not _eh_link(p) and not p.name.startswith(".")), key=lambda p: p.name)


def _eh_turma(pasta: Path) -> bool:
    planilha = pasta / PLANILHA
    return planilha.is_file() and not _eh_link(planilha)


def listar_turmas(escola: str) -> list[str]:
    return [p.name for p in _subpastas(raiz_redacoes() / escola) if _eh_turma(p)]


def listar_escolas() -> list[str]:
    """Só pastas com ao menos uma turma (uma pasta de tema solta na raiz não é escola)."""
    return [p.name for p in _subpastas(raiz_redacoes()) if listar_turmas(p.name)]


def _validar_nome(nome: str, o_que: str) -> None:
    if (not nome or nome != nome.strip() or nome in (".", "..") or _PROIBIDOS.search(nome)
            or Path(nome).is_absolute()):
        raise TurmaInvalida(f"{o_que} inválida: {nome!r} (só o nome da pasta, sem / \\ .. nem caminho)")


def pasta_da_turma(escola: str, turma: str, criar: bool = False) -> Path:
    """Pasta da turma, conferida. ``criar`` (--preparar): pode ainda não existir."""
    _validar_nome(escola, "Escola")
    _validar_nome(turma, "Turma")
    raiz = raiz_redacoes()
    pasta = raiz / escola / turma
    for p in (raiz, raiz / escola, pasta, pasta / PLANILHA, *(pasta / s for s in ("temas", "dados", "relatorios", "logs"))):
        if _eh_link(p):
            raise TurmaInvalida(f"{p} é link/atalho de pasta: a turma não pode apontar para fora dela")
    if criar:
        return pasta
    if escola not in listar_escolas():
        raise TurmaInvalida(f"Escola não encontrada: {escola!r}. Escolas: {', '.join(listar_escolas()) or 'nenhuma'}")
    if turma not in listar_turmas(escola):
        raise TurmaInvalida(f"Turma não encontrada em {escola}: {turma!r} (precisa da pasta com {PLANILHA}). "
                            f"Turmas: {', '.join(listar_turmas(escola)) or 'nenhuma'}")
    if os.path.commonpath([pasta.resolve(), raiz.resolve()]) != str(raiz.resolve()):
        raise TurmaInvalida(f"{pasta} sai de {raiz}")
    return pasta


def aplicar_turma(cfg, escola: str, turma: str, criar: bool = False) -> Path:
    """Aponta TODOS os caminhos da turma no ``cfg`` (planilha, temas, dados,
    relatórios, logs). Levanta :class:`TurmaInvalida`. Retorna a pasta da turma."""
    pasta = pasta_da_turma(escola, turma, criar)
    cfg.escola, cfg.turma, cfg.id_turma = escola, turma, f"{escola}/{turma}"
    cfg.planilha = pasta / PLANILHA
    cfg.pasta_raiz = pasta / "temas"
    cfg.arquivo_nomes_aprovados = pasta / "dados" / "nomes_aprovados.csv"
    cfg.arquivo_pastas_aprovadas = pasta / "dados" / "pastas_aprovadas.csv"
    cfg.temas_site = pasta / "dados" / "temas_site.csv"
    cfg.pasta_relatorios = pasta / "relatorios"
    cfg.pasta_logs = pasta / "logs"
    return pasta
