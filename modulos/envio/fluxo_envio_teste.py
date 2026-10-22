"""Fluxo de envio de teste (conta de teste).

T40: o modo teste usa o MESMO caminho da produção (conciliação com as
aprovações, tema genérico, revisão de nomes, contagem do dia, lote), só com
a conta de teste como único aluno, a pasta testes/redacoes_teste/ e arquivos
de aprovação próprios em testes/. Confirmação ENVIAR TESTE.
"""

from __future__ import annotations

from typing import Optional

from modulos.base.config import NOME_CONTA_TESTE, Config, obter_email_teste
from modulos.base.progresso_relatorio import Progresso
from modulos.dados.conciliacao_completa import TEMAS_SITE_CSV, conciliar_com_aprovacoes, ler_codigos_site_csv
from modulos.dados.planilha_arquivos import Aluno
from modulos.envio.fluxo_envio_producao import executar_envio_producao


def executar_envio_teste(cfg: Config, progresso: Optional[Progresso] = None) -> int:
    """0 = tudo enviado/já enviado; 1 = parou num problema; 2 = cancelado.
    ``cfg`` já vem com a pasta e as aprovações de teste (configurar_modo_teste)."""
    email = obter_email_teste()
    conciliacao = conciliar_com_aprovacoes(cfg, [Aluno(nome=NOME_CONTA_TESTE, email=email)],
                                           ler_codigos_site_csv(TEMAS_SITE_CSV))
    return executar_envio_producao(cfg, conciliacao.resultado, progresso, conta_teste=email)
