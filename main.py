"""CLI: selecao de sala e orquestracao. Padrao: dry-run."""

from __future__ import annotations

import argparse
import sys
import logging

# Configuração de logging com UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuração de encoding para stdout e stderr
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path

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
)
from progresso_relatorio import (
    Progresso,
    configurar_logging,
    gerar_fila_dry_run,
    gerar_relatorio_conciliacao,
)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Automacao de redacoes — MVP")
    p.add_argument("--config", help="caminho do config.ini")
    p.add_argument("--sala", help="sala a processar (ex.: B)")
    p.add_argument("--envio-real", action="store_true",
                   help="habilita envio real (somente Fase 3+)")
    p.add_argument("--limite-alunos", type=int, default=None)
    p.add_argument("--limite-redacoes", type=int, default=None)
    return p.parse_args(argv)


def selecionar_sala(salas, sala_arg):
    if sala_arg:
        alvo = sala_arg.strip()
        if alvo not in salas:
            raise SystemExit(f"Sala {alvo!r} nao encontrada. Disponiveis: {salas}")
        return alvo
    print("Salas disponiveis:")
    for i, s in enumerate(salas, 1):
        print(f"  {i}. {s}")
    escolha = input("Numero da sala: ").strip()
    try:
        return salas[int(escolha) - 1]
    except (ValueError, IndexError):
        raise SystemExit("Selecao invalida.")


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

    log.info("Iniciando conciliacao (dry-run).")

    alunos = carregar_alunos(cfg)
    salas = sorted({a.sala for a in alunos})
    sala = selecionar_sala(salas, args.sala)
    alunos_sala = [a for a in alunos if a.sala == sala]
    print(f"Sala selecionada: {sala} ({len(alunos_sala)} aluno(s) na planilha)")

    arquivos = descobrir_arquivos(cfg)
    total_jpgs = sum(len(v) for v in arquivos.values())
    print(f"Pastas de temas: {len(arquivos)} | JPGs encontrados: {total_jpgs}")

    resultado = conciliar(
        alunos_sala, arquivos,
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