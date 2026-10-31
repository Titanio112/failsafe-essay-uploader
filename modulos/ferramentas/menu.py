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

# (grupo, tecla mostrada, ação, nome, ajuda curta). A "ação" é o número interno que ``argumentos_da_opcao`` entende
# (não muda com a ordem do menu). Mais usadas primeiro; cada linha cabe em 80 colunas.
OPCOES = [
    ("Preparar", "1", "1", "Conferir redações", "não envia nada"),
    ("Preparar", "2", "2", "Revisar temas e nomes", "escolhe temas, confirma alunos"),
    ("Preparar", "3", "5", "Conferir contas no site", "login, nome e já enviadas; só lê"),
    ("Enviar", "4", "6", "Enviar para os alunos", "envio de verdade"),
    ("Enviar", "5", "7", "Enviar as que faltam", "só o que falta no site"),
    ("Manutenção", "6", "8", "Resolver revisões manuais", "chegou no site? sim/não"),
    ("Manutenção", "7", "9", "Atualizar temas do site", "só leitura"),
    ("Manutenção", "8", "10", "Desfazer renomeação", "volta os nomes de uma revisão"),
    ("Ferramentas", "9", "14", "Trocar escola ou turma", ""),
    ("Ferramentas", "10", "11", "Arquivo morto", "guarda as pastas já enviadas"),
    ("Ferramentas", "11", "13", "Configurações e turmas", ""),
    ("Ferramentas", "12", "12", "Primeiro uso / o que falta", "cria o que falta e explica"),
    ("Ferramentas", "13", "T", "Testes", "ensaio e modo teste (conta de teste)"),
]
ACAO_DA_TECLA = {tecla: acao for _, tecla, acao, _, _ in OPCOES}
ENVIAR = ("6", "7")  # ações que só abrem depois de Preparar (e com a produção liberada)
MENSAGEM_PREPARAR = "conclua as etapas de Preparar primeiro"
SEM_TURMA = ("4",)  # ação do modo teste: conta de teste e testes/redacoes_teste, sem turma
NOVA = "<nova>"  # "n" na escolha de escola (nome inválido em pasta: nunca colide com uma escola)


def _perguntar(entrada: Entrada | None, texto: str) -> str:
    return tela.perguntar(texto, entrada)


def _sim(entrada: Entrada | None, texto: str) -> bool:
    return _perguntar(entrada, f"  {texto} (s/n): ").lower() in ("s", "sim")


def preparacao_da_turma(turma: tuple[str, str]) -> tuple[bool, str]:
    """(ok, motivo): a trava do Enviar no menu. Só libera com a conferência no site de HOJE desta turma completa."""
    from modulos.base.turma import raiz_redacoes
    from modulos.site.conferencia_site import preparacao_concluida
    try:
        return preparacao_concluida(raiz_redacoes() / turma[0] / turma[1] / "relatorios", f"{turma[0]}/{turma[1]}")
    except Exception:  # noqa: BLE001 - na dúvida, fica travado
        return False, "não consegui ler a conferência de hoje"


def mostrar_menu(saida: Callable = print, turma: tuple[str, str] | None = None) -> None:
    tela.titulo("AUTOMAÇÃO DE REDAÇÕES  ·  " + (f"{turma[0]} / {turma[1]}" if turma else "menu"), saida)
    preparada = preparacao_da_turma(turma)[0] if turma else True  # sem turma (testes do desenho) não há o que travar
    grupo_atual = None
    for grupo, tecla, acao, nome, ajuda in OPCOES:
        if grupo != grupo_atual:
            tela.secao(grupo, saida)
            grupo_atual = grupo
        rotulo = f"{tecla})".rjust(3)  # 1) a 13) alinhados
        if acao in ENVIAR and not preparada:  # trava visual: cinza e o aviso (a recusa de verdade está em executar_menu)
            saida(f" {tela.c(rotulo, 'fraco')} {tela.c(nome, 'fraco')}")
            aviso = f"{tela.SIMBOLOS['bloqueado']} bloqueado ({MENSAGEM_PREPARAR})"
            saida(f"       {tela.c(aviso, 'fraco')}")
            continue
        if acao in ENVIAR and config_mod.PRODUCAO_BLOQUEADA:
            ajuda = tela.c(f"{tela.SIMBOLOS['bloqueado']} bloqueado (só a conta de teste envia)", "bloqueado")
        elif acao == "13":  # T52: mostra a escolha atual
            ajuda = tela.c(f"{resumo_navegador()} · escolas e turmas", "fraco")
        else:
            ajuda = tela.c(ajuda, "fraco")
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
    if opcao == "T":  # Ferramentas > Testes: só para quem está desenvolvendo ou treinando
        tela.menu([("1", "Ensaio: algumas redações reais → conta de teste"),
                   ("2", "Modo teste: conferir, revisar ou enviar (conta de teste)")], saida)
        escolha = _perguntar(entrada, "  > ")
        if escolha in ("1", "2"):
            return argumentos_da_opcao("3" if escolha == "1" else "4", entrada, pasta_relatorios, saida)
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
            tela.comando('python main.py --preparar --escola "<Escola>" --turma "<Turma>"', "cria uma turma", saida,
                         sempre=True)  # sem terminal não há menu para guiar
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


