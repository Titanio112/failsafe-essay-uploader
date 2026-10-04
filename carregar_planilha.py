"""Leitura da planilha XLSX de alunos."""

from __future__ import annotations

import openpyxl
from pathlib import Path
from typing import List

from config import Config
from planilha_arquivos import Aluno, PlanilhaError, normalizar_nome


def carregar_alunos(config: Config) -> List[Aluno]:
    """Carrega alunos da planilha XLSX.

    A planilha tem:
    - Linha 1: título (ignorada)
    - Linha 2: cabeçalho (Nome, E-mail, Sala, Créditos)
    - Linha 3+: dados
    """
    caminho = config.planilha
    if not caminho.exists():
        raise PlanilhaError(f"Planilha não encontrada: {caminho}")

    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb.active

    alunos = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        nome, email, sala, creditos = row[:4]
        if not nome:
            continue
        # Normalizar e-mail
        email_norm = email.strip().lower() if email else ""
        # Créditos pode vir como string ou None
        try:
            creditos_int = int(creditos) if creditos is not None else None
        except (ValueError, TypeError):
            creditos_int = None

        alunos.append(Aluno(
            nome=str(nome).strip(),
            email=email_norm,
            sala=str(sala).strip() if sala else "",
            creditos=creditos_int,
        ))

    if not alunos:
        raise PlanilhaError("Planilha sem alunos válidos (linhas 3+)")

    return alunos