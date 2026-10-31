"""Conferência manual guiada das contas com problema (issue #55).

Só lê o site (navegador VISÍVEL, uma conta por vez) e só mexe em dois lugares, sempre com a pessoa
confirmando olhando a conta aberta: o nome no ``alunos.csv`` (cópia antes) e os nomes das fotos
(com log; dá para desfazer em Manutenção > Desfazer renomeação). Nada é enviado.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator

from modulos.base import tela
from modulos.base.config import Config
from modulos.base.excecoes import CaptchaOuBloqueio, LoginFalhou
from modulos.dados.normalizacao import normalizar_nome
from modulos.dados.planilha_arquivos import Aluno, mascarar_email
from modulos.ferramentas.cadastro_aluno import trocar_nome
from modulos.site.conferencia_site import ConferenciaAluno

log = logging.getLogger("automacao_redacoes")
Entrada = Callable[[str], str] | None


@contextmanager
def conta_aberta(cfg: Config, aluno: Aluno) -> Iterator[str]:
    """Abre o navegador visível, entra na conta do aluno e entrega o nome que o site mostra no menu.
    Fecha tudo ao sair do ``with`` (a pessoa já respondeu)."""
    from playwright.sync_api import sync_playwright
    from modulos.site.login import DOMINIO_ESPERADO, login, logout, verificar_dominio_autorizado
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=cfg.slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            verificar_dominio_autorizado(page)
            login(page, cfg, aluno.email, aluno.senha)
            menu = page.locator(".navbar-right .dropdown-toggle")
            menu.first.wait_for(state="visible", timeout=10000)
            yield (menu.first.text_content() or "").strip()
        finally:
            try:
                logout(page)
                context.close()
                browser.close()
            except Exception:  # noqa: BLE001 - fechar não pode esconder a resposta da pessoa
                log.warning("Conferencia manual: nao fechou o navegador direito.")


def _sim(entrada: Entrada, texto: str) -> bool:
    return tela.perguntar(f"  {texto} (s/n): ", entrada).lower() in ("s", "sim")


def _renomear_fotos(cfg: Config, conf: ConferenciaAluno, novo: Aluno, log_csv: Path, saida: Callable) -> int:
    from modulos.ferramentas.revisao_interativa import renomear
    feitas = 0
    for item in conf.itens:
        nome, motivo = renomear(cfg.pasta_raiz, item.pasta, item.arquivo, novo, cfg.banco_progresso, log_csv)
        if nome:
            feitas += 1
            tela.ok(f"Foto renomeada: {item.pasta}/{item.arquivo} -> {nome}", saida)
        elif not motivo.startswith("ja esta"):
            tela.erro(f"Foto NÃO renomeada: {item.pasta}/{item.arquivo}: {motivo}", saida)
    return feitas


def _manual(cfg: Config, conf: ConferenciaAluno, entrada: Entrada, saida: Callable) -> bool:
    """A pessoa corrige o alunos.csv à mão. True = "deu certo"."""
    tela.info(f"Abra e corrija (Ctrl+clique): {tela.caminho(cfg.planilha)}", saida)
    r = tela.perguntar("  Conseguiu fazer a manutenção manual? (s = deu certo, continuar / n = pular este aluno): ", entrada)
    return r.lower() in ("s", "sim")


def conferir_manualmente(cfg: Config, problemas: list[ConferenciaAluno], entrada: Entrada = None,
                         saida: Callable = print, abrir: Callable = conta_aberta,
                         alunos: list[Aluno] | None = None) -> int:
    """Percorre as contas com problema. Retorna quantos cadastros mudaram (nome trocado ou corrigido à mão)."""
    if not _sim(entrada, f"Deseja fazer a conferência manual das {len(problemas)} conta(s) com problema agora?"):
        return 0
    from modulos.dados.planilha_arquivos import carregar_alunos
    alunos = alunos if alunos is not None else carregar_alunos(cfg)
    log_csv = Path(cfg.pasta_relatorios) / f"renomeacoes_{datetime.now():%Y%m%d_%H%M%S}.csv"
    mudaram = pulados = 0
    for i, conf in enumerate(problemas, 1):
        aluno = conf.aluno
        tela.cabecalho(f"CONTA {i} de {len(problemas)}:  {aluno.nome}  <{mascarar_email(aluno.email)}>", saida)
        tela.status("erro", conf.erro, saida, recuo=4)
        if conf.tipo_erro != "identidade" or not aluno.senha:
            # senha recusada (ou sem senha): não há conta aberta para olhar
            if _manual(cfg, conf, entrada, saida):
                mudaram += 1
            else:
                pulados += 1
            continue
        tela.info("Entrando no aluno para conferência manual...", saida)
        try:
            with abrir(cfg, aluno) as nome_site:
                tela.ok(f"Navegador aberto. Estamos logados na conta de: {nome_site or '(nome não apareceu)'}", saida)
                tela.status("fraco", f"Na lista (alunos.csv) o nome é: {aluno.nome}", saida, recuo=4)
                mesma = bool(nome_site) and _sim(entrada, "Esse aluno que apareceu no site é a mesma pessoa?")
        except CaptchaOuBloqueio as e:
            tela.erro(f"CAPTCHA/bloqueio ({e}): parei a conferência manual.", saida)
            break
        except LoginFalhou as e:
            tela.erro(f"O site não aceitou o login agora ({e}).", saida)
            mesma = None
        except Exception as e:  # noqa: BLE001 - uma conta não derruba as outras
            log.exception("Conferencia manual: erro em %s", aluno.nome)
            tela.erro(f"Não consegui abrir a conta ({type(e).__name__}).", saida)
            mesma = None
        if mesma:
            outros = [a for a in alunos if a.email.casefold() != aluno.email.casefold()]
            if any(a.nome_norm == normalizar_nome(nome_site) for a in outros):
                tela.erro("Já existe outro aluno com esse nome na lista (o site não distingue homônimos): "
                          "decida à mão.", saida)
                mesma = False
            else:
                try:
                    copia = trocar_nome(cfg.planilha, aluno.email, nome_site)
                except (OSError, ValueError, KeyError) as e:
                    tela.erro(f"Não consegui trocar o nome no alunos.csv ({type(e).__name__}): {e}", saida)
                    mesma = False
                else:
                    tela.ok(f"Nome na lista agora é igual ao do site (cópia: {copia.name}).", saida)
                    alunos[:] = [Aluno(nome_site, a.email, senha=a.senha) if a.email.casefold() == aluno.email.casefold()
                                 else a for a in alunos]  # as próximas checagens de homônimo já veem o nome novo
                    _renomear_fotos(cfg, conf, Aluno(nome_site, aluno.email, senha=aluno.senha), log_csv, saida)
                    mudaram += 1
                    continue
        if _manual(cfg, conf, entrada, saida):
            mudaram += 1
        else:
            pulados += 1
    tela.secao("Conferência manual", saida)
    tela.status("ok" if mudaram else "fraco", f"{mudaram} conta(s) corrigida(s), {pulados} pulada(s).", saida)
    if mudaram:
        tela.info(f"Renomeações guardadas em {tela.caminho(log_csv)} (Manutenção > Desfazer renomeação).", saida)
    return mudaram
