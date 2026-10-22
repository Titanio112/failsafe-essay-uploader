"""Análise remota (T27): atualiza dados/temas_site.csv lendo o combo do site.

Só leitura: login na CONTA DE TESTE (ou, com --conta-aluno, na conta de um
aluno da lista, T29: o combo do aluno pode ter temas que a de teste não tem),
abre /wordings/new, lê o combo
"Informe o tema da redação" e grava o CSV. Nada é anexado nem enviado.
Confirmação textual ANALISAR (digitada pelo Antônio). O CSV anterior vira
backup em dados/temas_site.<data_hora>.bak.csv. Combo vazio -> não grava.
"""

from __future__ import annotations

import csv
import logging
import shutil
from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from modulos.base.config import Config, obter_email_teste, obter_senha
from modulos.site.formulario_envio import abrir_formulario_envio, ler_combo_temas
from modulos.site.login import DOMINIO_ESPERADO, confirmar_identidade, login, verificar_dominio_autorizado
from modulos.dados.planilha_arquivos import Aluno, mascarar_email

log = logging.getLogger("automacao_redacoes")


def gravar_temas_csv(temas: list[tuple[str, str]], caminho: Path, conta: str) -> Path | None:
    """Grava (codigo, texto) mantendo repetidos (ex.: 0000 duas vezes).
    Faz backup do CSV anterior. Retorna o caminho do backup (ou None)."""
    caminho = Path(caminho)
    backup = None
    if caminho.is_file():
        backup = caminho.with_name(f"{caminho.stem}.{datetime.now():%Y%m%d_%H%M%S}.bak{caminho.suffix}")
        shutil.copy2(caminho, backup)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["codigo", "texto", "data_leitura", "conta_mascarada"])
        for codigo, texto in temas:
            escritor.writerow([codigo, texto, date.today().isoformat(), conta])
    return backup


def executar_analise_remota(cfg: Config, caminho_csv: Path, aluno: Aluno | None = None) -> int:
    """0 = CSV atualizado; 1 = falhou (CSV intacto); 2 = cancelado.
    ``aluno``: entra na conta desse aluno (senha ESQUEMA_SENHA_PADRAO)."""
    qual = f"do aluno {aluno.nome}" if aluno else "de TESTE"
    print(f"Analise remota: login na conta {qual}, leitura do combo de temas e")
    print(f"regravacao de {caminho_csv} (o atual vira backup). Nada e enviado.")
    try:
        confirmacao = input("Digite ANALISAR para confirmar (qualquer outro texto cancela): ").strip()
    except (EOFError, OSError):
        confirmacao = ""  # sem terminal para digitar: cancela
    if confirmacao != "ANALISAR":
        print("Cancelado pelo usuario.")
        return 2

    if aluno:
        email, senha = aluno.email, obter_senha("ESQUEMA_SENHA_PADRAO")
        esperado, modo_teste = aluno, False
    else:
        email = obter_email_teste()
        senha = obter_senha("ESQUEMA_SENHA_TESTE")
        esperado, modo_teste = Aluno(nome="Usuario Testes Ignorar", email=email), True
    conta = mascarar_email(email)
    antes = {c for c, _ in ler_temas_csv(caminho_csv)}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)
            login(page, cfg, email, senha)
            confirmar_identidade(page, esperado, modo_teste=modo_teste)
            abrir_formulario_envio(page)
            temas = ler_combo_temas(page)
        except Exception as e:
            log.error("Analise remota falhou: %s. %s ficou como estava.", type(e).__name__, caminho_csv)
            return 1
        finally:
            context.close()
            browser.close()

    if not temas:
        log.error("Combo de temas vazio. %s ficou como estava.", caminho_csv)
        return 1
    backup = gravar_temas_csv(temas, caminho_csv, conta)
    repetidos = sorted({c for c, _ in temas if [x for x, _ in temas].count(c) > 1})
    print(f"{len(temas)} tema(s) gravado(s) em {caminho_csv}.")
    if backup:
        print(f"Backup do anterior: {backup}")
    if repetidos:
        print(f"Codigos repetidos no combo (nunca enviados automaticamente): {repetidos}")
    agora = {c for c, _ in temas}
    if antes:
        print(f"Codigos novos em relacao ao CSV anterior: {sorted(agora - antes, key=_ordem) or 'nenhum'}")
        print(f"Codigos que sumiram: {sorted(antes - agora, key=_ordem) or 'nenhum'}")
    return 0


def _ordem(codigo: str) -> tuple[int, str]:
    return (int(codigo), codigo) if codigo.isdigit() else (0, codigo)


def ler_temas_csv(caminho: Path) -> list[tuple[str, str]]:
    from modulos.dados.sugestao_temas import ler_temas_site
    return ler_temas_site(caminho)
