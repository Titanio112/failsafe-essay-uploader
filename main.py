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

from modulos.config import MENSAGEM_BLOQUEIO, carregar_config
from modulos.planilha_arquivos import (
    Aluno,
    carregar_alunos,
    conciliar,
    descobrir_arquivos,
)
from modulos.progresso_relatorio import (
    Progresso,
    configurar_logging,
    gerar_fila_dry_run,
    gerar_relatorio_conciliacao,
)
from modulos.fluxo_envio_teste import executar_envio_teste
from modulos.fluxo_envio_producao import executar_envio_producao
from modulos.analise_remota import executar_analise_remota
from modulos.nomes_aprovados import (
    carregar_nomes_aprovados,
    registrar_sugestoes,
)
from modulos.sugestao_temas import SCORE_PROVAVEL, ler_temas_site, sugerir_codigos


TEMAS_SITE_CSV = Path("dados/temas_site.csv")


def ler_codigos_site_csv(caminho: Path) -> list[str]:
    """Códigos (strings exatas) da coluna 'codigo' do CSV, NA ORDEM e com os
    repetidos (ex.: 0000 duas vezes), para a conciliação marcar código
    duplicado no combo (bug 001). Vazio se não existir."""
    import csv
    if not Path(caminho).is_file():
        return []
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return [row["codigo"] for row in csv.DictReader(f) if row.get("codigo")]


