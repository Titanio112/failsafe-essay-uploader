"""Menu principal (T47): `python main.py` sem nada abre este menu.

Cada opção só monta os argumentos e chama o mesmo ``main`` que os comandos
com flags usam, então o menu nunca pula uma trava (confirmações digitadas,
PRODUCAO_BLOQUEADA, ensaio só na conta de teste). Quem já sabe os comandos
continua podendo usar ``python main.py --revisar`` etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from modulos.base import config as config_mod
from modulos.base import tela

Entrada = Callable[[str], str]

# (grupo, tecla, nome, ajuda curta): cada linha cabe em 80 colunas
OPCOES = [
    ("Preparar", "1", "Conferir as redações", "não envia nada"),
    ("Preparar", "2", "Revisar temas e nomes", "escolhe temas, confirma alunos"),
    ("Testar na conta de teste", "3", "Ensaio com redações reais", "algumas reais → conta de teste"),
    ("Testar na conta de teste", "4", "Modo teste", "pasta testes/redacoes_teste"),
    ("Enviar", "5", "Enviar para os alunos", "envio de verdade"),
    ("Enviar", "6", "Resolver revisões manuais", "chegou no site? sim/não"),
    ("Ferramentas", "7", "Atualizar os temas do site", "só leitura"),
    ("Ferramentas", "8", "Desfazer uma renomeação", "volta os nomes de uma revisão"),
    ("Ferramentas", "9", "Primeiro uso / o que falta", "cria o que falta e explica"),
]


def _perguntar(entrada: Entrada | None, texto: str) -> str:
    return tela.perguntar(texto, entrada)


def _sim(entrada: Entrada | None, texto: str) -> bool:
    return _perguntar(entrada, f"  {texto} (s/n): ").lower() in ("s", "sim")


def mostrar_menu(saida: Callable = print) -> None:
    tela.titulo("AUTOMAÇÃO DE REDAÇÕES  ·  menu", saida)
    grupo_atual = None
    for grupo, tecla, nome, ajuda in OPCOES:
        if grupo != grupo_atual:
            tela.secao(grupo, saida)
            grupo_atual = grupo
        if tecla == "5" and config_mod.PRODUCAO_BLOQUEADA:
            ajuda = tela.c(f"{tela.SIMBOLOS['bloqueado']} bloqueado (só a conta de teste envia)", "bloqueado")
        else:
            ajuda = tela.c(ajuda, "fraco")
        saida(f"  {tela.c(tecla + ')', 'tecla')} {nome:<30} {ajuda}")
    saida("")
    saida(f"  {tela.c('0)', 'tecla')} Sair")


def argumentos_da_opcao(opcao: str, entrada: Entrada | None = None,
                        pasta_relatorios: Path | None = None, saida: Callable = print) -> list[str] | None:
    """Argumentos do main para a opção escolhida (None = voltar ao menu)."""
    if opcao == "1":
        return []
    if opcao == "2":
        return ["--revisar"]
    if opcao == "3":
        n = _perguntar(entrada, "  Quantas redações no ensaio? [Enter = 3]: ") or "3"
        if not n.isdigit() or int(n) < 1:
            tela.erro("Número inválido.", saida)
            return None
        if _sim(entrada, f"Enviar agora as {n} para a CONTA DE TESTE? (n = so mostrar quais iriam)"):
            return ["--ensaio", n, "--envio-real"]
        return ["--ensaio", n]
    if opcao == "4":
        if _sim(entrada, "Enviar a pasta de teste agora? (n = so conferir)"):
            return ["--modo-teste", "--envio-real"]
        return ["--modo-teste"]
    if opcao == "5":
        if config_mod.PRODUCAO_BLOQUEADA:
            tela.bloqueado(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA, saida)
            return None
        return ["--envio-real"]
    if opcao == "6":
        return ["--resolver"]
    if opcao == "7":
        return ["--analise-remota"]
    if opcao == "8":
        logs = sorted(Path(pasta_relatorios or config_mod.RAIZ / "relatorios").glob("renomeacoes_*.csv"),
                      reverse=True)[:9]
        if not logs:
            tela.info("Nenhuma renomeação para desfazer.", saida)
            return None
        for i, log in enumerate(logs, 1):
            saida(f"    {tela.c(f'{i})', 'tecla')} {log.name}")
        escolha = _perguntar(entrada, "  Qual desfazer? (Enter = nenhuma): ")
        if escolha.isdigit() and 1 <= int(escolha) <= len(logs):
            return ["--desfazer-renomeacao", str(logs[int(escolha) - 1])]
        return None
    if opcao == "9":
        return ["--preparar"]
    tela.erro("Opção inválida.", saida)
    return None


def executar_menu(main: Callable[[list[str]], int], entrada: Entrada | None = None,
                  saida: Callable = print) -> int:
    """Mostra o menu até a pessoa escolher 0 (ou fechar a entrada)."""
    while True:
        mostrar_menu(saida)
        opcao = _perguntar(entrada, "\n  Escolha uma opção: ")
        if opcao in ("0", ""):
            return 0
        argumentos = argumentos_da_opcao(opcao, entrada, saida=saida)
        if argumentos is not None:
            try:
                main(argumentos)
            except KeyboardInterrupt:
                tela.aviso("Interrompido (Ctrl+C).", saida)
            except Exception as e:  # o menu não fecha por causa de um erro
                import logging
                logging.getLogger("automacao_redacoes").exception("Erro no menu (opcao %s)", opcao)
                tela.erro(f"Erro inesperado: {type(e).__name__}: {e}", saida)
                tela.status("fraco", "Detalhes em logs/automacao.log.", saida)
        if _perguntar(entrada, "\n  Enter para voltar ao menu (0 = sair): ") == "0":
            return 0
