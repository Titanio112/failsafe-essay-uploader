"""Ensaio com redações reais na conta de teste (T42).

Usa a conciliação de produção de verdade (lista real de alunos, pasta
"Redações plataforma", aprovações de dados/) e escolhe uma amostra da fila
validada, mas TODA a amostra vai para a conta de teste. Nenhuma conta de
aluno é aberta: o lote só tem a conta de teste e passa pela mesma trava
do modo teste (ENVIAR TESTE, ESQUEMA_SENHA_TESTE).

Serve para testar, antes de liberar a produção, as fotos reais, os temas
reais (inclusive o genérico 000) e as aprovações feitas no --revisar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from modulos.base.progresso_relatorio import Progresso
from modulos.dados.planilha_arquivos import Aluno, ResultadoConciliacao
from modulos.envio.fila_producao import ESTADOS_SEM_REENVIO, LoteAluno
from modulos.envio.fila_teste import ItemFilaTeste

QUANTIDADE_PADRAO = 3
PREFIXO_CHAVE = "ensaio/"


def montar_lote_ensaio(
    resultado: ResultadoConciliacao,
    pasta_raiz: Path,
    conta_teste: Aluno,
    progresso: Optional[Progresso] = None,
    quantidade: int = QUANTIDADE_PADRAO,
) -> list[LoteAluno]:
    """Uma pasta de cada vez (rodízio), para a amostra cobrir temas
    diferentes. Item já ENVIADO/JA_ENVIADO/REVISAO_MANUAL no ensaio não volta.

    Chave no banco: "ensaio/pasta/arquivo", na conta de teste; o registro
    do aluno real nunca é tocado. ``total_mesmo_tema`` = o que o caderno já
    tem hoje na conta de teste naquele código + o que esta amostra manda,
    para a checagem por contagem (T35) bater com o site."""
    por_pasta: dict[str, list] = {}
    for item in sorted(resultado.fila_validada(), key=lambda i: (i.pasta, i.arquivo)):
        if not item.codigo_tema:
            continue
        chave = PREFIXO_CHAVE + item.chave
        registro = progresso.obter(conta_teste.id, chave) if progresso else None
        if registro and registro["estado"] in ESTADOS_SEM_REENVIO:
            continue
        if not (Path(pasta_raiz) / item.pasta / item.arquivo).is_file():
            continue
        por_pasta.setdefault(item.pasta, []).append(item)

    escolhidos = []
    filas = [list(itens) for _, itens in sorted(por_pasta.items())]
    while len(escolhidos) < max(quantidade, 0) and any(filas):
        for fila in filas:
            if fila and len(escolhidos) < quantidade:
                escolhidos.append(fila.pop(0))

    if not escolhidos:
        return []
    por_codigo: dict[str, int] = {}
    for item in escolhidos:
        por_codigo[item.codigo_tema] = por_codigo.get(item.codigo_tema, 0) + 1
    ja_hoje = {codigo: (progresso.enviados_hoje(conta_teste.id, codigo) if progresso else 0)
               for codigo in por_codigo}
    itens = [
        ItemFilaTeste(item.pasta, item.arquivo, item.codigo_tema,
                      Path(pasta_raiz) / item.pasta / item.arquivo, PREFIXO_CHAVE + item.chave,
                      total_mesmo_tema=ja_hoje[item.codigo_tema] + por_codigo[item.codigo_tema])
        for item in escolhidos
    ]
    return [LoteAluno(conta_teste, itens)]
