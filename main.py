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
from modulos.base import tela
from modulos.base.config import (
    MENSAGEM_BLOQUEIO,
    NOME_CONTA_TESTE,
    carregar_config,
    configurar_modo_teste,
    obter_email_teste,
)
from modulos.envio.ensaio import QUANTIDADE_PADRAO, montar_lote_ensaio
from modulos.dados.planilha_arquivos import Aluno, carregar_alunos
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
    if not novas and not sugestoes:
        return
    tela.secao("O que falta revisar")
    if novas:
        tela.aviso(f"{novas} sugestao(oes) nova(s) de nome em {tela.caminho(arquivo_nomes)}.")
    if sugestoes:
        registrar_sugestoes_pasta(sugestoes, arquivo_pastas)
        tela.aviso("Pastas SEM codigo de tema aprovado (nada delas sera enviado):")
        for pasta, codigo, texto, score in sugestoes:
            if not codigo:
                tela.status("fraco", f"{pasta}: nenhum tema parecido em {TEMAS_SITE_CSV} (tema novo no site?)", recuo=4)
            else:
                nivel = "provavel" if score >= SCORE_PROVAVEL else "FRACO, conferir"
                print(f"    {tela.porcentagem(score)} {pasta}: {nivel} -> {texto}")
    tela.comando(revisar, "escolher os temas e confirmar os nomes")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Automacao de redacoes — MVP")
    p.add_argument("--config", help="caminho do config.ini")
    p.add_argument("--modo-teste", action="store_true",
                   help="usa conta de teste e pasta testes/redacoes_teste/")
    p.add_argument("--envio-real", action="store_true",
                   help="habilita envio real (teste: ENVIAR TESTE; producao: ENVIAR)")
    p.add_argument("--analise-remota", action="store_true",
                   help="so leitura: login na conta de teste, le o combo de temas e atualiza dados/temas_site.csv (confirmacao ANALISAR)")
    p.add_argument("--conta-aluno", metavar="EMAIL", default=None,
                   help="com --analise-remota: le o combo na conta deste aluno da lista (senha ESQUEMA_SENHA_PADRAO)")
    p.add_argument("--revisar", action="store_true",
                   help="revisao no terminal: aprova o tema de cada pasta e renomeia arquivos para o nome do aluno")
    p.add_argument("--desfazer-renomeacao", metavar="LOG_CSV", default=None,
                   help="volta os nomes de uma revisao (relatorios/renomeacoes_<data>.csv)")
    p.add_argument("--limite-alunos", type=int, default=None)
    p.add_argument("--limite-redacoes", type=int, default=None)
    p.add_argument("--pasta", default=None,
                   help="pasta com as redacoes; padrao: \"Redações plataforma\" na raiz do projeto")
    p.add_argument("--preparar", action="store_true",
                   help="primeiro uso: cria as pastas/arquivos que faltam e mostra onde colocar cada coisa")
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
    with Progresso(cfg.banco_progresso) as progresso:
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


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = carregar_config(args.config)
    tela.ativar_cores()
    if args.pasta and not args.modo_teste:
        cfg.pasta_raiz = Path(args.pasta)
        if not cfg.pasta_raiz.is_dir():
            tela.erro(f"Pasta de redacoes nao encontrada: {cfg.pasta_raiz}")
            return 2
    if args.preparar:
        return preparar(cfg, config_mod.RAIZ)
    # Os avisos já saem na tela; não repetir como UserWarning do Python
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="modulos")
    log = configurar_logging()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if (args.revisar or args.desfazer_renomeacao) and args.envio_real:
        tela.erro("--revisar/--desfazer-renomeacao nao combinam com --envio-real.")
        return 2
    if args.ensaio is not None and (args.modo_teste or args.revisar or args.analise_remota):
        tela.erro("--ensaio usa as redacoes reais: nao combina com --modo-teste, --revisar ou --analise-remota.")
        return 2
    if args.modo_teste:
        configurar_modo_teste(cfg)  # T40: pasta e aprovações de testes/
    if args.desfazer_renomeacao:
        tela.titulo("DESFAZER RENOMEAÇÃO")
        desfazer_renomeacoes(Path(args.desfazer_renomeacao), cfg.pasta_raiz)
        return 0

    # Análise remota (T27): só lê o combo de temas do site e atualiza o CSV
    if args.analise_remota:
        from dotenv import load_dotenv
        load_dotenv()
        aluno_conta = None
        if args.conta_aluno:
            # T29: o combo de um aluno pode ter temas que a conta de teste não tem
            aluno_conta = next((a for a in carregar_alunos(cfg)
                                if a.email.casefold() == args.conta_aluno.strip().casefold()), None)
            if aluno_conta is None:
                tela.erro(f"{args.conta_aluno} nao esta na lista de alunos ({cfg.planilha}).")
                return 2
        return executar_analise_remota(cfg, TEMAS_SITE_CSV, aluno=aluno_conta)

    modo = ("MODO TESTE (conta de teste)" if args.modo_teste
            else "ENSAIO (redacoes reais -> conta de teste)" if args.ensaio is not None
            else "alunos da lista")
    if not args.revisar:
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
        if args.envio_real:
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
            log.info("Iniciando conciliacao para envio de producao.")
        if args.envio_real and not Path(cfg.planilha).is_file():
            tela.erro(f"Planilha de alunos nao encontrada: {cfg.planilha}")
            return 2
        if not Path(cfg.planilha).is_file() or not Path(cfg.pasta_raiz).is_dir():
            # Primeiro uso (T38): explicar em vez de quebrar
            tela.aviso("Falta a lista de alunos ou a pasta das redacoes.")
            mostrar_guia(cfg, config_mod.RAIZ / ".env")
            tela.comando("python main.py --preparar", "cria o que falta")
            return 2
        alunos = carregar_alunos(cfg)
        tela.ok(f"Alunos carregados: {len(alunos)}  ·  pasta {tela.caminho(cfg.pasta_raiz)}")

    # O CSV é só referência; a trava real é o combo da conta logada,
    # conferido item a item antes do clique (T18D).
    codigos_site: list[str] = []
    if TEMAS_SITE_CSV.exists():
        codigos_site = ler_codigos_site_csv(TEMAS_SITE_CSV)
        if codigos_site:
            tela.info(f"Temas do site: {len(set(codigos_site))} códigos em dados/temas_site.csv "
                      "(atualize com --analise-remota)")
        else:
            tela.aviso("dados/temas_site.csv existe mas sem códigos válidos")
    else:
        tela.aviso("dados/temas_site.csv não encontrado, sem validação de CODIGO_INVALIDO")

    # Conciliação com as aprovações do humano (T26/T28); T40: vale também no modo teste
    conciliacao = conciliar_com_aprovacoes(cfg, alunos, codigos_site)
    resultado, arquivos = conciliacao.resultado, conciliacao.arquivos
    nomes_aprovados, codigos_pasta = conciliacao.nomes_aprovados, conciliacao.codigos_pasta
    tela.ok(f"Pastas de temas: {len(arquivos)} | JPGs encontrados: {sum(len(v) for v in arquivos.values())}")
    if nomes_aprovados:
        tela.ok(f"Nomes aprovados em {cfg.arquivo_nomes_aprovados.name}: {len(nomes_aprovados)}")
    for pasta, codigo in sorted(codigos_pasta.items()):
        if pasta in arquivos:
            if not codigos_site or codigo in codigos_site:
                tela.ok(f"Pasta aprovada: {pasta} -> tema {codigo}")
            else:
                tela.aviso(f"Pasta aprovada: {pasta} -> tema {codigo}  (codigo fora do temas_site.csv)")

    cfg.pasta_relatorios.mkdir(parents=True, exist_ok=True)
    if args.revisar:
        return executar_revisao(
            resultado, alunos, arquivos, ler_temas_site(TEMAS_SITE_CSV), codigos_pasta,
            cfg.pasta_raiz, cfg.arquivo_pastas_aprovadas, cfg.banco_progresso,
            cfg.pasta_relatorios, nomes_aprovados,
        )
    csv_path = gerar_relatorio_conciliacao(
        resultado, cfg.pasta_relatorios / "relatorio_conciliacao.csv"
    )
    txt_path = gerar_fila_dry_run(
        resultado, cfg.pasta_relatorios / "fila_dry_run.txt"
    )

    with Progresso(cfg.banco_progresso) as prog:
        for item in resultado.fila_validada():
            if prog.obter(item.aluno.id, item.chave) is None:
                prog.marcar(item.aluno.id, item.chave, "A_ENVIAR", pasta=item.pasta)

    resumo = resultado.resumo()
    tela.secao("Resumo da conciliacao")
    tela.contagens([
        ("Exatos unicos (fila real)", resumo["EXATO_UNICO"], "ok"),
        ("Sugestoes fuzzy (revisao)", resumo["SUGESTAO_FUZZY"], "aviso"),
        ("Ambiguos", resumo["AMBIGUO"], "aviso"),
        ("Arquivos sem aluno", resumo["ARQUIVO_SEM_ALUNO"], "aviso"),
        ("Alunos sem arquivo", resumo["ALUNO_SEM_ARQUIVO"], "fraco"),
        ("Sem codigo na pasta", resumo.get("SEM_CODIGO", 0), "aviso"),
        ("Codigo invalido", resumo.get("CODIGO_INVALIDO", 0), "erro"),
        ("Codigo repetido no site", resumo.get("SIMULADO", 0), "erro"),
        ("Revisao manual", resumo.get("REVISAO_MANUAL", 0), "aviso"),
    ])

    # Tabela por tema
    if any(i.pasta for i in resultado.itens):
        tela.secao("Detalhes por tema")
        for tema in sorted(set(i.pasta for i in resultado.itens if i.pasta)):
            itens_tema = [i for i in resultado.itens if i.pasta == tema]
            print(f"  {tela.SIMBOLOS['pasta']} {tela.c(tema, 'pasta')}  {tela.c(f'({len(itens_tema)} arquivo(s))', 'fraco')}")
            for item in itens_tema:
                aluno_nome = item.aluno.nome if item.aluno else "N/A"
                obs = tela.c(f"  ({item.observacao})", "fraco") if item.observacao else ""
                papel = tela.PAPEL_DO_ESTADO.get(item.estado, "info")
                tela.status(papel, f"{item.estado}: {item.arquivo} -> {aluno_nome}", recuo=5,
                            saida=lambda linha, obs=obs: print(linha + obs))

    tela.secao("Arquivos gerados")
    tela.info(f"Relatorio CSV: {tela.caminho(csv_path)}")
    tela.info(f"Fila dry-run:  {tela.caminho(txt_path)}")
    tela.status("fraco", "Fuzzy/ambiguo/sem par exigem revisao humana e nao entram na fila real.")

    _mostrar_sugestoes(resultado, alunos, arquivos, cfg.arquivo_nomes_aprovados,
                       cfg.arquivo_pastas_aprovadas, codigos_pasta,
                       "python main.py --modo-teste --revisar" if args.modo_teste else "python main.py --revisar")

    # Ensaio (T42): redações reais -> conta de teste
    if args.ensaio is not None:
        return _executar_ensaio(cfg, resultado, alunos, args.ensaio, args.envio_real)

    # Modo teste com envio real: executar fluxo de envio de teste
    if args.modo_teste and args.envio_real:
        progresso = Progresso(cfg.banco_progresso)
        return executar_envio_teste(cfg, progresso)

    # Produção com envio real (F4/T24): confirmação ENVIAR dentro do fluxo
    if args.envio_real:
        with Progresso(cfg.banco_progresso) as progresso:
            return executar_envio_producao(
                cfg, resultado, progresso,
                limite_alunos=args.limite_alunos,
                limite_redacoes=args.limite_redacoes,
            )

    print()
    tela.bloqueado(MENSAGEM_BLOQUEIO + " (dry-run; use --envio-real para enviar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())