"""Fluxo de envio de teste (conta de teste).

T40: o modo teste usa o MESMO caminho da produção (conciliação com as
aprovações, tema genérico, revisão de nomes, contagem do dia, lote), só com
a conta de teste como único aluno, a pasta testes/redacoes_teste/ e arquivos
de aprovação próprios em testes/. Confirmação ENVIAR TESTE.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from modulos.base import tela

from modulos.base.config import NOME_CONTA_TESTE, Config, obter_email_teste
from modulos.base.progresso_relatorio import Progresso
from modulos.dados.conciliacao_completa import TEMAS_SITE_CSV, conciliar_com_aprovacoes, ler_codigos_site_csv
from modulos.dados.planilha_arquivos import Aluno, carregar_alunos
from modulos.envio.fluxo_envio_producao import executar_envio_producao


def executar_envio_teste(cfg: Config, progresso: Optional[Progresso] = None) -> int:
    """0 = tudo enviado/já enviado; 1 = parou num problema; 2 = cancelado.
    ``cfg`` já vem com a pasta e as aprovações de teste (configurar_modo_teste)."""
    email = obter_email_teste().strip()
    # T44: a "conta de teste" nunca pode ser o e-mail de um aluno de verdade
    if Path(cfg.planilha).is_file():
        try:
            reais = {a.id for a in carregar_alunos(cfg)}
        except Exception as e:  # T48: sem conferir, não envia
            tela.erro(f"Nao consegui ler a lista de alunos para conferir a conta de teste "
                      f"({type(e).__name__}). Nada foi enviado.")
            return 2
        if email.casefold() in reais:
            tela.erro("ESQUEMA_EMAIL_TESTE e o e-mail de um aluno da lista. Nada foi enviado.")
            return 2
    conciliacao = conciliar_com_aprovacoes(cfg, [Aluno(nome=NOME_CONTA_TESTE, email=email)],
                                           ler_codigos_site_csv(TEMAS_SITE_CSV))
    return executar_envio_producao(cfg, conciliacao.resultado, progresso, conta_teste=email)
