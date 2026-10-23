"""Conferência no site (T52): `python main.py --conferir-site`.

Só leitura. Para cada aluno com redação conferida na pasta, entra na conta
dele (senha ESQUEMA_SENHA_PADRAO), lê Minhas redações e compara com as fotos
da pasta: o tema já está no site (qualquer data) ou ainda não. Nada é
anexado, clicado em "Enviar" nem gravado no caderno; o resultado vai para a
tela e para relatorios/conferencia_site_<data>.csv.

Confirmação textual CONFERIR (digitada pelo Antônio). Mesmas travas do envio
para o navegador: um aluno por contexto, domínio exato, identidade conferida,
CAPTCHA ou 2 logins falhando seguidos param tudo.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from modulos.base import relogio, tela
from modulos.base.config import Config, obter_senha
from modulos.base.excecoes import CaptchaOuBloqueio, IdentidadeDivergente, LoginFalhou
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao, mascarar_email
from modulos.site.lista_redacoes import ItemListaRedacao

log = logging.getLogger("automacao_redacoes")

PALAVRA = "CONFERIR"
NO_SITE, EM_PARTE, FORA_DO_SITE, NAO_CONFERIDO = "no site", "em parte", "não está no site", "não conferido"
COLUNAS_CSV = ["aluno", "pasta", "arquivo", "tema", "resultado", "no_site", "datas_no_site", "situacoes"]


@dataclass
class ConferenciaAluno:
    aluno: Aluno
    itens: list[ItemConciliacao]
    lista: list[ItemListaRedacao] | None = None  # None = não conseguiu ler
    erro: str = ""
    linhas: list[tuple[ItemConciliacao, str, list[ItemListaRedacao]]] = field(default_factory=list)


def alunos_para_conferir(resultado: ResultadoConciliacao) -> list[ConferenciaAluno]:
    """Alunos com foto conferida (nome exato + tema), na ordem dos nomes."""
    por_aluno: dict[str, ConferenciaAluno] = {}
    for item in resultado.fila_validada():
        if item.aluno and item.codigo_tema:
            por_aluno.setdefault(item.aluno.id, ConferenciaAluno(item.aluno, [])).itens.append(item)
    return sorted(por_aluno.values(), key=lambda c: c.aluno.nome)


def comparar(conf: ConferenciaAluno) -> None:
    """Preenche ``conf.linhas``: para cada foto, o tema já está no site?

    Vale o tema em qualquer data. Várias fotos do mesmo tema (ex.: genérico
    000): com N linhas no site, as N primeiras contam como "no site" e o
    resto como "em parte" (não dá para saber qual foto é qual)."""
    conf.linhas = []
    if conf.lista is None:
        conf.linhas = [(item, NAO_CONFERIDO, []) for item in conf.itens]
        return
    vistos: dict[str, int] = {}
    for item in conf.itens:
        do_tema = [r for r in conf.lista if r.codigo == item.codigo_tema]
        vistos[item.codigo_tema] = vistos.get(item.codigo_tema, 0) + 1
        if not do_tema:
            estado = FORA_DO_SITE
        elif vistos[item.codigo_tema] <= len(do_tema):
            estado = NO_SITE
        else:
            estado = EM_PARTE
        conf.linhas.append((item, estado, do_tema))


def _ler_conta(page, cfg: Config, senha: str, aluno: Aluno) -> list[ItemListaRedacao]:
    from modulos.site.lista_redacoes import ler_lista_redacoes
    from modulos.site.login import DOMINIO_ESPERADO, confirmar_identidade, login, verificar_dominio_autorizado
    page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    login(page, cfg, aluno.email, senha)
    confirmar_identidade(page, aluno)
    return ler_lista_redacoes(page)


def _ler_no_navegador(cfg: Config, conferencias: list[ConferenciaAluno], senha: str,
                      saida: Callable = print) -> bool:
    """Lê a lista de cada aluno. Retorna True se parou antes do fim."""
    from playwright.sync_api import sync_playwright
    from modulos.envio.fluxo_envio_producao import MAX_FALHAS_LOGIN_SEGUIDAS, Andamento, _motivo_login
    andamento = Andamento(len(conferencias), saida, unidade="alunos")
    falhas = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        try:
            for n, conf in enumerate(conferencias, 1):
                log.info("Conferencia no site %d de %d: %s", n, len(conferencias), conf.aluno.nome)
                context = browser.new_context()  # um aluno por contexto: nada de sessão misturada
                page = context.new_page()
                try:
                    conf.lista = _ler_conta(page, cfg, senha, conf.aluno)
                    falhas = 0
                except CaptchaOuBloqueio as e:
                    conf.erro = f"CAPTCHA/bloqueio: {e}"
                    log.error("Captcha/bloqueio na conta de %s. Parando a conferencia.", conf.aluno.nome)
                    return True
                except (LoginFalhou, IdentidadeDivergente) as e:
                    conf.erro = _motivo_login(e)
                    falhas += 1
                    log.error("Conferencia: %s (%s): %s", conf.aluno.nome, mascarar_email(conf.aluno.email),
                              conf.erro)
                except RuntimeError as e:  # lista ilegível (página de erro, outra página)
                    conf.erro = f"lista ilegível ({e})"
                    falhas += 1
                    log.error("Conferencia: %s (%s): %s", conf.aluno.nome, mascarar_email(conf.aluno.email),
                              conf.erro)
                except Exception as e:  # noqa: BLE001 - um aluno não derruba a conferência
                    conf.erro = f"erro inesperado ({type(e).__name__})"
                    falhas += 1
                    log.exception("Conferencia: erro inesperado em %s", conf.aluno.nome)
                finally:
                    context.close()
                comparar(conf)
                _mostrar_aluno(conf, cfg.pasta_raiz, saida)
                andamento.avancar()
                if falhas >= MAX_FALHAS_LOGIN_SEGUIDAS:
                    tela.erro(f"{falhas} contas seguidas não abriram: parei (senha padrão errada? site fora?).",
                              saida)
                    return True
        finally:
            browser.close()
    return False


def _mostrar_aluno(conf: ConferenciaAluno, pasta_raiz: Path, saida: Callable = print) -> None:
    saida(f"  {tela.c(conf.aluno.nome, 'titulo')} {tela.c(f'<{mascarar_email(conf.aluno.email)}>', 'fraco')}")
    if conf.erro:
        tela.status("erro", f"não conferido: {conf.erro}", saida, recuo=4)
        return
    papel = {NO_SITE: "ok", EM_PARTE: "aviso", FORA_DO_SITE: "info"}
    for item, estado, do_tema in conf.linhas:
        quando = ", ".join(sorted({r.data for r in do_tema if r.data}))
        extra = f" ({quando})" if quando else ""
        arquivo = tela.link_arquivo(pasta_raiz, item.pasta, item.arquivo)
        tela.status(papel.get(estado, "fraco"), f"tema {item.codigo_tema}: {estado}{extra}  {arquivo}",
                    saida, recuo=4)


def gravar_csv(conferencias: list[ConferenciaAluno], pasta: Path) -> Path:
    caminho = Path(pasta) / f"conferencia_site_{relogio.agora():%Y%m%d_%H%M%S}.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(COLUNAS_CSV)
        for conf in conferencias:
            linhas = conf.linhas or [(item, NAO_CONFERIDO, []) for item in conf.itens]
            for item, estado, do_tema in linhas:
                escritor.writerow([conf.aluno.nome, item.pasta, item.arquivo, item.codigo_tema,
                                   conf.erro and NAO_CONFERIDO or estado, len(do_tema),
                                   " | ".join(r.data for r in do_tema),
                                   " | ".join(r.situacao for r in do_tema)])
    return caminho


def executar_conferencia_site(cfg: Config, resultado: ResultadoConciliacao,
                              entrada: Callable[[str], str] | None = None, saida: Callable = print,
                              ler: Callable | None = None) -> int:
    """0 = conferido até o fim; 1 = parou antes; 2 = cancelado/nada a conferir.
    ``ler`` (testes): substitui o navegador (recebe cfg, conferências, senha, saida)."""
    from modulos.base.trava import TravaOcupada, trava_de_envio
    conferencias = alunos_para_conferir(resultado)
    tela.titulo("CONFERÊNCIA NO SITE  ·  só leitura, nada é enviado", saida)
    if not conferencias:
        tela.aviso("Nenhuma redação conferida na pasta (nome exato + tema aprovado). Rode a revisão antes.", saida)
        return 2
    total = sum(len(c.itens) for c in conferencias)
    tela.texto(f"Vou entrar na conta de {len(conferencias)} aluno(s), ler Minhas redações e comparar com as "
               f"{total} foto(s) da pasta. Não anexo nem envio nada, e o caderno de envios não muda.", saida)
    tela.status("fraco", "Usa a senha padrão (ESQUEMA_SENHA_PADRAO). CAPTCHA ou 2 contas seguidas sem abrir: para.",
                saida)
    saida("")
    if tela.perguntar(f"  Digite {tela.c(PALAVRA, 'tecla')} para começar (qualquer outro texto cancela): ",
                      entrada) != PALAVRA:
        tela.aviso("Cancelado: nenhuma conta foi aberta.", saida)
        return 2
    tela.secao("Conferindo", saida)
    try:
        with trava_de_envio(Path(cfg.pasta_relatorios) / "envio.trava"):
            senha = obter_senha("ESQUEMA_SENHA_PADRAO")
            parou = (ler or _ler_no_navegador)(cfg, conferencias, senha, saida)
    except TravaOcupada:
        tela.erro("Um envio está rodando agora (outra janela?). Espere ele acabar.", saida)
        return 2

    contagem = {NO_SITE: 0, EM_PARTE: 0, FORA_DO_SITE: 0, NAO_CONFERIDO: 0}
    for conf in conferencias:
        if not conf.linhas:
            comparar(conf)
        for _, estado, _ in conf.linhas:
            contagem[NAO_CONFERIDO if conf.erro else estado] += 1
    tela.secao("Resumo da conferência no site", saida)
    tela.contagens([("Já estão no site", contagem[NO_SITE], "ok"),
                    ("Tema no site, mas menos vezes que as fotos", contagem[EM_PARTE], "aviso"),
                    ("Ainda não estão no site", contagem[FORA_DO_SITE], "info"),
                    ("Não conferidas (conta não abriu)", contagem[NAO_CONFERIDO], "erro")], saida)
    if parou:
        tela.erro("Conferência PARADA antes do fim (veja o motivo acima).", saida)
    tela.info(f"Relatório: {tela.caminho(gravar_csv(conferencias, cfg.pasta_relatorios))}", saida)
    tela.status("fraco", "Nada foi enviado e o caderno não mudou.", saida)
    return 1 if parou else 0
