"""CLI: orquestracao. Padrao: dry-run. NÃO EXISTEM SALAS — entramos como aluno."""

from __future__ import annotations

import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configuração de encoding para stdout e stderr
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from config import Config, MENSAGEM_BLOQUEIO, carregar_config
from planilha_arquivos import (
    ALUNO_SEM_ARQUIVO,
    carregar_alunos,
    conciliar,
    descobrir_arquivos,
    mascarar_email,
    normalizar_nome,
    Aluno,
    ResultadoConciliacao,
    ItemConciliacao,
    EXATO_UNICO,
    SUGESTAO_FUZZY,
    AMBIGUO,
    ARQUIVO_SEM_ALUNO,
    SEM_CODIGO,
    CODIGO_INVALIDO,
    REVISAO_MANUAL,
)
from progresso_relatorio import (
    Progresso,
    configurar_logging,
    gerar_fila_dry_run,
    gerar_relatorio_conciliacao,
    JA_ENVIADO,
)
from plataforma import (
    login,
    confirmar_identidade,
    ler_saldo_creditos,
    ler_lista_redacoes,
    verificar_duplicidade,
    abrir_formulario_envio,
    ler_combo_temas,
    selecionar_tema_por_codigo,
    selecionar_criterio,
    anexar_arquivo,
    aguardar_upload_aceito,
    clicar_enviar,
    aguardar_confirmacao,
    logout,
)
    p = argparse.ArgumentParser(description="Automacao de redacoes — MVP")
    p.add_argument("--config", help="caminho do config.ini")
    p.add_argument("--modo-teste", action="store_true",
                   help="usa conta de teste e pasta testes/redacoes_teste/")
    p.add_argument("--envio-real", action="store_true",
                   help="habilita envio real (somente Fase 3+)")
    p.add_argument("--analise-remota", action="store_true",
                   help="somente leitura: login, lista redacoes, combo temas, logout")
    p.add_argument("--limite-alunos", type=int, default=None)
    p.add_argument("--limite-redacoes", type=int, default=None)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = carregar_config(args.config)
    log = configurar_logging()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if args.envio_real:
        print(MENSAGEM_BLOQUEIO)
        print("Envio real so sera executado na Fase 3, com as confirmacoes exigidas.")
        return 2

    # Modo teste: usa conta de teste e pasta de teste
    if args.modo_teste:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        cfg.planilha = Path("testes") / "planilha_teste.xlsx"  # placeholder, não usado
        cfg.pasta_raiz = Path("testes/redacoes_teste")
        # Apenas aluno virtual
        from planilha_arquivos import Aluno
        email_teste = os.getenv("ESQUEMA_EMAIL_TESTE", "teste@esquema.com")
        alunos = [Aluno(nome="Usuario Testes Ignorar", email=email_teste, sala="TESTE")]
        log.info("Modo teste: processando aluno virtual Usuario Testes Ignorar")
    else:
        log.info("Iniciando conciliacao (dry-run).")
        alunos = carregar_alunos(cfg)
        print(f"Alunos carregados: {len(alunos)}")

    arquivos = descobrir_arquivos(cfg)
    total_jpgs = sum(len(v) for v in arquivos.values())
    print(f"Pastas de temas: {len(arquivos)} | JPGs encontrados: {total_jpgs}")

    # Determinar codigos_site com fail-closed
    codigos_site = set()
    if args.analise_remota or args.envio_real or (args.modo_teste and args.envio_real):
        # Modos que exigem códigos do site reais: abortar se não tiver
        print("[ERRO] Códigos do site não disponíveis. Execute a análise remota primeiro para obter o combo de temas.")
        print("[ERRO] Use --analise-remota no mesmo dia para preencher dados/temas_site.csv.")
        return 2
    else:
        # Dry-run: usar dados/temas_site.csv como referência (pode estar vazio/desatualizado)
        temas_csv = Path("dados/temas_site.csv")
        if temas_csv.exists():
            import csv
            with open(temas_csv, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                codigos_site = {row["codigo"] for row in reader if row.get("codigo")}
            if codigos_site:
                print(f"[AVISO] Dry-run: usando {len(codigos_site)} códigos de dados/temas_site.csv (referência, pode estar desatualizado)")
            else:
                print("[AVISO] Dry-run: dados/temas_site.csv existe mas sem códigos válidos")
        else:
            print("[AVISO] Dry-run: dados/temas_site.csv não encontrado, sem validação de CODIGO_INVALIDO")

    resultado = conciliar(
        alunos, arquivos,
        codigos_site=codigos_site,
        limiar=cfg.limiar_fuzzy, margem=cfg.margem_minima,
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
    print()
    print(f"Relatorio CSV: {csv_path}")
    print(f"Fila dry-run:  {txt_path}")
    print()
    print("Revise o CSV antes de autorizar qualquer envio. Fuzzy/ambiguo/sem par")
    print("exigem revisao humana e nao entram na fila real.")
    return 0


if __name__ == "__main__":
    sys.exit(main())