def _mostrar_sugestoes(resultado, alunos, arquivos, arquivo_nomes) -> None:
    """Sugestões para o humano resolver (T26): nomes e códigos de tema. Só sugere."""
    novas = registrar_sugestoes(resultado, alunos, arquivo_nomes)
    if novas:
        print()
        print(f"{novas} sugestao(oes) nova(s) de nome em {arquivo_nomes}.")
        print("Abra o arquivo e escreva 'sim' na coluna 'aprovado' das que estiverem certas;")
        print("na proxima execucao esses arquivos entram na fila como nome exato.")

    sugestoes = sugerir_codigos(list(arquivos), ler_temas_site(TEMAS_SITE_CSV))
    if sugestoes:
        print()
        print("Pastas SEM codigo de tema (nada delas sera enviado). Renomeie para '<codigo> - <titulo>':")
        for pasta, codigo, texto, score in sugestoes:
            if not codigo:
                print(f"  {pasta}: nenhum tema parecido em {TEMAS_SITE_CSV} (tema novo no site?)")
            else:
                nivel = "provavel" if score >= SCORE_PROVAVEL else "FRACO, conferir"
                print(f"  {pasta}: {nivel} -> {texto} ({score:.0f}%)")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Automacao de redacoes — MVP")
    p.add_argument("--config", help="caminho do config.ini")
    p.add_argument("--modo-teste", action="store_true",
                   help="usa conta de teste e pasta testes/redacoes_teste/")
    p.add_argument("--envio-real", action="store_true",
                   help="habilita envio real (teste: ENVIAR TESTE; producao: ENVIAR)")
    p.add_argument("--analise-remota", action="store_true",
                   help="so leitura: login na conta de teste, le o combo de temas e atualiza dados/temas_site.csv (confirmacao ANALISAR)")
    p.add_argument("--limite-alunos", type=int, default=None)
    p.add_argument("--limite-redacoes", type=int, default=None)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = carregar_config(args.config)
    log = configurar_logging()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Análise remota (T27): só lê o combo de temas do site e atualiza o CSV
    if args.analise_remota:
        from dotenv import load_dotenv
        load_dotenv()
        return executar_analise_remota(cfg, TEMAS_SITE_CSV)

    # Modo teste: usa conta de teste e pasta de teste
    if args.modo_teste:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        cfg.planilha = Path("testes") / "planilha_teste.xlsx"  # placeholder, não usado
        cfg.pasta_raiz = Path("testes/redacoes_teste")
        # Apenas aluno virtual
        email_teste = os.getenv("ESQUEMA_EMAIL_TESTE", "teste@esquema.com")
        alunos = [Aluno(nome="Usuario Testes Ignorar", email=email_teste)]
        log.info("Modo teste: processando aluno virtual Usuario Testes Ignorar")
    else:
        if args.envio_real:
            # Produção (F4/T24): fail-closed sem a referência de códigos do site
            if not ler_codigos_site_csv(TEMAS_SITE_CSV):
                print(f"[ERRO] Envio de producao exige {TEMAS_SITE_CSV} com os codigos do combo de temas.")
                print("[ERRO] Nada foi enviado.")
                return 2
            # Senha padrão vem do .env (ou getpass)
            from dotenv import load_dotenv
            load_dotenv()
            log.info("Iniciando conciliacao para envio de producao.")
        else:
            log.info("Iniciando conciliacao (dry-run).")
        if args.envio_real and not Path(cfg.planilha).is_file():
            print(f"[ERRO] Planilha de alunos nao encontrada: {cfg.planilha}")
            return 2
        alunos = carregar_alunos(cfg)
        print(f"Alunos carregados: {len(alunos)}")

    arquivos = descobrir_arquivos(cfg)
    total_jpgs = sum(len(v) for v in arquivos.values())
    print(f"Pastas de temas: {len(arquivos)} | JPGs encontrados: {total_jpgs}")

    # Determinar codigos_site com fail-closed
    codigos_site: list[str] = []
    # O CSV é só referência; a trava real é o combo da conta logada,
    # conferido item a item antes do clique (T18D).
    if TEMAS_SITE_CSV.exists():
        codigos_site = ler_codigos_site_csv(TEMAS_SITE_CSV)
        if codigos_site:
            print(f"[AVISO] Usando {len(set(codigos_site))} códigos de dados/temas_site.csv (referência; atualize com --analise-remota)")
        else:
            print("[AVISO] dados/temas_site.csv existe mas sem códigos válidos")
    else:
        print("[AVISO] dados/temas_site.csv não encontrado, sem validação de CODIGO_INVALIDO")

    # Nomes de arquivo aprovados por humano (T26); não vale no modo teste
    nomes_aprovados = {} if args.modo_teste else carregar_nomes_aprovados(cfg.arquivo_nomes_aprovados, alunos)
    if nomes_aprovados:
        print(f"Nomes aprovados em {cfg.arquivo_nomes_aprovados.name}: {len(nomes_aprovados)}")

    resultado = conciliar(
        alunos, arquivos,
        codigos_site=codigos_site,
        limiar=cfg.limiar_fuzzy, margem=cfg.margem_minima,
        nomes_aprovados=nomes_aprovados,
    )

    cfg.pasta_relatorios.mkdir(parents=True, exist_ok=True)
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
    print()
    print("Resumo da conciliacao:")
    print(f"  Exatos unicos (fila real): {resumo['EXATO_UNICO']}")
    print(f"  Sugestoes fuzzy (revisao): {resumo['SUGESTAO_FUZZY']}")
    print(f"  Ambiguos:                  {resumo['AMBIGUO']}")
    print(f"  Arquivos sem aluno:        {resumo['ARQUIVO_SEM_ALUNO']}")
    print(f"  Alunos sem arquivo:        {resumo['ALUNO_SEM_ARQUIVO']}")
    print(f"  Sem codigo na pasta:       {resumo.get('SEM_CODIGO', 0)}")
    print(f"  Codigo invalido:           {resumo.get('CODIGO_INVALIDO', 0)}")
    print(f"  Simulados (codigo duplicado no site): {resumo.get('SIMULADO', 0)}")
    print(f"  Revisao manual:            {resumo.get('REVISAO_MANUAL', 0)}")
    print()

    # Tabela por tema
    if resultado.itens:
        print("Detalhes por tema:")
        temas_ordenados = sorted(set(i.pasta for i in resultado.itens if i.pasta))
        for tema in temas_ordenados:
            itens_tema = [i for i in resultado.itens if i.pasta == tema]
            print(f"  Tema {tema}: {len(itens_tema)} arquivo(s)")
            for item in itens_tema:
                aluno_nome = item.aluno.nome if item.aluno else "N/A"
                obs = f" ({item.observacao})" if item.observacao else ""
                print(f"    {item.estado}: {item.arquivo} -> {aluno_nome}{obs}")

    print()
    print(f"Relatorio CSV: {csv_path}")
    print(f"Fila dry-run:  {txt_path}")
    print()
    print("Revise o CSV antes de autorizar qualquer envio. Fuzzy/ambiguo/sem par")
    print("exigem revisao humana e nao entram na fila real.")

    if not args.modo_teste:
        _mostrar_sugestoes(resultado, alunos, arquivos, cfg.arquivo_nomes_aprovados)

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

    print(MENSAGEM_BLOQUEIO + " (dry-run; use --envio-real para enviar)")
    return 0


if __name__ == "__main__":
    sys.exit(main())