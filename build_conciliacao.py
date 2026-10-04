import os

os.makedirs('temp_conciliacao', exist_ok=True)

part1 = '''"""Lógica de conciliação: alunos × arquivos → estados."""

from __future__ import annotations

import warnings
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Set

from rapidfuzz import fuzz

from config import Config
from estados import (
    ALUNO_SEM_ARQUIVO,
    AMBIGUO,
    ARQUIVO_SEM_ALUNO,
    CODIGO_INVALIDO,
    EXATO_UNICO,
    REVISAO_MANUAL,
    SEM_CODIGO,
    SIMULADO,
    ESTADOS_CONCILIACAO,
    MARCADOR_PESSOA,
)
from normalizacao import (
    extrair_codigo_tema,
    extrair_pessoa,
    normalizar_nome,
)
from planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao


def _emitir_aviso(mensagem: str) -> None:
    aviso = f"[AVISO] {mensagem}"
    print(aviso)
    warnings.warn(aviso, UserWarning, stacklevel=3)


def _sugerir_fuzzy(
    norm: str, alunos: List[Aluno], limiar: float, margem: float
) -> Optional[Aluno]:
    """Retorna melhor candidato fuzzy se acima do limiar e com margem para o segundo."""
    candidatos = []
    for a in alunos:
        score = fuzz.token_set_ratio(norm, a.nome_norm)
        if score >= limiar:
            candidatos.append((score, a))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[0], reverse=True)
    melhor_score, melhor_aluno = candidatos[0]
    segundo_score = candidatos[1][0] if len(candidatos) > 1 else 0.0

    if melhor_score - segundo_score >= margem:
        return melhor_aluno

    return None
'''

with open('temp_conciliacao/part1.py', 'w', encoding='utf-8') as f:
    f.write(part1)
print('part1 written')