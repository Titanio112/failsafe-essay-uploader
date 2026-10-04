"""Lógica de conciliação: alunos × arquivos → estados."""

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
    SUGESTAO_FUZZY,
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


def conciliar(
    alunos: List[Aluno],
    arquivos_por_pasta: dict[str, List[str]],
    codigos_site: Set[str],
    limiar: float = 95.0,
    margem: float = 8.0,
) -> ResultadoConciliacao:
    """Concilia alunos com arquivos descobertos.

    Retorna ResultadoConciliacao com itens classificados em estados.
    """
    # Índice por nome normalizado
    por_norm = {}
    for a in alunos:
        por_norm.setdefault(a.nome_norm, []).append(a)

    # Detectar códigos duplicados no combo do site
    codigos_duplicados_site: Set[str] = set()
    if codigos_site:
        contagem_codigos: dict[str, int] = {}
        for cod in codigos_site:
            contagem_codigos[cod] = contagem_codigos.get(cod, 0) + 1
        codigos_duplicados_site = {cod for cod, count in contagem_codigos.items() if count > 1}

    # Contar quantos arquivos cada aluno tem por código
    contagem_aluno_codigo: dict[tuple[str, str], int] = defaultdict(int)

    # Primeira passada: contar
    for pasta, arquivos in arquivos_por_pasta.items():
        for nome_arquivo in arquivos:
            pessoa = extrair_pessoa(nome_arquivo)
            norm = normalizar_nome(pessoa)
            codigo = extrair_codigo_tema(nome_arquivo, pasta)
            if norm and codigo:
                contagem_aluno_codigo[(norm, codigo)] += 1

    itens: List[ItemConciliacao] = []
    alunos_com_arquivo: Set[str] = set()

    # Segunda passada: classificar
    for pasta, arquivos in arquivos_por_pasta.items():
        for nome_arquivo in arquivos:
            pessoa = extrair_pessoa(nome_arquivo)
            norm = normalizar_nome(pessoa)
            codigo = extrair_codigo_tema(nome_arquivo, pasta)

            # SEM_CODIGO: arquivo sem código no nome nem na pasta
            if not codigo:
                itens.append(ItemConciliacao(
                    pasta=pasta,
                    arquivo=nome_arquivo,
                    pessoa=pessoa,
                    estado=SEM_CODIGO,
                    observacao="sem código no nome do arquivo nem no nome da pasta",
                ))
                continue

            # CODIGO_INVALIDO: código não existe no combo do site
            if codigos_site and codigo not in codigos_site:
                itens.append(ItemConciliacao(
                    pasta=pasta,
                    arquivo=nome_arquivo,
                    pessoa=pessoa,
                    estado=CODIGO_INVALIDO,
                    codigo_tema=codigo,
                    codigo_valido=False,
                    observacao=f"código {codigo} não existe no combo do site",
                ))
                continue

            # Candidatos exatos
            candidatos_exatos = por_norm.get(norm, [])
            if len(candidatos_exatos) == 1:
                aluno = candidatos_exatos[0]
                if contagem_aluno_codigo.get((norm, codigo), 0) > 1:
                    itens.append(ItemConciliacao(
                        pasta=pasta,
                        arquivo=nome_arquivo,
                        pessoa=pessoa,
                        estado=REVISAO_MANUAL,
                        aluno=aluno,
                        codigo_tema=codigo,
                        codigo_valido=True,
                        observacao=f"duplicata: mesmo aluno + mesmo código ({codigo})",
                    ))
                else:
                    itens.append(ItemConciliacao(
                        pasta=pasta,
                        arquivo=nome_arquivo,
                        pessoa=pessoa,
                        estado=EXATO_UNICO,
                        aluno=aluno,
                        codigo_tema=codigo,
                        codigo_valido=True,
                    ))
                    alunos_com_arquivo.add(aluno.id)
                continue

            if len(candidatos_exatos) > 1:
                nomes = [a.nome for a in candidatos_exatos]
                itens.append(ItemConciliacao(
                    pasta=pasta,
                    arquivo=nome_arquivo,
                    pessoa=pessoa,
                    estado=AMBIGUO,
                    candidatos=candidatos_exatos,
                    codigo_tema=codigo,
                    codigo_valido=True,
                    observacao=f"múltiplos alunos com mesmo nome normalizado: {nomes}",
                ))
                continue

            # Fuzzy
            candidato_fuzzy = _sugerir_fuzzy(norm, alunos, limiar, margem)
            if candidato_fuzzy:
                if contagem_aluno_codigo.get((candidato_fuzzy.nome_norm, codigo), 0) > 1:
                    itens.append(ItemConciliacao(
                        pasta=pasta,
                        arquivo=nome_arquivo,
                        pessoa=pessoa,
                        estado=REVISAO_MANUAL,
                        aluno=candidato_fuzzy,
                        codigo_tema=codigo,
                        codigo_valido=True,
                        observacao=f"duplicata fuzzy: mesmo aluno + mesmo código ({codigo})",
                    ))
                else:
                    itens.append(ItemConciliacao(
                        pasta=pasta,
                        arquivo=nome_arquivo,
                        pessoa=pessoa,
                        estado=SUGESTAO_FUZZY,
                        aluno=candidato_fuzzy,
                        codigo_tema=codigo,
                        codigo_valido=True,
                        score_fuzzy=fuzz.token_set_ratio(norm, candidato_fuzzy.nome_norm),
                        observacao=f"revisão humana obrigatória (SUGESTAO_FUZZY nunca entra na fila real)",
                    ))
                    alunos_com_arquivo.add(candidato_fuzzy.id)
                continue

            # ARQUIVO_SEM_ALUNO
            itens.append(ItemConciliacao(
                pasta=pasta,
                arquivo=nome_arquivo,
                pessoa=pessoa,
                estado=ARQUIVO_SEM_ALUNO,
                codigo_tema=codigo,
                codigo_valido=True,
                observacao="nenhum aluno compatível encontrado",
            ))
    # ALUNO_SEM_ARQUIVO
    for aluno in alunos:
        if aluno.id not in alunos_com_arquivo:
            itens.append(ItemConciliacao(
                pasta="",
                arquivo="",
                pessoa=aluno.nome,
                estado=ALUNO_SEM_ARQUIVO,
                aluno=aluno,
                observacao="aluno da planilha sem nenhum arquivo associado",
            ))

    return ResultadoConciliacao(itens)