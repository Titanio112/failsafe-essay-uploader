"""CLI: orquestracao. Padrao: dry-run. Entramos como aluno (e-mail/senha do aluno)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Configuração de encoding para stdout e stderr
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from modulos.base import config as config_mod
from modulos.base import pendencias, tela
from modulos.base.config import (
    NOME_CONTA_TESTE,
    carregar_config,
    configurar_modo_teste,
    obter_email_teste,
)
from modulos.envio.ensaio import QUANTIDADE_PADRAO, montar_lote_ensaio
from modulos.dados.planilha_arquivos import Aluno, PlanilhaError, carregar_alunos
from modulos.base.progresso_relatorio import (
    Progresso,
    configurar_logging,
    gerar_fila_dry_run,
    gerar_relatorio_conciliacao,
)
from modulos.envio.fluxo_envio_teste import executar_envio_teste
from modulos.envio.fluxo_envio_producao import executar_envio_producao
from modulos.site.analise_remota import executar_analise_remota
from modulos.ferramentas.revisao_interativa import desfazer_renomeacoes, executar_revisao
from modulos.ferramentas.primeiro_uso import mostrar_guia, preparar
from modulos.dados.conciliacao_completa import (  # noqa: F401 (ler_codigos_site_csv: testes usam main.)
    TEMAS_SITE_CSV,
    conciliar_com_aprovacoes,
    ler_codigos_site_csv,
)
from modulos.dados.nomes_aprovados import registrar_sugestoes
from modulos.dados.normalizacao import normalizar_nome
from modulos.dados.sugestao_temas import (
    SCORE_PROVAVEL,
    ler_temas_site,
    registrar_sugestoes_pasta,
    sugerir_codigos,
)


def _mostrar_sugestoes(resultado, alunos, arquivos, arquivo_nomes, arquivo_pastas, codigos_pasta,
                       revisar: str = "python main.py --revisar") -> None:
    """Sugestões para o humano resolver (T26/T28): nomes e códigos de tema. Só sugere."""
    novas = registrar_sugestoes(resultado, alunos, arquivo_nomes)
    pastas = [p for p in arquivos if p not in codigos_pasta]
    sugestoes = sugerir_codigos(pastas, ler_temas_site(TEMAS_SITE_CSV))
    pendencias.revisao_pendente = bool(novas or sugestoes)  # o menu oferece a Revisão (issue #52)
    if not novas and not sugestoes:
        return
    tela.secao("O que falta revisar")
    if novas:
        tela.aviso(f"{novas} sugestão(ões) nova(s) de nome em {tela.caminho(arquivo_nomes)}.")
    if sugestoes:
        registrar_sugestoes_pasta(sugestoes, arquivo_pastas)
        tela.aviso("Pastas SEM tema aprovado (nada delas é enviado):")
        for pasta, codigo, texto, score in sugestoes:
            if not codigo:
                tela.status("fraco", f"{pasta}: nenhum tema parecido em {TEMAS_SITE_CSV} (tema novo no site?)", recuo=4)
            else:
                nivel = "provável" if score >= SCORE_PROVAVEL else "fraco, conferir"
                print(f"    {tela.porcentagem(score)} {pasta}: {nivel} → {texto}")
    tela.comando(revisar, "escolher os temas e confirmar os nomes")


def _ler_alunos(cfg):
    """Lista de alunos ou None (erro já explicado na tela) (T43)."""
    try:
        return carregar_alunos(cfg)
    except (PlanilhaError, OSError, KeyError) as e:
        tela.erro(f"Não consegui ler a lista de alunos {tela.caminho(cfg.planilha)}: {e}")
        tela.status("fraco", "O arquivo precisa ter as colunas Nome, Email e Senha (separadas por ; ou ,).", recuo=4)
        return None


def _resumo_pasta_sem_tema(itens, alunos) -> None:
    """T45: pasta sem tema aprovado: nada dela vai; em vez de uma linha por
    arquivo, uma linha só com como estão os nomes."""
    exatos = {a.nome_norm for a in alunos}
    outros = [i for i in itens if i.estado != "REVISAO_MANUAL"]
    com_nome = sum(1 for i in outros if i.aluno and normalizar_nome(i.pessoa) in exatos)
    sem_aluno = sum(1 for i in outros if not i.aluno)
    tela.status("aviso", "sem tema aprovado: nenhum arquivo vai até escolher o tema (--revisar)", recuo=5)
    tela.status("fraco", f"nomes: {com_nome} exato(s), {len(outros) - com_nome - sem_aluno} parecido(s), "
                         f"{sem_aluno} sem aluno, {len(itens) - len(outros)} para decidir à mão (em branco...)",
                recuo=5)


def _tem_turma(cfg) -> bool:
    """M3: sem turma escolhida nada roda (nem cai na lista/pasta antigas)."""
    if cfg.turma:
        return True
    tela.erro("Escolha a turma: --escola \"<Escola>\" --turma \"<Turma>\" "
              "(ou rode python main.py para o menu). Só o --modo-teste roda sem turma.")
    return False


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Automacao de redacoes — MVP")
    p.add_argument("--config", help="caminho do config.ini")
    p.add_argument("--escola", default=None,
                   help="escola (pasta em \"Redações plataforma/\"); obrigatória fora do --modo-teste")
    p.add_argument("--turma", default=None,
                   help="turma da escola (pasta com alunos.csv e temas/); vai junto com --escola")
    p.add_argument("--modo-teste", action="store_true",
                   help="usa conta de teste e pasta testes/redacoes_teste/")
    p.add_argument("--envio-real", action="store_true",
                   help="habilita envio real (teste: ENVIAR TESTE; producao: ENVIAR)")
    p.add_argument("--analise-remota", action="store_true",
                   help="so leitura: login na conta de teste, le o combo de temas e atualiza dados/temas_site.csv (confirmacao ANALISAR)")
    p.add_argument("--conta-aluno", metavar="EMAIL", default=None,
                   help="com --analise-remota: le o combo na conta deste aluno da turma (senha do alunos.csv)")
    p.add_argument("--revisar", action="store_true",
                   help="revisao no terminal: aprova o tema de cada pasta e renomeia arquivos para o nome do aluno")
    p.add_argument("--desfazer-renomeacao", metavar="LOG_CSV", default=None,
                   help="volta os nomes de uma revisao (relatorios/renomeacoes_<data>.csv)")
    p.add_argument("--limite-alunos", type=int, default=None,
                   help="producao: envia so para os N primeiros alunos do lote")
    p.add_argument("--limite-redacoes", type=int, default=None,
                   help="producao: envia so as N primeiras redacoes do lote")
    p.add_argument("--pasta", default=None,
                   help="saiu na M3 (recusado): use --escola e --turma")
    p.add_argument("--preparar", action="store_true",
                   help="primeiro uso: cria as pastas/arquivos que faltam e mostra onde colocar cada coisa")
    p.add_argument("--sem-janela", action="store_true",
                   help="envia sem mostrar o navegador (padrao: mostra, para acompanhar)")
    p.add_argument("--conferir-site", action="store_true",
                   help="so leitura: entra na conta de cada aluno com redacao na pasta e ve se o tema ja esta "
                        "no site (confirmacao CONFERIR); nao envia nada")
    p.add_argument("--enviar-faltantes", action="store_true",
                   help="envia so as que a conferencia no site de HOJE marcou como faltando (ENVIAR)")
    p.add_argument("--arquivar", action="store_true",
                   help="arquivo morto: move pastas de tema ja enviadas para \"Arquivo morto/<data>\" (nada e apagado)")
    p.add_argument("--resolver", action="store_true",
                   help="resolve as redacoes em REVISAO_MANUAL: chegou no site (s) ou nao (n)")
    p.add_argument("--vincular-antigos", action="store_true",
                   help="registros do caderno de antes das turmas, dos alunos desta turma, passam a ser dela "
                        "(copia do caderno antes; pergunta s/n)")
    p.add_argument("--ensaio", nargs="?", type=int, const=QUANTIDADE_PADRAO, default=None, metavar="N",
                   help=f"redacoes REAIS ja conferidas (padrao {QUANTIDADE_PADRAO}) vao para a CONTA DE TESTE; "
                        "com --envio-real envia (ENVIAR TESTE)")
    return p.parse_args(argv)


def _executar_ensaio(cfg, resultado, alunos, quantidade: int, envio_real: bool) -> int:
    """T42: amostra da fila real enviada para a conta de teste (nunca para o aluno)."""
    from dotenv import load_dotenv
    load_dotenv()
    conta = Aluno(nome=NOME_CONTA_TESTE, email=obter_email_teste().strip())
    if any(a.id == conta.id for a in alunos):
        tela.erro("ESQUEMA_EMAIL_TESTE e o e-mail de um aluno da lista. Ensaio cancelado.")
        return 2
    with Progresso(cfg.banco_progresso, cfg.id_turma) as progresso:
        lotes = montar_lote_ensaio(resultado, cfg.pasta_raiz, conta, progresso, quantidade)
        tela.secao("Ensaio na conta de teste")
        if not lotes:
            tela.aviso("Nenhuma redacao validada para o ensaio (falta aprovar temas/nomes? --revisar).")
            return 0
        for item in lotes[0].itens:
            tela.status("info", f"tema {item.codigo}: {item.pasta}/{item.arquivo}", recuo=4)
        tela.status("fraco", "Vao para a CONTA DE TESTE; nenhuma conta de aluno e aberta.")
        if not envio_real:
            tela.comando(f"python main.py --ensaio {quantidade} --envio-real", "envia estas para a conta de teste")
            return 0
        return executar_envio_producao(cfg, resultado, progresso, conta_teste=conta.email, lotes=lotes)


def _enviar_faltantes(cfg, faltam, entrada=None, resultado=None) -> int:
    """T53: depois da conferência no site, oferece enviar SÓ as fotos que
    certamente não estão lá. Mesmo caminho do envio de produção: trava
    PRODUCAO_BLOQUEADA, lote mostrado, ENVIAR digitado, checagens de sempre."""
    from modulos.dados.planilha_arquivos import ResultadoConciliacao
    from modulos.envio.fila_producao import montar_lote_producao
    tela.secao(f"Enviar as {len(faltam)} que não estão no site?")
    if config_mod.PRODUCAO_BLOQUEADA:
        tela.bloqueado("Envio para os alunos bloqueado hoje: nada foi enviado. A lista está no relatório acima.")
        return 2
    if tela.perguntar("  Montar o envio só destas? (s/n): ", entrada).lower() not in ("s", "sim"):
        tela.info("Ok, nada foi enviado.")
        return 0
    # T56: o lote é montado com a fila INTEIRA (a checagem "mesma foto em duas
    # pastas" e a contagem por tema precisam de todas) e depois fica só com estas
    completo = resultado or ResultadoConciliacao(itens=list(faltam))
    chaves = {(item.aluno.id, item.chave) for item in faltam}
    with Progresso(cfg.banco_progresso, cfg.id_turma) as progresso:
        lotes, ignorados = montar_lote_producao(completo, cfg.pasta_raiz, progresso)
        for lote in lotes:
            lote.itens = [i for i in lote.itens if (lote.aluno.id, i.chave_progresso) in chaves]
        lotes = [lote for lote in lotes if lote.itens]
        for chave, motivo in ignorados:
            if any(chave == c for _, c in chaves):
                tela.status("fraco", f"fora do envio: {chave} ({motivo})")
        return executar_envio_producao(cfg, completo, progresso, lotes=lotes)


def main(argv=None) -> int:
    args = parse_args(argv)
    tela.ativar_cores()
    try:
        cfg = carregar_config(args.config)
    except config_mod.ConfigInvalida as e:
        tela.erro(str(e))
        return 2
    if args.sem_janela:
        cfg.headless = True  # T51: escolha da pessoa; o padrão continua mostrando o navegador
    if args.pasta:
        # M3: a pasta vem da turma; uma pasta solta misturaria lista e temas de turmas diferentes
        tela.erro("--pasta saiu: escolha a turma com --escola e --turma (ou rode python main.py para o menu).")
        return 2
    if bool(args.escola) != bool(args.turma):
        tela.erro("--escola e --turma vao juntos.")
        return 2
    if args.escola:
        if args.modo_teste:
            tela.erro("--modo-teste nao usa turma (usa sempre testes/redacoes_teste/).")
            return 2
        if cfg.dados_do_ini:
            tela.erro("Com --escola/--turma a planilha e a pasta vem da turma: tire pasta_raiz/planilha "
                      "da secao [dados] do config.ini.")
            return 2
        from modulos.base.turma import TurmaInvalida, aplicar_turma
        try:
            aplicar_turma(cfg, args.escola, args.turma, criar=args.preparar)
        except TurmaInvalida as e:
            tela.erro(str(e))
            return 2
    # Bug 020: ações que rodam sozinhas, conferidas antes de qualquer uma rodar
    sozinhas = [nome for nome, ligada in (
        ("--preparar", args.preparar), ("--arquivar", args.arquivar), ("--resolver", args.resolver),
        ("--vincular-antigos", args.vincular_antigos),
        ("--desfazer-renomeacao", bool(args.desfazer_renomeacao)), ("--conferir-site", args.conferir_site),
        ("--enviar-faltantes", args.enviar_faltantes), ("--analise-remota", args.analise_remota)) if ligada]
    envio = args.envio_real or args.modo_teste or args.ensaio is not None or args.revisar
    if len(sozinhas) > 1 or (sozinhas and sozinhas[0] not in ("--desfazer-renomeacao", "--analise-remota")
                             and envio):
        tela.erro(f"{sozinhas[0]} roda sozinho (nao combina com outras acoes nem com envio/ensaio/revisao).")
        return 2
    if args.preparar:
        return preparar(cfg, config_mod.RAIZ)
    if args.arquivar:
        # T57: só move pastas (nada de site nem caderno)
        if args.envio_real or args.modo_teste or args.revisar or args.analise_remota or args.ensaio is not None:
            tela.erro("--arquivar roda sozinho.")
            return 2
        if not _tem_turma(cfg):
            return 2
        from modulos.ferramentas.arquivo_morto import PASTA_ARQUIVO, executar_arquivar
        # M3: Arquivo morto/<Escola>/<Turma>/<data_hora>/; trava global (a mesma do envio)
        return executar_arquivar(cfg.pasta_raiz, config_mod.RAIZ / PASTA_ARQUIVO / cfg.escola / cfg.turma,
                                 cfg.pasta_relatorios, trava=Path(cfg.banco_progresso).parent / "envio.trava")
    # Os avisos já saem na tela; não repetir como UserWarning do Python
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="modulos")
    log = configurar_logging(cfg.pasta_logs)  # T45: automacao.log de cada execução (M3: da turma)
    # T57: o log diz qual comando rodou (o Antônio quer acompanhar pelos logs)
    log.info("Inicio: python main.py %s", " ".join(argv if argv is not None else sys.argv[1:]) or "(conferencia)",
             extra={"so_no_arquivo": True})
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if (args.revisar or args.desfazer_renomeacao) and args.envio_real:
        tela.erro("--revisar/--desfazer-renomeacao nao combinam com --envio-real.")
        return 2
    # T46: opção que não vale na combinação pedida é recusada (não ignorada calada)
    if args.conta_aluno and not args.analise_remota:
        tela.erro("--conta-aluno so vale com --analise-remota.")
        return 2
    if (args.limite_alunos is not None or args.limite_redacoes is not None) and (
            not args.envio_real or args.modo_teste or args.ensaio is not None):
        tela.erro("--limite-alunos/--limite-redacoes so valem no envio de producao (--envio-real); "
                  "no ensaio use --ensaio N.")
        return 2
    if args.resolver and (args.envio_real or args.revisar or args.analise_remota or args.desfazer_renomeacao):
        tela.erro("--resolver roda sozinho.")
        return 2
    if args.desfazer_renomeacao and (args.revisar or args.ensaio is not None or args.analise_remota):
        tela.erro("--desfazer-renomeacao roda sozinho.")
        return 2
    if args.analise_remota and (args.envio_real or args.modo_teste or args.revisar):
        tela.erro("--analise-remota so le os temas: nao combina com --envio-real, --modo-teste ou --revisar.")
        return 2
    if args.ensaio is not None and args.ensaio < 1:
        tela.erro("--ensaio precisa de um numero a partir de 1 (ex.: --ensaio 3).")
        return 2
    if args.enviar_faltantes and (args.conferir_site or args.envio_real or args.modo_teste or args.revisar
                                  or args.analise_remota or args.ensaio is not None or args.resolver
                                  or args.desfazer_renomeacao):
        tela.erro("--enviar-faltantes roda sozinho.")
        return 2
    if args.conferir_site and (args.envio_real or args.modo_teste or args.revisar or args.analise_remota
                               or args.ensaio is not None or args.resolver or args.desfazer_renomeacao):
        tela.erro("--conferir-site roda sozinho (so le o site, nao envia).")
        return 2
    if args.ensaio is not None and (args.modo_teste or args.revisar or args.analise_remota):
        tela.erro("--ensaio usa as redacoes reais: nao combina com --modo-teste, --revisar ou --analise-remota.")
        return 2
    if not args.modo_teste and not _tem_turma(cfg):
        return 2
    if args.modo_teste:
        configurar_modo_teste(cfg)  # T40: pasta e aprovações de testes/
    if args.resolver:
        # T49: só mexe no caderno; os nomes vêm da lista, se ela existir
        from modulos.ferramentas.resolver import executar_resolver
        nomes = {}
        if Path(cfg.planilha).is_file():
            nomes = {a.id: a.nome for a in (_ler_alunos(cfg) or [])}
        import os
        from dotenv import load_dotenv
        load_dotenv()
        contas_teste = ()
        if os.getenv("ESQUEMA_EMAIL_TESTE"):
            contas_teste = (os.environ["ESQUEMA_EMAIL_TESTE"].strip().casefold(),)
            nomes[contas_teste[0]] = NOME_CONTA_TESTE
        # M3: só os registros desta turma (+ os da conta de teste, que não é de turma nenhuma)
        executar_resolver(cfg.banco_progresso, cfg.pasta_relatorios, nomes, pasta_raiz=cfg.pasta_raiz,
                          turma=cfg.id_turma, contas_teste=contas_teste)
        return 0
    if args.vincular_antigos:
        from modulos.ferramentas.resolver import vincular_antigos
        alunos = _ler_alunos(cfg)
        if alunos is None:
            return 2
        vincular_antigos(cfg.banco_progresso, cfg.id_turma, [a.id for a in alunos])
        return 0
    if args.desfazer_renomeacao:
        tela.titulo("DESFAZER RENOMEAÇÃO")
        # M3: log de outra turma (outra pasta de temas) é recusado
        desfazer_renomeacoes(Path(args.desfazer_renomeacao), cfg.pasta_raiz, banco=cfg.banco_progresso,
                             exigir_raiz=True)
        return 0

    # Análise remota (T27): só lê o combo de temas do site e atualiza o CSV
    if args.analise_remota:
        from dotenv import load_dotenv
        load_dotenv()
        aluno_conta = None
        if args.conta_aluno:
            # T29: o combo de um aluno pode ter temas que a conta de teste não tem
            aluno_conta = next((a for a in (_ler_alunos(cfg) or [])
                                if a.email.casefold() == args.conta_aluno.strip().casefold()), None)
            if aluno_conta is None:
                tela.erro(f"{args.conta_aluno} nao esta na lista de alunos ({cfg.planilha}).")
                return 2
        return executar_analise_remota(cfg, TEMAS_SITE_CSV, aluno=aluno_conta)

    modo = ("MODO TESTE (conta de teste)" if args.modo_teste
            else "ENSAIO (redacoes reais -> conta de teste)" if args.ensaio is not None
            else "alunos da lista")
    if not args.revisar and not args.conferir_site and not args.enviar_faltantes:
        tela.titulo(f"CONFERÊNCIA  ·  {modo}  ·  " + ("depois envia" if args.envio_real else "nada é enviado"))
    tela.secao("Dados")

    # Modo teste: usa conta de teste e pasta de teste
    if args.modo_teste:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        # T40: mesmo caminho da produção; o único aluno é a conta de teste
        email_teste = os.getenv("ESQUEMA_EMAIL_TESTE", "teste@esquema.com")
        alunos = [Aluno(nome=NOME_CONTA_TESTE, email=email_teste)]
        tela.ok(f"Conta de teste: {NOME_CONTA_TESTE}  ·  pasta {tela.caminho(cfg.pasta_raiz)}")
    else:
        if args.envio_real or args.enviar_faltantes:  # T56: as mesmas checagens antes do envio
            # Produção (F4/T24): fail-closed sem a referência de códigos do site
            if not ler_codigos_site_csv(TEMAS_SITE_CSV):
                tela.erro(f"Envio de producao exige {TEMAS_SITE_CSV} com os codigos do combo de temas.")
                tela.erro("Nada foi enviado.")
                return 2
            if config_mod.PRODUCAO_BLOQUEADA and args.ensaio is None:
                tela.bloqueado(config_mod.MENSAGEM_PRODUCAO_BLOQUEADA)
                return 2
            # Senha padrão vem do .env (ou getpass)
            from dotenv import load_dotenv
            load_dotenv()
            log.info("Iniciando conciliacao para envio (%s).", "ensaio" if args.ensaio is not None else "producao")
        if (args.envio_real or args.enviar_faltantes) and not Path(cfg.planilha).is_file():
            tela.erro(f"Planilha de alunos nao encontrada: {cfg.planilha}")
            return 2
        if not Path(cfg.planilha).is_file() or not Path(cfg.pasta_raiz).is_dir():
            # Primeiro uso (T38): explicar em vez de quebrar
            tela.aviso("Falta a lista de alunos ou a pasta das redacoes.")
            mostrar_guia(cfg, config_mod.RAIZ / ".env")
            tela.comando("python main.py --preparar", "cria o que falta")
            return 2
        alunos = _ler_alunos(cfg)
        if alunos is None:
            return 2
        tela.ok(f"Alunos carregados: {len(alunos)}  ·  pasta {tela.caminho(cfg.pasta_raiz)}")

    # O CSV é só referência; a trava real é o combo da conta logada,
    # conferido item a item antes do clique (T18D).
    codigos_site: list[str] = []
    if Path(TEMAS_SITE_CSV).exists():
        codigos_site = ler_codigos_site_csv(TEMAS_SITE_CSV)
        if codigos_site:
            tela.info(f"Temas do site: {len(set(codigos_site))} códigos em {tela.caminho(TEMAS_SITE_CSV)} "
                      "(atualize com --analise-remota)")
        else:
            tela.aviso(f"{TEMAS_SITE_CSV} existe mas sem códigos válidos")
    else:
        tela.aviso(f"{TEMAS_SITE_CSV} não encontrado, sem validação de CODIGO_INVALIDO")

    # Conciliação com as aprovações do humano (T26/T28); T40: vale também no modo teste
    conciliacao = conciliar_com_aprovacoes(cfg, alunos, codigos_site)
    resultado, arquivos = conciliacao.resultado, conciliacao.arquivos
    nomes_aprovados, codigos_pasta = conciliacao.nomes_aprovados, conciliacao.codigos_pasta
    tela.ok(f"Pastas de tema: {len(arquivos)}  ·  fotos encontradas: {sum(len(v) for v in arquivos.values())}")
    if nomes_aprovados:
        tela.ok(f"Nomes aprovados em {cfg.arquivo_nomes_aprovados.name}: {len(nomes_aprovados)}")
    for pasta, codigo in sorted(codigos_pasta.items()):
        if pasta in arquivos:
            if not codigos_site or codigo in codigos_site:
                tela.ok(f"Pasta aprovada: {pasta} -> tema {codigo}")
            else:
                tela.aviso(f"Pasta aprovada: {pasta} -> tema {codigo}  (codigo fora do temas_site.csv)")

    cfg.pasta_relatorios.mkdir(parents=True, exist_ok=True)
    if args.conferir_site:
        # T52: só leitura nas contas dos alunos; não grava caderno nem envia
        from dotenv import load_dotenv
        from modulos.site.conferencia_site import executar_conferencia_site
        load_dotenv()
        from modulos.site.conferencia_manual import conferir_manualmente
        guiada = (lambda problemas: conferir_manualmente(cfg, problemas)) if sys.stdin.isatty() else None  # só com pessoa
        return executar_conferencia_site(cfg, resultado, depois=lambda faltam: _enviar_faltantes(cfg, faltam, resultado=resultado),
                                         guiada=guiada)
    if args.enviar_faltantes:
        # T54: usa a conferência de hoje (menu 7), sem abrir as contas de novo
        from dotenv import load_dotenv
        from modulos.site.conferencia_site import faltantes_do_relatorio
        load_dotenv()
        tela.titulo("ENVIAR AS QUE FALTAM NO SITE")
        faltam = faltantes_do_relatorio(cfg.pasta_relatorios, resultado, turma=cfg.id_turma)
        if faltam is None:
            return 2
        if not faltam:
            tela.ok("A conferência de hoje não achou nenhuma faltando: nada para enviar.")
            return 0
        return _enviar_faltantes(cfg, faltam, resultado=resultado)
    if args.revisar:
        return executar_revisao(
            resultado, alunos, arquivos, ler_temas_site(TEMAS_SITE_CSV), codigos_pasta,
            cfg.pasta_raiz, cfg.arquivo_pastas_aprovadas, cfg.banco_progresso,
            cfg.pasta_relatorios, nomes_aprovados,
            turma_args=" --modo-teste" if args.modo_teste else f' --escola "{cfg.escola}" --turma "{cfg.turma}"',
            planilha=None if args.modo_teste else cfg.planilha,  # aluno que falta na lista (issue #54)
        )
    csv_path = gerar_relatorio_conciliacao(
        resultado, cfg.pasta_relatorios / "relatorio_conciliacao.csv"
    )
    txt_path = gerar_fila_dry_run(
        resultado, cfg.pasta_relatorios / "fila_dry_run.txt"
    )

    with Progresso(cfg.banco_progresso, cfg.id_turma) as prog:
        for item in resultado.fila_validada():
            if prog.obter(item.aluno.id, item.chave) is None:
                prog.marcar(item.aluno.id, item.chave, "A_ENVIAR", pasta=item.pasta)

    resumo = resultado.resumo()
    tela.secao("Resumo")
    tela.contagens([
        ("Prontas para enviar", resumo["EXATO_UNICO"], "ok"),
        ("Nome parecido (confirmar no --revisar)", resumo["SUGESTAO_FUZZY"], "aviso"),
        ("Nome de mais de um aluno", resumo["AMBIGUO"], "aviso"),
        ("Arquivo sem aluno", resumo["ARQUIVO_SEM_ALUNO"], "aviso"),
        ("Aluno sem arquivo", resumo["ALUNO_SEM_ARQUIVO"], "fraco"),
        ("Em pasta sem tema", resumo.get("SEM_CODIGO", 0), "aviso"),
        ("Tema que não existe no site", resumo.get("CODIGO_INVALIDO", 0), "erro"),
        ("Tema repetido no site", resumo.get("SIMULADO", 0), "erro"),
        ("Para decidir à mão", resumo.get("REVISAO_MANUAL", 0), "aviso"),
    ])

    # Tabela por tema
    if any(i.pasta for i in resultado.itens):
        tela.secao("Detalhes por tema")
        for tema in sorted(set(i.pasta for i in resultado.itens if i.pasta)):
            itens_tema = [i for i in resultado.itens if i.pasta == tema]
            # T51: abre a pasta; bug 022: no VS Code pasta não vira link (T52)
            nome_pasta = tela.link(tela.c(tema, "pasta"), Path(cfg.pasta_raiz) / tema, pasta=True)
            print(f"  {tela.SIMBOLOS['pasta']} {nome_pasta}  {tela.c(f'({len(itens_tema)} arquivo(s))', 'fraco')}")
            if not any(i.codigo_tema for i in itens_tema):
                _resumo_pasta_sem_tema(itens_tema, alunos)
                continue
            for item in itens_tema:
                aluno_nome = item.aluno.nome if item.aluno else "?"
                # T50: o texto interno (fixo pelo teste protegido) fica curto na tela
                texto_obs = item.observacao.replace("revisao humana obrigatoria antes de validar",
                                                    "confirmar no --revisar")
                obs = tela.c(f"  ({texto_obs})", "fraco") if texto_obs else ""
                papel = tela.PAPEL_DO_ESTADO.get(item.estado, "info")
                arquivo = tela.link(item.arquivo, Path(cfg.pasta_raiz) / item.pasta / item.arquivo)  # T51
                tela.status(papel, f"{tela.rotulo(item.estado)}: {arquivo} → {aluno_nome}", recuo=5,
                            saida=lambda linha, obs=obs: print(linha + obs))

    tela.secao("Arquivos gerados")
    tela.info(f"Relatório (abre no Excel): {tela.caminho(csv_path)}")
    tela.info(f"Fila do envio:             {tela.caminho(txt_path)}")
    tela.status("fraco", "Só as \"prontas\" entram no envio; as outras esperam a revisão.")

    _mostrar_sugestoes(resultado, alunos, arquivos, cfg.arquivo_nomes_aprovados,
                       cfg.arquivo_pastas_aprovadas, codigos_pasta,
                       "python main.py --modo-teste --revisar" if args.modo_teste else "python main.py --revisar")

    # Ensaio (T42): redações reais -> conta de teste
    if args.ensaio is not None:
        return _executar_ensaio(cfg, resultado, alunos, args.ensaio, args.envio_real)

    # Modo teste com envio real: executar fluxo de envio de teste
    if args.modo_teste and args.envio_real:
        with Progresso(cfg.banco_progresso, cfg.id_turma) as progresso:
            return executar_envio_teste(cfg, progresso)

    # Produção com envio real (F4/T24): confirmação ENVIAR dentro do fluxo
    if args.envio_real:
        with Progresso(cfg.banco_progresso, cfg.id_turma) as progresso:
            return executar_envio_producao(
                cfg, resultado, progresso,
                limite_alunos=args.limite_alunos,
                limite_redacoes=args.limite_redacoes,
            )

    if resultado.fila_validada() and not args.modo_teste:
        tela.secao("Próximo passo")
        tela.comando(f"python main.py --ensaio {QUANTIDADE_PADRAO}",
                     "manda algumas destas para a CONTA DE TESTE, para testar com redações reais")
    print()
    # T50: fim normal da conferência não é erro (antes saía um ⛔ vermelho)
    tela.info("Só conferência: nada foi enviado.")
    return 0


if __name__ == "__main__":
    # T45: dados/, testes/ e diagnosticos/ são relativos à pasta do projeto;
    # assim funciona mesmo rodando o script de outra pasta.
    import os
    os.chdir(Path(__file__).resolve().parent)
    # T47: sem nenhuma opção, num terminal de verdade, abre o menu
    if len(sys.argv) == 1 and sys.stdin.isatty():
        from modulos.ferramentas.menu import executar_menu
        tela.ativar_cores()
        sys.exit(executar_menu(main))
    sys.exit(main())