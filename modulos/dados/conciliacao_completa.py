"""Conciliação com as aprovações do humano (T40).

Um caminho só para o dry-run, a revisão e os dois envios (teste e produção):
lê os JPGs da pasta, os nomes aprovados (``dados/nomes_aprovados.csv``) e os
temas aprovados por pasta (``dados/pastas_aprovadas.csv``) e concilia. O modo
teste usa as mesmas regras com os arquivos de aprovação de ``testes/``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from modulos.base.config import Config
from modulos.dados.arquivos_csv import abrir_csv
from modulos.dados.nomes_aprovados import carregar_nomes_aprovados
from modulos.dados.planilha_arquivos import Aluno, ResultadoConciliacao, conciliar, descobrir_arquivos
from modulos.dados.sugestao_temas import carregar_codigos_pasta

TEMAS_SITE_CSV = Path("dados/temas_site.csv")


def ler_codigos_site_csv(caminho: Path) -> list[str]:
    """Códigos (strings exatas) da coluna 'codigo' do CSV, NA ORDEM e com os
    repetidos (ex.: 0000 duas vezes), para a conciliação marcar código
    duplicado no combo (bug 001). Vazio se não existir."""
    if not Path(caminho).is_file():
        return []
    return [row["codigo"] for row in csv.DictReader(abrir_csv(caminho)) if row.get("codigo")]


@dataclass
class Conciliacao:
    resultado: ResultadoConciliacao
    arquivos: dict[str, list[str]]
    nomes_aprovados: dict
    codigos_pasta: dict[str, str]


def conciliar_com_aprovacoes(cfg: Config, alunos: list[Aluno], codigos_site: list[str]) -> Conciliacao:
    arquivos = descobrir_arquivos(cfg)
    nomes_aprovados = carregar_nomes_aprovados(cfg.arquivo_nomes_aprovados, alunos)
    codigos_pasta = carregar_codigos_pasta(cfg.arquivo_pastas_aprovadas)
    resultado = conciliar(
        alunos, arquivos,
        codigos_site=codigos_site,
        limiar=cfg.limiar_fuzzy, margem=cfg.margem_minima,
        nomes_aprovados=nomes_aprovados,
        codigos_pasta=codigos_pasta,
    )
    return Conciliacao(resultado, arquivos, nomes_aprovados, codigos_pasta)
