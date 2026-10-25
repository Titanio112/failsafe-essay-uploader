"""Nomes de arquivo aprovados por humano -> aluno (T26).

O nome no arquivo costuma ser curto ou ter erro de digitação
("Ana Lalara Larili", "Isabela Larulii"). A regra do projeto exige revisão
humana para isso. Em vez de revisar arquivo por arquivo toda semana, o
dry-run grava SUGESTÕES em ``dados/nomes_aprovados.csv``; o Antônio marca
``sim`` na coluna ``aprovado`` e, daí em diante, aquele nome de arquivo conta
como nome exato do aluno. Nada é aprovado automaticamente.

Colunas (``;``): nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo
"""

from __future__ import annotations

import csv
from pathlib import Path

from rapidfuzz import fuzz

from modulos.dados.arquivos_csv import CsvIlegivel, garantir_quebra_final, ler_linhas_ponto_e_virgula
from modulos.dados.normalizacao import normalizar_nome
from modulos.dados.planilha_arquivos import (
    Aluno, ResultadoConciliacao, _emitir_aviso, candidatos_nome_parcial, eh_folha_em_branco,
)

COLUNAS = ["nome_no_arquivo", "aluno_nome", "aluno_email", "aprovado", "motivo"]
RESPOSTAS_SIM = {"sim", "s", "x", "ok", "yes"}
SCORE_MINIMO_SUGESTAO = 70.0


def _ler(caminho: Path) -> list[dict]:
    return ler_linhas_ponto_e_virgula(caminho, ["nome_no_arquivo", "aluno_email", "aprovado"])


def carregar_nomes_aprovados(caminho: Path, alunos: list[Aluno]) -> dict[str, Aluno]:
    """{nome normalizado do arquivo: Aluno} só das linhas com aprovado=sim.

    E-mail que não está na lista de alunos é ignorado (aviso). O mesmo nome
    de arquivo aprovado para dois alunos diferentes é ignorado (aviso)."""
    por_email = {a.email.casefold(): a for a in alunos}
    aprovados: dict[str, Aluno] = {}
    conflitos: set[str] = set()
    try:
        linhas = _ler(caminho)
    except CsvIlegivel as e:
        _emitir_aviso(f"nomes_aprovados: {e}; nenhuma aprovacao de nome foi lida.")
        return {}
    for linha in linhas:
        if linha.get("aprovado", "").lower() not in RESPOSTAS_SIM:
            continue
        norm = normalizar_nome(linha.get("nome_no_arquivo", ""))
        aluno = por_email.get(linha.get("aluno_email", "").casefold())
        if not norm:
            continue
        if aluno is None:
            _emitir_aviso(f"nomes_aprovados: e-mail fora da lista de alunos para '{linha.get('nome_no_arquivo')}'; ignorado.")
            continue
        if (linha.get("motivo", "") == "nome parcial"
                and len(candidatos_nome_parcial(norm, alunos)) > 1):
            # T46: na aprovação só um aluno combinava; a lista mudou e agora
            # combinam vários -> a aprovação antiga não vale mais.
            _emitir_aviso(f"nomes_aprovados: '{linha.get('nome_no_arquivo')}' agora combina com mais de um "
                          "aluno da lista; aprovacao ignorada (aprove de novo).")
            continue
        if _outro_aluno_tao_parecido(norm, aluno, alunos):
            # Bug 012: o mesmo vale para "parecido" (ex.: "Ana" aprovado para
            # Ana Souza e depois entra Ana Lima na lista).
            _emitir_aviso(f"nomes_aprovados: '{linha.get('nome_no_arquivo')}' parece tanto com outro aluno "
                          "da lista quanto com o aprovado; aprovacao ignorada (aprove de novo).")
            continue
        if norm in aprovados and aprovados[norm] is not aluno:
            conflitos.add(norm)
        aprovados[norm] = aluno
    for norm in conflitos:
        _emitir_aviso(f"nomes_aprovados: '{norm}' aprovado para mais de um aluno; ignorado.")
        aprovados.pop(norm, None)
    return aprovados


def _outro_aluno_tao_parecido(norm: str, aprovado: Aluno, alunos: list[Aluno]) -> bool:
    """Algum OUTRO aluno da lista parece com o nome do arquivo tanto quanto
    (ou mais que) o aluno aprovado."""
    nota = fuzz.token_set_ratio(norm, aprovado.nome_norm)
    return any(a.email.casefold() != aprovado.email.casefold()
               and fuzz.token_set_ratio(norm, a.nome_norm) >= nota for a in alunos)


def _sugestoes_para(norm: str, alunos: list[Aluno]) -> list[tuple[Aluno, str]]:
    parciais = candidatos_nome_parcial(norm, alunos)
    if parciais:
        return [(a, "nome parcial" if len(parciais) == 1 else "nome parcial (varios: escolha 1)")
                for a in parciais]
    pontuados = sorted(((fuzz.token_set_ratio(norm, a.nome_norm), a) for a in alunos),
                       key=lambda t: t[0], reverse=True)
    return [(a, f"parecido {score:.0f}%") for score, a in pontuados[:2] if score >= SCORE_MINIMO_SUGESTAO]


def registrar_sugestoes(resultado: ResultadoConciliacao, alunos: list[Aluno], caminho: Path) -> int:
    """Acrescenta sugestões novas (aprovado vazio) para todo nome de arquivo
    que não é o nome exato de um aluno, em qualquer estado da conciliação.
    Nunca altera linhas existentes. Retorna quantas linhas novas."""
    caminho = Path(caminho)
    try:
        existentes = _ler(caminho)
    except CsvIlegivel as e:
        _emitir_aviso(f"nomes_aprovados: {e}; sugestoes novas nao gravadas (o arquivo ficou como esta).")
        return 0
    ja_tem = {(normalizar_nome(l.get("nome_no_arquivo", "")), l.get("aluno_email", "").casefold())
              for l in existentes}
    vistos: set[str] = set()
    novas: list[dict] = []
    nomes_exatos = {a.nome_norm for a in alunos}
    for item in resultado.itens:
        if not item.arquivo:
            continue
        # T28: vale para qualquer estado (ex.: SEM_CODIGO de pasta ainda não
        # aprovada), para nomes e pastas serem aprovados na mesma rodada.
        norm = normalizar_nome(item.pessoa)
        if not norm or norm in vistos or norm in nomes_exatos:
            continue
        if eh_folha_em_branco(norm):
            continue  # folha em branco: nunca sugerir aluno (decidir à mão)
        vistos.add(norm)
        # Bug 012: nome que já tem linha ganha sugestão para um aluno NOVO da
        # lista (o par nome/e-mail que já existe não se repete).
        for aluno, motivo in _sugestoes_para(norm, alunos):
            if (norm, aluno.email.casefold()) in ja_tem:
                continue
            novas.append({"nome_no_arquivo": item.pessoa, "aluno_nome": aluno.nome,
                          "aluno_email": aluno.email, "aprovado": "", "motivo": motivo})
    if novas:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        novo_arquivo = not caminho.is_file()
        garantir_quebra_final(caminho)
        with open(caminho, "a", encoding="utf-8-sig" if novo_arquivo else "utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
            if novo_arquivo:
                escritor.writeheader()
            escritor.writerows(novas)
    return len(novas)