def verificar_turma_ao_abrir(turma: tuple[str, str], main: Callable[[list[str]], int],
                             entrada: Entrada | None = None, saida: Callable = print) -> None:
    """O que o menu confere sozinho ao abrir uma turma (só com pessoa no teclado): se há redações e se há temas."""
    from modulos.ferramentas.guia_redacoes import avisar_se_sem_redacoes
    try:  # roda antes do laço do menu: um erro aqui não pode fechar o script ao abrir
        avisar_se_sem_redacoes(*turma, entrada, saida)
    except Exception as e:  # noqa: BLE001 - o menu segue; os detalhes ficam no log
        import logging
        logging.getLogger("automacao_redacoes").exception("Erro ao verificar as redações da turma")
        tela.erro(f"Não consegui olhar a pasta de redações agora: {type(e).__name__}: {e}", saida)
    oferecer_temas(turma, main, entrada, saida)


def proximo_passo(argumentos: list[str], turma: tuple[str, str], main: Callable[[list[str]], int],
                  entrada: Entrada | None = None, saida: Callable = print) -> None:
    """Depois de uma etapa de Preparar, oferece a seguinte: Conferir -> (pendências) Revisão -> Conferir de novo ->
    contas no site. Só com pessoa no teclado; cada etapa tem as confirmações dela (issue #52)."""
    from modulos.base import pendencias
    da_turma = ["--escola", turma[0], "--turma", turma[1]]
    for _ in range(6):  # Conferir <-> Revisão pode repetir; 6 voltas bastam
        if argumentos == []:
            if pendencias.revisao_pendente:
                pergunta, proximo = "Encontrei pendências. Deseja abrir a Revisão agora?", ["--revisar"]
            else:
                pergunta, proximo = "Tudo certo nas pastas. Deseja conferir as contas no site agora?", ["--conferir-site"]
        elif argumentos == ["--revisar"]:
            pergunta, proximo = "Revisão concluída. Deseja conferir as redações de novo, para ver se não sobrou nada?", []
        else:
            return
        if not _sim(entrada, pergunta):
            return
        try:
            main(proximo + da_turma)
        except KeyboardInterrupt:
            tela.aviso("Interrompido (Ctrl+C).", saida)
            return
        except Exception as e:  # noqa: BLE001 - o menu segue; os detalhes ficam no log
            import logging
            logging.getLogger("automacao_redacoes").exception("Erro no passo seguinte do menu")
            tela.erro(f"Erro inesperado: {type(e).__name__}: {e}", saida)
            return
        argumentos = proximo


def executar_menu(main: Callable[[list[str]], int], entrada: Entrada | None = None,
                  saida: Callable = print, turma: tuple[str, str] | None = None) -> int:
    """Escolhe a turma e mostra o menu até a pessoa escolher 0 (ou fechar a entrada)."""
    anterior = tela.DICAS_DE_COMANDO
    tela.DICAS_DE_COMANDO = False  # quem usa o menu não digita "python main.py ..."
    try:
        return _executar_menu(main, entrada, saida, turma)
    finally:
        tela.DICAS_DE_COMANDO = anterior


def _executar_menu(main: Callable[[list[str]], int], entrada: Entrada | None,
                   saida: Callable, turma: tuple[str, str] | None) -> int:
    turma = turma or escolher_turma(entrada, saida)
    if not turma:
        return 0
    interativo = entrada is None and sys.stdin.isatty()  # verificação automática só com pessoa no teclado
    if interativo:
        verificar_turma_ao_abrir(turma, main, entrada, saida)
    while True:
        mostrar_menu(saida, turma)
        opcao = _perguntar(entrada, "\n  Escolha uma opção: ")
        if opcao in ("0", ""):
            return 0
        acao = ACAO_DA_TECLA.get(opcao, "?")  # tecla mostrada -> ação interna ("?" = inválida)
        if acao == "14":  # trocar turma: o main da próxima opção só recebe a nova
            tela.menu([("Enter / t", "outra turma desta escola"), ("e", "outra escola")], saida)
            qual = _perguntar(entrada, "  > ").lower()
            turma = escolher_turma(entrada, saida, turma[0] if qual in ("", "t") else None) or turma
            if interativo:
                verificar_turma_ao_abrir(turma, main, entrada, saida)
            continue
        try:
            from modulos.base.turma import raiz_redacoes  # a turma é conferida pelo main
            relatorios = raiz_redacoes() / turma[0] / turma[1] / "relatorios"
            # Bug 017: as perguntas da opção também ficam dentro do try
            preparada, motivo = preparacao_da_turma(turma) if acao in ENVIAR else (True, "")
            if not preparada:  # a trava de verdade; o desenho do menu só avisa
                tela.bloqueado(f"Enviar bloqueado: {MENSAGEM_PREPARAR} ({motivo}).", saida)
                argumentos = None
            else:
                argumentos = argumentos_da_opcao(acao, entrada, relatorios, saida=saida)
            if argumentos is not None:
                sem_turma = "--modo-teste" in argumentos  # modo teste não usa turma
                main(argumentos + ([] if sem_turma else ["--escola", turma[0], "--turma", turma[1]]))
                if interativo and not sem_turma:
                    proximo_passo(argumentos, turma, main, entrada, saida)
        except KeyboardInterrupt:
            tela.aviso("Interrompido (Ctrl+C).", saida)
        except Exception as e:  # o menu não fecha por causa de um erro
            import logging
            logging.getLogger("automacao_redacoes").exception("Erro no menu (opcao %s)", opcao)
            tela.erro(f"Erro inesperado: {type(e).__name__}: {e}", saida)
            tela.status("fraco", "Detalhes em logs/automacao.log.", saida)
        if _perguntar(entrada, "\n  Enter para voltar ao menu (0 = sair): ") == "0":
            return 0
