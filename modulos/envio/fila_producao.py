"""Monta o lote de envio de produção a partir da conciliação (sem navegador).

Regras (T24):
- só itens EXATO_UNICO da conciliação;
- nunca reenviar o que o banco registra como ENVIADO, JA_ENVIADO ou
  REVISAO_MANUAL (ERRO pode tentar de novo: não houve clique);
- vários arquivos do mesmo aluno no mesmo código entram se estiverem em
  pastas diferentes (T35: ex. tema genérico 000); o envio confere pela
  contagem do dia; na mesma pasta a conciliação já mandou para revisão;
- T44: a mesma foto (mesmo conteúdo) não entra duas vezes no lote, nem
  volta se o banco já a registrou para o aluno com outro nome/pasta;
- sem limite de redações por aluno (Antônio, 22/10);
- ``limite_alunos`` / ``limite_redacoes`` cortam o lote no fim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from modulos.envio.fila_teste import ItemFilaTeste, hash_do_arquivo
from modulos.dados.planilha_arquivos import Aluno, ResultadoConciliacao
from modulos.base.progresso_relatorio import Progresso, ENVIADO, JA_ENVIADO, REVISAO_MANUAL

ESTADOS_SEM_REENVIO = {ENVIADO, JA_ENVIADO, REVISAO_MANUAL}


@dataclass
class LoteAluno:
    """Itens de um aluno a enviar nesta execução, na ordem."""
    aluno: Aluno
    itens: list[ItemFilaTeste] = field(default_factory=list)


def montar_lote_producao(
    resultado: ResultadoConciliacao,
    pasta_raiz: Path,
    progresso: Optional[Progresso] = None,
    limite_alunos: Optional[int] = None,
    limite_redacoes: Optional[int] = None,
) -> tuple[list[LoteAluno], list[tuple[str, str]]]:
    """Retorna (lotes por aluno, ignorados=[(chave, motivo)])."""
    lotes: dict[str, LoteAluno] = {}
    ignorados: list[tuple[str, str]] = []
    vistos: set[tuple[str, str, str]] = set()
    conteudos: dict[str, str] = {}  # T44: hash -> chave já no lote

    fila = sorted(resultado.fila_validada(), key=lambda i: (i.aluno.nome_norm, i.pasta, i.arquivo))
    total_por_tema: dict[tuple[str, str], int] = {}
    for item in fila:
        if item.codigo_tema:
            chave_tema = (item.aluno.id, item.codigo_tema)
            total_por_tema[chave_tema] = total_por_tema.get(chave_tema, 0) + 1
    for item in fila:
        aluno, codigo, chave = item.aluno, item.codigo_tema, item.chave
        caminho = Path(pasta_raiz) / item.pasta / item.arquivo
        registro = progresso.obter(aluno.id, chave) if progresso else None

        if not codigo:
            ignorados.append((chave, "sem codigo de tema (revisao manual)"))
        elif (aluno.id, codigo, item.pasta) in vistos:
            ignorados.append((chave, f"codigo {codigo} repetido para o aluno na mesma pasta (revisao manual)"))
        elif registro and registro["estado"] in ESTADOS_SEM_REENVIO:
            motivo = f"ja registrado como {registro['estado']}"
            # T57: mesmo nome de pasta/arquivo, foto diferente = redação NOVA com
            # nome repetido (pasta reaproveitada). Continua fora (seguro), mas diz por quê.
            if registro.get("hash_arquivo") and caminho.is_file() and hash_do_arquivo(caminho) != registro["hash_arquivo"]:
                motivo += "; a FOTO E OUTRA (nome repetido de redacao ja enviada): use um nome de pasta novo"
            ignorados.append((chave, motivo))
        elif not caminho.is_file():
            ignorados.append((chave, "arquivo nao encontrado"))
        elif (h := hash_do_arquivo(caminho)) in conteudos:
            ignorados.append((chave, f"mesma foto que {conteudos[h]} (copia? revisao manual)"))
        elif progresso and (antigo := progresso.registro_do_conteudo(aluno.id, h, chave)):
            ignorados.append((chave, f"mesma foto ja registrada como {antigo['estado']} em {antigo['arquivo']}"))
        elif progresso and (outro := progresso.conteudo_de_outro_aluno(aluno.id, h)):
            ignorados.append((chave, f"mesma foto ja registrada para OUTRO aluno como {outro['estado']} "
                                     f"em {outro['arquivo']} (nome trocado? revisao manual)"))
        else:
            vistos.add((aluno.id, codigo, item.pasta))
            conteudos[h] = chave
            lote = lotes.setdefault(aluno.id, LoteAluno(aluno))
            lote.itens.append(ItemFilaTeste(item.pasta, item.arquivo, codigo, caminho, chave,
                                            total_mesmo_tema=total_por_tema[(aluno.id, codigo)],
                                            hash_arquivo=h))

    resultado_lotes = [lote for lote in lotes.values() if lote.itens]
    if limite_alunos is not None:
        resultado_lotes = resultado_lotes[:max(limite_alunos, 0)]
    if limite_redacoes is not None:
        restante = max(limite_redacoes, 0)
        cortados = []
        for lote in resultado_lotes:
            if restante <= 0:
                break
            cortados.append(LoteAluno(lote.aluno, lote.itens[:restante]))
            restante -= len(cortados[-1].itens)
        resultado_lotes = cortados

    return resultado_lotes, ignorados
