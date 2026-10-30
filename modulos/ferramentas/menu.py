"""Menu principal (T47): `python main.py` sem nada abre este menu.

M3: primeiro escolhe escola -> turma, mostra o resumo e pede s/n; o menu
fica só daquela turma ("Trocar escola ou turma" volta à escolha).

Cada opção só monta os argumentos e chama o mesmo ``main`` que os comandos
com flags usam (com ``--escola``/``--turma``), então o menu nunca pula uma
trava (confirmações digitadas, PRODUCAO_BLOQUEADA, ensaio só na conta de
teste) e nada da turma anterior é reaproveitado. Quem já sabe os comandos
continua podendo usar ``python main.py --revisar --escola X --turma Y`` etc.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from modulos.base import config as config_mod
from modulos.base import sobre, tela
from modulos.ferramentas.configuracoes import executar_configuracoes, resumo_navegador

Entrada = Callable[[str], str]

# (grupo, tecla, nome, ajuda curta): cada linha cabe em 80 colunas
OPCOES = [
    ("Preparar", "1", "Conferir as redações", "não envia nada"),
    ("Preparar", "2", "Revisar temas e nomes", "escolhe temas, confirma alunos"),
    ("Testar (nada vai para os alunos)", "3", "Ensaio com redações reais", "algumas reais → conta de teste"),
    ("Testar (nada vai para os alunos)", "4", "Modo teste", "conferir, revisar ou enviar"),
    ("Testar (nada vai para os alunos)", "5", "Conferir no site", "lê as contas dos alunos, não envia"),
    ("Enviar", "6", "Enviar para os alunos", "envio de verdade"),
    ("Enviar", "7", "Enviar as que faltam no site", "usa a conferência de hoje (5)"),
    ("Enviar", "8", "Resolver revisões manuais", "chegou no site? sim/não"),
    ("Ferramentas", "9", "Atualizar os temas do site", "só leitura"),
    ("Ferramentas", "10", "Desfazer uma renomeação", "volta os nomes de uma revisão"),
    ("Ferramentas", "11", "Arquivo morto", "guarda as pastas já enviadas"),
    ("Ferramentas", "12", "Primeiro uso / o que falta", "cria o que falta e explica"),
    ("Ferramentas", "13", "Configurações", ""),
    ("Ferramentas", "14", "Trocar escola ou turma", "outra turma da escola, ou outra escola"),
]
SEM_TURMA = ("4",)  # modo teste: conta de teste e testes/redacoes_teste, sem turma
NOVA = "<nova>"  # "n" na escolha de escola (nome inválido em pasta: nunca colide com uma escola)


def _perguntar(entrada: Entrada | None, texto: str) -> str:
    return tela.perguntar(texto, entrada)


def _sim(entrada: Entrada | None, texto: str) -> bool:
    return _perguntar(entrada, f"  {texto} (s/n): ").lower() in ("s", "sim")


def mostrar_menu(saida: Callable = print, turma: tuple[str, str] | None = None) -> None:
    tela.titulo("AUTOMAÇÃO DE REDAÇÕES  ·  " + (f"{turma[0]} / {turma[1]}" if turma else "menu"), saida)
    grupo_atual = None
    for grupo, tecla, nome, ajuda in OPCOES:
        if grupo != grupo_atual:
            tela.secao(grupo, saida)
            grupo_atual = grupo
        if tecla in ("6", "7") and config_mod.PRODUCAO_BLOQUEADA:
            ajuda = tela.c(f"{tela.SIMBOLOS['bloqueado']} bloqueado (só a conta de teste envia)", "bloqueado")
        elif tecla == "13":  # T52: mostra a escolha atual
            ajuda = tela.c(f"{resumo_navegador()} · escolas e turmas", "fraco")
        else:
            ajuda = tela.c(ajuda, "fraco")
        rotulo = f"{tecla})".rjust(3)  # 1) a 14) alinhados
        saida(f" {tela.c(rotulo, 'tecla')} {nome:<30} {ajuda}")
    saida("")
    saida(f" {tela.c(' 0)', 'tecla')} Sair")
    saida("")
    saida(tela.c(f"  {sobre.creditos()}", "fraco"))  # T53


def argumentos_da_opcao(opcao: str, entrada: Entrada | None = None,
                        pasta_relatorios: Path | None = None, saida: Callable = print) -> list[str] | None:
    """Argumentos do main para a opção escolhida (None = voltar ao menu)."""
    if opcao == "1":
        return []
    if opcao == "2":
        return ["--revisar"]
    if opcao == "3":
        n = _perguntar(entrada, "  Quantas redações no ensaio? [Enter = 3]: ") or "3"
        if not n.isdecimal() or int(n) < 1:
            tela.erro("Número inválido.", saida)
            return None
        if _sim(entrada, f"Enviar agora as {n} para a CONTA DE TESTE? (n = so mostrar quais iriam)"):
            return ["--ensaio", n, "--envio-real"]
        return ["--ensaio", n]
    if opcao == "4":
        # T55: a revisão da pasta de teste não tinha caminho pelo menu
        tela.menu([("Enter / c", "só conferir a pasta de teste"),
                   ("r", "revisar temas e nomes da pasta de teste"),
                   ("e", "enviar para a conta de teste")], saida)
        escolha = _perguntar(entrada, "  > ").lower()
        if escolha in ("", "c"):
            return ["--modo-teste"]
        if escolha == "r":
            return ["--modo-teste", "--revisar"]
        if escolha in ("e", "s"):
            return ["--modo-teste", "--envio-real"]
        tela.erro("Opção inválida.", saida)
        return None
    if opcao == "5":
        return ["--conferir-site"]
    if opcao == "6":
        if config_mod.PRODUCAO_BLOQUEADA:
            tela.bloqueado(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA, saida)
            return None
        # T57: o 1º envio de verdade deve ser pequeno (1 aluno, 1 redação)
        argumentos = ["--envio-real"]
        for flag, pergunta in (("--limite-alunos", "Quantos alunos desta vez? (Enter = todos): "),
                               ("--limite-redacoes", "Quantas redações no máximo? (Enter = todas): ")):
            n = _perguntar(entrada, f"  {pergunta}")
            if not n:
                continue
            if not n.isdecimal() or int(n) < 1:
                tela.erro("Número inválido: nada foi enviado.", saida)
                return None
            argumentos += [flag, n]
        return argumentos
    if opcao == "7":
        if config_mod.PRODUCAO_BLOQUEADA:
            tela.bloqueado(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA, saida)
            return None
        return ["--enviar-faltantes"]
    if opcao == "8":
        return ["--resolver"]
    if opcao == "9":
        return ["--analise-remota"]
    if opcao == "10":
        logs = sorted(Path(pasta_relatorios or config_mod.RAIZ / "relatorios").glob("renomeacoes_*.csv"),
                      reverse=True)[:9]
        if not logs:
            tela.info("Nenhuma renomeação para desfazer.", saida)
            return None
        for i, log in enumerate(logs, 1):
            saida(f"    {tela.c(f'{i})', 'tecla')} {log.name}")
        escolha = _perguntar(entrada, "  Qual desfazer? (Enter = nenhuma): ")
        if escolha.isdecimal() and 1 <= int(escolha) <= len(logs):
            return ["--desfazer-renomeacao", str(logs[int(escolha) - 1])]
        return None
    if opcao == "11":
        return ["--arquivar"]
    if opcao == "12":
        return ["--preparar"]
    if opcao == "13":
        from modulos.ferramentas.estrutura import executar_configuracoes_e_estrutura
        executar_configuracoes_e_estrutura(entrada=entrada, saida=saida)  # navegador, escolas e turmas (#35)
        return None
    tela.erro("Opção inválida.", saida)
    return None


def _escolher(itens: list[str], o_que: str, entrada: Entrada | None, saida: Callable,
              voltar: bool = False, nova: bool = False) -> str | None:
    """Item escolhido, "v" (voltar), ``NOVA`` ("n", só com ``nova``) ou None (cancelar)."""
    tela.secao(o_que, saida)
    for i, item in enumerate(itens, 1):
        saida(f"    {tela.c(f'{i})', 'tecla')} {item}")
    extra = ("v = voltar, " if voltar else "") + ("n = nova escola/turma, " if nova else "")
    while True:
        r = _perguntar(entrada, f"  {o_que} ({extra}Enter = cancelar): ").lower()
        if not r or r == "0":
            return None
        if voltar and r == "v":
            return "v"
        if nova and r == "n":
            return NOVA
        if r.isdecimal() and 1 <= int(r) <= len(itens):
            return itens[int(r) - 1]
        tela.erro("Opção inválida.", saida)


def resumo_turma(escola: str, turma: str, saida: Callable = print) -> bool:
    """Escola, turma, planilha, nº de alunos e temas. False = turma com problema."""
    from modulos.base.turma import aplicar_turma
    from modulos.dados.planilha_arquivos import carregar_alunos, descobrir_pastas
    try:
        cfg = config_mod.carregar_config()
        aplicar_turma(cfg, escola, turma)
        alunos = carregar_alunos(cfg)
    except Exception as e:  # noqa: BLE001 - mostra e deixa escolher outra
        tela.erro(f"Turma com problema: {type(e).__name__}: {e}", saida)
        return False
    temas = [p.name for p in descobrir_pastas(cfg)]
    tela.secao("Turma escolhida", saida)
    tela.info(f"Escola: {escola}  ·  Turma: {turma}", saida)
    tela.info(f"Lista de alunos: {tela.caminho(cfg.planilha)}", saida)
    tela.contagens([("Alunos na lista", len(alunos), "ok"),
                    ("Alunos sem senha (não entram no site)", sum(1 for a in alunos if not a.senha), "aviso"),
                    ("Pastas de tema", len(temas), "ok")], saida)
    for tema in temas:
        tela.status("fraco", tema, saida, recuo=4)
    return True


def escolher_turma(entrada: Entrada | None = None, saida: Callable = print,
                   escola_fixa: str | None = None) -> tuple[str, str] | None:
    """Escola -> turma -> resumo -> s/n. None = cancelou (ou não há turma).
    ``escola_fixa``: começa pelas turmas dessa escola (``v`` volta à escolha de escola)."""
    from modulos.base.turma import listar_escolas, listar_turmas
    tela.titulo("AUTOMAÇÃO DE REDAÇÕES  ·  escolha a turma", saida)
    while True:
        escolas = listar_escolas()
        if not escolas:
            if entrada is None and sys.stdin.isatty():  # primeiro uso guiado (issue #34); só com pessoa no teclado
                from modulos.ferramentas.assistente_inicial import executar_assistente
                if executar_assistente():
                    continue
                return None
            tela.aviso("Nenhuma turma encontrada. Cada turma é uma pasta "
                       f"\"{config_mod.PASTA_REDACOES}/<Escola>/<Turma>/\" com alunos.csv.", saida)
            tela.comando('python main.py --preparar --escola "<Escola>" --turma "<Turma>"', "cria uma turma", saida)
            return None
        escola = escola_fixa if escola_fixa in escolas else _escolher(escolas, "Escola", entrada, saida, nova=True)
        escola_fixa = None
        if escola == NOVA:
            _criar_estrutura(entrada, saida)
            continue
        if escola is None:
            return None
        turma = _escolher(listar_turmas(escola), f"Turma de {escola}", entrada, saida, voltar=True)
        if turma is None:
            return None
        if turma != "v" and resumo_turma(escola, turma, saida) and _sim(entrada, "Usar esta turma?"):
            return escola, turma


def _criar_estrutura(entrada: Entrada | None, saida: Callable) -> None:
    """"n" na escolha de escola: cria escola ou turma sem sair do menu (mesmas perguntas do menu 13)."""
    from modulos.ferramentas import estrutura
    tela.menu([("e", "nova escola (com as turmas dela)"), ("t", "nova turma em uma escola que já existe")], saida)
    qual = _perguntar(entrada, "  > ").lower()
    if qual == "e":
        estrutura.adicionar_escola(entrada, saida)
    elif qual == "t":
        estrutura.adicionar_turma(entrada, saida)


def oferecer_temas(turma: tuple[str, str], main: Callable[[list[str]], int], entrada: Entrada | None = None,
                   saida: Callable = print) -> bool:
    """Sem a lista de temas do site (``dados/temas_site.csv``, uma só para todas as turmas): oferece lê-la agora
    (o mesmo caminho do menu 9, com o ANALISAR). ``turma`` só diz em qual turma o log da leitura fica."""
    from modulos.dados.conciliacao_completa import TEMAS_SITE_CSV
    try:  # roda antes do laço do menu: um erro aqui não pode fechar o script ao abrir
        if TEMAS_SITE_CSV.is_file():
            return False
        tela.aviso("Ainda não existe a lista de temas do site (vale para todas as turmas).", saida)
        if not _sim(entrada, "Ler os temas do site agora (só leitura, conta de teste)?"):
            return False
        main(["--analise-remota", "--escola", turma[0], "--turma", turma[1]])
    except KeyboardInterrupt:
        tela.aviso("Interrompido (Ctrl+C).", saida)
    except Exception as e:  # noqa: BLE001 - o menu segue; os detalhes ficam no log
        import logging
        logging.getLogger("automacao_redacoes").exception("Erro ao oferecer a leitura dos temas")
        tela.erro(f"Não consegui ler os temas agora: {type(e).__name__}: {e}", saida)
        return False
    return True


def executar_menu(main: Callable[[list[str]], int], entrada: Entrada | None = None,
                  saida: Callable = print, turma: tuple[str, str] | None = None) -> int:
    """Escolhe a turma e mostra o menu até a pessoa escolher 0 (ou fechar a entrada)."""
    turma = turma or escolher_turma(entrada, saida)
    if not turma:
        return 0
    interativo = entrada is None and sys.stdin.isatty()  # verificação automática só com pessoa no teclado
    if interativo:
        oferecer_temas(turma, main, entrada, saida)
    while True:
        mostrar_menu(saida, turma)
        opcao = _perguntar(entrada, "\n  Escolha uma opção: ")
        if opcao in ("0", ""):
            return 0
        if opcao == "14":  # trocar turma: o main da próxima opção só recebe a nova
            tela.menu([("Enter / t", "outra turma desta escola"), ("e", "outra escola")], saida)
            qual = _perguntar(entrada, "  > ").lower()
            turma = escolher_turma(entrada, saida, turma[0] if qual in ("", "t") else None) or turma
            if interativo:
                oferecer_temas(turma, main, entrada, saida)
            continue
        try:
            from modulos.base.turma import raiz_redacoes  # a turma é conferida pelo main
            relatorios = raiz_redacoes() / turma[0] / turma[1] / "relatorios"
            # Bug 017: as perguntas da opção também ficam dentro do try
            argumentos = argumentos_da_opcao(opcao, entrada, relatorios, saida=saida)
            if argumentos is not None:
                main(argumentos + ([] if opcao in SEM_TURMA else ["--escola", turma[0], "--turma", turma[1]]))
        except KeyboardInterrupt:
            tela.aviso("Interrompido (Ctrl+C).", saida)
        except Exception as e:  # o menu não fecha por causa de um erro
            import logging
            logging.getLogger("automacao_redacoes").exception("Erro no menu (opcao %s)", opcao)
            tela.erro(f"Erro inesperado: {type(e).__name__}: {e}", saida)
            tela.status("fraco", "Detalhes em logs/automacao.log.", saida)
        if _perguntar(entrada, "\n  Enter para voltar ao menu (0 = sair): ") == "0":
            return 0
