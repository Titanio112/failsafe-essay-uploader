"""Conferência no site (T52): `python main.py --conferir-site`.

Só leitura. Para cada aluno com redação conferida na pasta, entra na conta
dele (M3: senha dele no alunos.csv da turma), lê Minhas redações e compara com as fotos
da pasta: o tema já está no site (qualquer data) ou ainda não. Nada é
anexado, clicado em "Enviar" nem gravado no caderno; o resultado vai para a
tela e para relatorios/conferencia_site_<data>.csv.

Confirmação textual CONFERIR (digitada pelo Antônio). Mesmas travas do envio
para o navegador: um aluno por contexto, domínio exato, identidade conferida.
CAPTCHA/bloqueio ou o site fora do ar (3 erros de site seguidos) param tudo; senha recusada
e identidade divergente só marcam o aluno.
"""

from __future__ import annotations

import csv
import logging
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from modulos.base import pendencias, relogio, tela
from modulos.base.config import Config
from modulos.base.excecoes import CaptchaOuBloqueio, IdentidadeDivergente, LoginFalhou
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao, mascarar_email
from modulos.site.confirmacao import logout
from modulos.site.lista_redacoes import ItemListaRedacao

log = logging.getLogger("automacao_redacoes")

PALAVRA = "CONFERIR"
# Senha recusada e identidade divergente são erro de CADASTRO (o site respondeu): marcam o aluno e seguem.
# Só param a conferência CAPTCHA/bloqueio e o site que não responde (erros seguidos que não são de cadastro).
MAX_ERROS_DE_SITE_SEGUIDOS = 3
NO_SITE, EM_PARTE, FORA_DO_SITE, NAO_CONFERIDO = "no site", "em parte", "não está no site", "não conferido"
OUTRO_TEMA = "talvez no site com outro tema"
NAO_TENTADO = "não tentado"  # T56: a conferência parou antes de chegar no aluno
CANCELADA = "cancelada no site (conferir)"  # bug 018
COLUNAS_CSV = ["aluno", "pasta", "arquivo", "tema", "resultado", "no_site", "datas_no_site", "situacoes",
               "turma"]  # M3: "Enviar as que faltam" só usa relatório da mesma turma


@dataclass
class ConferenciaAluno:
    aluno: Aluno
    itens: list[ItemConciliacao]
    lista: list[ItemListaRedacao] | None = None  # None = não conseguiu ler
    erro: str = ""
    tipo_erro: str = ""  # "identidade" | "login" | "" (issue #55: a conferência manual trata cada um)
    linhas: list[tuple[ItemConciliacao, str, list[ItemListaRedacao]]] = field(default_factory=list)
    reaproveitada: list[dict] | None = None  # linhas da conferência de hoje reaproveitadas, sem abrir a conta (#57)


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
    if conf.lista is None:  # T56: sem erro = a conferência parou antes deste aluno
        estado = NAO_CONFERIDO if conf.erro else NAO_TENTADO
        conf.linhas = [(item, estado, []) for item in conf.itens]
        return
    # Bug 018: "Cancelada" não conta como no site (o envio também não conta);
    # só cancelada no tema = conferir à mão, nunca entra sozinha no envio.
    ativas = [r for r in conf.lista if r.situacao.strip().lower() != "cancelada"]
    vistos: dict[str, int] = {}
    for item in conf.itens:
        do_tema = [r for r in ativas if r.codigo == item.codigo_tema]
        vistos[item.codigo_tema] = vistos.get(item.codigo_tema, 0) + 1
        if not do_tema:
            canceladas = [r for r in conf.lista if r.codigo == item.codigo_tema]
            estado, do_tema = (CANCELADA, canceladas) if canceladas else (FORA_DO_SITE, [])
        elif vistos[item.codigo_tema] <= len(do_tema):
            estado = NO_SITE
        else:
            estado = EM_PARTE
        conf.linhas.append((item, estado, do_tema))
    # T53: tema que "não está no site" enquanto o site tem redações A MAIS de
    # outro tema (do que fotos na pasta) provavelmente foi mandado com esse
    # outro tema (23/10: 28 do tema 100 estavam no site como 000). Nunca
    # contar como "falta enviar".
    locais: dict[str, int] = {}
    for item in conf.itens:
        locais[item.codigo_tema] = locais.get(item.codigo_tema, 0) + 1
    sobra: dict[str, int] = {}
    for r in ativas:
        sobra[r.codigo] = sobra.get(r.codigo, 0) + 1
    for codigo, n in locais.items():
        if codigo in sobra:
            sobra[codigo] -= n
    # T56 (revisão): fail-closed. Com QUALQUER sobra, TODAS as "não está" do
    # aluno viram "outro tema?" (não só tantas quanto a sobra): as fotos do
    # genérico 000 na pasta podem ter "gastado" linhas que eram de outro
    # tema, e aí uma foto já enviada pareceria faltando.
    sobras = sorted(c for c, n in sobra.items() if n > 0)
    if not sobras:
        return
    for i, (item, estado, do_tema) in enumerate(conf.linhas):
        if estado == FORA_DO_SITE:
            conf.linhas[i] = (item, OUTRO_TEMA, [r for r in ativas if r.codigo in sobras])


def contas_com_problema(conferencias: list[ConferenciaAluno]) -> list[ConferenciaAluno]:
    """Contas que não abriram (senha recusada, identidade divergente...): precisam de cadastro corrigido."""
    return [c for c in conferencias if c.erro]


def faltam_enviar(conferencias: list[ConferenciaAluno]) -> list[ItemConciliacao]:
    """Só as fotos que certamente não estão no site (conta lida sem erro)."""
    return [item for conf in conferencias if not conf.erro
            for item, estado, _ in conf.linhas if estado == FORA_DO_SITE]


def _ler_conta(page, cfg: Config, aluno: Aluno) -> list[ItemListaRedacao]:
    from modulos.site.lista_redacoes import ler_lista_redacoes
    from modulos.site.login import DOMINIO_ESPERADO, confirmar_identidade, login, verificar_dominio_autorizado
    page.goto(f"https://{DOMINIO_ESPERADO}", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    login(page, cfg, aluno.email, aluno.senha)  # M3: a senha do próprio aluno
    confirmar_identidade(page, aluno)
    return ler_lista_redacoes(page)


def _ler_no_navegador(cfg: Config, conferencias: list[ConferenciaAluno], saida: Callable = print) -> bool:
    """Lê a lista de cada aluno. Retorna True se parou antes do fim."""
    from playwright.sync_api import sync_playwright
    from modulos.envio.fluxo_envio_producao import Andamento, _motivo_login
    andamento = Andamento(len(conferencias), saida, unidade="alunos")
    falhas = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        try:
            for n, conf in enumerate(conferencias, 1):
                log.info("Conferencia no site %d de %d: %s", n, len(conferencias), conf.aluno.nome,
                         extra={"so_no_arquivo": True})  # T54: a tela já mostra o aluno
                context = browser.new_context()  # um aluno por contexto: nada de sessão misturada
                page = None
                try:
                    page = context.new_page()  # T56: dentro do try (navegador caído = erro do aluno)
                    conf.lista = _ler_conta(page, cfg, conf.aluno)
                    falhas = 0
                except CaptchaOuBloqueio as e:
                    conf.erro = f"CAPTCHA/bloqueio: {e}"
                    log.error("Captcha/bloqueio na conta de %s. Parando a conferencia.", conf.aluno.nome)
                    return True
                except (LoginFalhou, IdentidadeDivergente) as e:
                    conf.erro = _motivo_login(e)
                    conf.tipo_erro = "identidade" if isinstance(e, IdentidadeDivergente) else "login"
                    falhas = 0  # o site respondeu: o problema é o cadastro deste aluno, não derruba os outros
                    log.error("Conferencia: %s (%s): %s", conf.aluno.nome, mascarar_email(conf.aluno.email),
                              conf.erro, extra={"so_no_arquivo": True})  # a tela já mostra o erro do aluno (uma vez)
                except RuntimeError as e:  # lista ilegível (página de erro, outra página)
                    conf.erro = f"lista ilegível ({e})"
                    falhas += 1
                    log.error("Conferencia: %s (%s): %s", conf.aluno.nome, mascarar_email(conf.aluno.email),
                              conf.erro, extra={"so_no_arquivo": True})
                except Exception as e:  # noqa: BLE001 - um aluno não derruba a conferência
                    conf.erro = f"erro inesperado ({type(e).__name__})"
                    falhas += 1
                    log.exception("Conferencia: erro inesperado em %s", conf.aluno.nome,
                                  extra={"so_no_arquivo": True})
                finally:
                    # T56: sair da conta e fechar sem deixar um erro aqui esconder o de cima
                    try:
                        if page is not None:
                            logout(page)
                        context.close()
                    except Exception:  # noqa: BLE001
                        log.warning("Conferencia: nao fechou o navegador de %s direito.", conf.aluno.nome)
                comparar(conf)
                _mostrar_aluno(conf, cfg.pasta_raiz, saida)
                andamento.avancar()
                if falhas >= MAX_ERROS_DE_SITE_SEGUIDOS:
                    tela.erro(f"{falhas} contas seguidas deram erro do site (fora do ar? internet?): parei. "
                              "Quem ainda não foi lido aparece como \"não tentado\".", saida)
                    return True
        finally:
            browser.close()
    return False


# T54: uma linha curta por foto, em colunas, sem quebrar no terminal
#   ✔ no site      tema 000  30/09/2026    3B - Efeitos da aporofobia
#   ⚠ outro tema?  tema 100  como 000?     3B - Impactos da Invisibilidade…
ROTULO_CURTO = {NO_SITE: "no site", EM_PARTE: "em parte", FORA_DO_SITE: "falta",
                OUTRO_TEMA: "outro tema?", NAO_CONFERIDO: "não conferido", NAO_TENTADO: "não tentado",
                CANCELADA: "cancelada?"}
PAPEL = {NO_SITE: "ok", EM_PARTE: "aviso", FORA_DO_SITE: "info", OUTRO_TEMA: "aviso", CANCELADA: "aviso"}


def _curto(texto: str, largura: int) -> str:
    return texto if len(texto) <= largura else texto[:max(largura - 1, 1)] + "…"


def _erro_inteiro(texto: str, saida: Callable, recuo: int = 4) -> None:
    """Linha de erro que quebra na largura da tela em vez de cortar com "…"."""
    linhas = textwrap.wrap(texto, tela.LARGURA - recuo - 2) or [""]
    tela.status("erro", linhas[0], saida, recuo=recuo)
    for linha in linhas[1:]:
        saida(" " * (recuo + 2) + tela.c(linha, "erro"))


def _mostrar_aluno(conf: ConferenciaAluno, pasta_raiz: Path, saida: Callable = print) -> None:
    saida("")
    saida(f"  {tela.c(conf.aluno.nome, 'titulo')}  {tela.c(f'<{mascarar_email(conf.aluno.email)}>', 'fraco')}")
    if conf.erro:
        _erro_inteiro(f"não conferido: {conf.erro}", saida)
        return
    for item, estado, do_tema in conf.linhas:
        datas = sorted({r.data for r in do_tema if r.data})
        if estado == OUTRO_TEMA and do_tema:
            detalhe = f"como {do_tema[0].codigo}?"
        elif datas:
            detalhe = datas[0] + ("+" if len(datas) > 1 else "")
        else:
            detalhe = ""
        inicio = f"{ROTULO_CURTO.get(estado, estado):<12} tema {item.codigo_tema:<4} {detalhe:<12}  "
        sobra = tela.LARGURA - 6 - len(inicio)
        # o nome do arquivo é o do aluno (já está em cima): só a pasta, que abre a foto
        pasta = tela.link(_curto(item.pasta, sobra), Path(pasta_raiz) / item.pasta / item.arquivo)
        tela.status(PAPEL.get(estado, "fraco"), inicio + pasta, saida, recuo=4)


GRUPOS_DE_PROBLEMA = (("Senha ou login recusado pelo site", "login"),
                      ("Nome no site diferente do nome na lista", "identidade"),
                      ("Outros problemas", ""))


def _mostrar_problemas(problemas: list[ConferenciaAluno], saida: Callable = print) -> None:
    """"Contas que precisam de atenção", em grupos e com a mensagem inteira."""
    tela.secao(f"Contas que precisam de atenção ({len(problemas)})", saida)
    for titulo, tipo in GRUPOS_DE_PROBLEMA:
        do_grupo = [c for c in problemas if c.tipo_erro == tipo]
        if do_grupo:
            saida("")
            saida("  " + tela.c(f"{titulo} ({len(do_grupo)})", "titulo"))
            for c in do_grupo:
                _erro_inteiro(f"{c.aluno.nome}: {c.erro}", saida)


def gravar_csv(conferencias: list[ConferenciaAluno], pasta: Path, turma: str = "") -> Path:
    caminho = Path(pasta) / f"conferencia_site_{relogio.agora():%Y%m%d_%H%M%S}.csv"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(COLUNAS_CSV)
        for conf in conferencias:
            if not conf.linhas:
                comparar(conf)
            for linha in conf.reaproveitada or []:  # conta não aberta agora: as linhas de hoje, como estavam
                escritor.writerow([linha[c] for c in COLUNAS_CSV])
            for item, estado, do_tema in [] if conf.reaproveitada else conf.linhas:
                escritor.writerow([conf.aluno.nome, item.pasta, item.arquivo, item.codigo_tema,
                                   conf.erro and NAO_CONFERIDO or estado, len(do_tema),
                                   " | ".join(r.data for r in do_tema),
                                   " | ".join(r.situacao for r in do_tema), turma])
    return caminho


def faltantes_do_relatorio(pasta_relatorios: Path, resultado: ResultadoConciliacao,
                           saida: Callable = print, turma: str | None = None) -> list[ItemConciliacao] | None:
    """T54 (Enviar as que faltam): as que faltam segundo a conferência de HOJE, sem refazê-la.

    Só vale relatório de hoje (Brasília): de outro dia, alguém pode ter
    mandado à mão depois. Só entram fotos que continuam conferidas na pasta
    (mesma pasta, mesmo arquivo, mesmo aluno). None = sem relatório válido.
    ``turma`` (M3): toda linha tem de ser desta turma."""
    hoje = relogio.agora().strftime("%Y%m%d")
    relatorios = sorted(Path(pasta_relatorios).glob("conferencia_site_*.csv"))
    if not relatorios:
        tela.aviso("Ainda não há conferência no site. Faça antes \"Conferir contas no site\" (Preparar).", saida)
        return None
    ultimo = relatorios[-1]
    if not ultimo.name.startswith(f"conferencia_site_{hoje}"):
        tela.aviso(f"A última conferência ({tela.caminho(ultimo)}) não é de hoje.", saida)
        tela.status("fraco", "Alguém pode ter enviado à mão depois dela. Faça \"Conferir contas no site\" de novo.", saida)
        return None
    try:  # T56: relatório mexido no Excel (outra codificação, vírgulas) -> não usa
        with open(ultimo, encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";")
            if leitor.fieldnames != COLUNAS_CSV:
                raise ValueError("colunas diferentes")
            linhas = list(leitor)
            # T56: o tema também tem de bater (pasta reaprovada com outro tema
            # depois da conferência = tema que a conferência não olhou)
            faltando = {(l["aluno"], l["pasta"], l["arquivo"], l["tema"]) for l in linhas
                        if l.get("resultado") == FORA_DO_SITE}
    except (OSError, UnicodeDecodeError, ValueError, KeyError, csv.Error) as e:
        tela.aviso(f"Não consegui ler {tela.caminho(ultimo)} ({type(e).__name__}). Faça \"Conferir contas no site\" de novo.", saida)
        return None
    if turma is not None and any(l["turma"] != turma for l in linhas):
        tela.aviso(f"{tela.caminho(ultimo)} é de outra turma. Faça \"Conferir contas no site\" nesta turma.", saida)
        return None
    tela.info(f"Conferência usada: {tela.caminho(ultimo)}", saida)
    return [item for item in resultado.fila_validada()
            if item.aluno and item.codigo_tema
            and (item.aluno.nome, item.pasta, item.arquivo, item.codigo_tema) in faltando]


def _linhas_de_hoje(pasta_relatorios: Path, turma: str) -> tuple[list[dict] | None, str]:
    """(linhas, motivo): as linhas da conferência no site DE HOJE desta turma, ou (None, por que não valem)."""
    hoje = relogio.agora().strftime("%Y%m%d")
    relatorios = sorted(Path(pasta_relatorios).glob("conferencia_site_*.csv"))
    if not relatorios or not relatorios[-1].name.startswith(f"conferencia_site_{hoje}"):
        return None, "falta conferir as contas no site hoje"
    try:
        with open(relatorios[-1], encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f, delimiter=";")
            if leitor.fieldnames != COLUNAS_CSV:
                raise ValueError("colunas diferentes")
            linhas = list(leitor)
    except (OSError, UnicodeDecodeError, ValueError, csv.Error):
        return None, "não consegui ler a conferência de hoje"
    if not linhas:
        return None, "a conferência de hoje não tem nenhuma redação"
    if any(l["turma"] != turma for l in linhas):
        return None, "a conferência de hoje é de outra turma"
    return linhas, ""


def preparacao_concluida(pasta_relatorios: Path, turma: str) -> tuple[bool, str]:
    """A trava do Enviar no menu (#53): (ok, motivo). Só vale a conferência no site DE HOJE desta turma, completa:
    nenhuma conta "não conferida" nem "não tentada". Só lê o relatório; nada é enviado."""
    linhas, motivo = _linhas_de_hoje(pasta_relatorios, turma)
    if linhas is None:
        return False, motivo
    pendentes = [l for l in linhas if l["resultado"] in (NAO_CONFERIDO, NAO_TENTADO)]
    if pendentes:
        contas = len({l["aluno"] for l in pendentes})
        return False, (f"restam {contas} conta(s) sem conferir ({len(pendentes)} redação(ões)): use "
                       "\"Conferir contas no site\" (ele confere só as pendentes e abre a conferência manual)")
    return True, ""


def contas_pendentes_hoje(pasta_relatorios: Path, turma: str) -> int:
    """Quantas contas a conferência de hoje deixou "não conferidas" ou "não tentadas" (0 = nenhuma ou sem relatório)."""
    linhas, _ = _linhas_de_hoje(pasta_relatorios, turma)
    return len({l["aluno"] for l in linhas or [] if l["resultado"] in (NAO_CONFERIDO, NAO_TENTADO)})


def _reaproveitaveis(linhas: list[dict], conferencias: list[ConferenciaAluno]) -> dict[str, list[dict]]:
    """{aluno.id: linhas de hoje} das contas já conferidas SEM erro e com as mesmas fotos (pasta, arquivo, tema).
    Aluno renomeado ou foto trocada/renomeada não casa e é lido de novo."""
    por_aluno: dict[str, list[dict]] = {}
    for l in linhas:
        por_aluno.setdefault(l["aluno"], []).append(l)
    achados = {}
    for conf in conferencias:
        antigas = por_aluno.get(conf.aluno.nome, [])
        fotos = {(i.pasta, i.arquivo, i.codigo_tema) for i in conf.itens}
        if (antigas and len(antigas) == len(conf.itens) == len(fotos)
                and {(l["pasta"], l["arquivo"], l["tema"]) for l in antigas} == fotos
                and not any(l["resultado"] in (NAO_CONFERIDO, NAO_TENTADO) for l in antigas)):
            achados[conf.aluno.id] = antigas
    return achados


def _contas_a_ler(cfg: Config, conferencias: list[ConferenciaAluno], so_pendentes: bool | None,
                  entrada: Callable[[str], str] | None, saida: Callable) -> list[ConferenciaAluno]:
    """As contas que serão abertas. Com a conferência de HOJE desta turma já feita, pode reaproveitar as contas
    conferidas e ler só as pendentes (issue #57). ``so_pendentes``: True, False ou None (pergunta, só com pessoa)."""
    if so_pendentes is False:
        return conferencias
    linhas, _ = _linhas_de_hoje(cfg.pasta_relatorios, cfg.id_turma)
    achados = _reaproveitaveis(linhas, conferencias) if linhas else {}
    a_ler = [c for c in conferencias if c.aluno.id not in achados]
    if not achados:
        if so_pendentes:
            tela.info("Não há conferência de hoje para reaproveitar: vou conferir todas as contas.", saida)
        return conferencias
    if not a_ler:
        if so_pendentes:
            tela.ok("Todas as contas já foram conferidas hoje: nada pendente.", saida)
            return []
        return conferencias
    if so_pendentes is None:
        if entrada is None and not sys.stdin.isatty():
            return conferencias
        if not tela.sim(f"Já há uma conferência de hoje: {len(achados)} conta(s) conferida(s) e {len(a_ler)} "
                        "pendente(s). Conferir só as pendentes?", entrada):
            return conferencias
    for conf in conferencias:
        antigas = achados.get(conf.aluno.id)
        if antigas:
            estado_de = {(l["pasta"], l["arquivo"], l["tema"]): l["resultado"] for l in antigas}
            conf.reaproveitada, conf.lista = antigas, []
            conf.linhas = [(i, estado_de[(i.pasta, i.arquivo, i.codigo_tema)], []) for i in conf.itens]
    tela.info(f"Reaproveitei a conferência de hoje de {len(achados)} conta(s); vou abrir só as {len(a_ler)} "
              "pendente(s).", saida)
    return a_ler


def nada_falta_enviar(pasta_relatorios: Path, turma: str) -> str:
    """Motivo (texto) se a conferência de hoje não achou nenhuma redação faltando no site; "" nos outros casos."""
    linhas, _ = _linhas_de_hoje(pasta_relatorios, turma)
    if linhas and not any(l["resultado"] == FORA_DO_SITE for l in linhas):
        return f"nada falta enviar: nenhuma das {len(linhas)} redações conferidas está ausente do site"
    return ""


def executar_conferencia_site(cfg: Config, resultado: ResultadoConciliacao,
                              entrada: Callable[[str], str] | None = None, saida: Callable = print,
                              ler: Callable | None = None,
                              depois: Callable[[list[ItemConciliacao]], object] | None = None,
                              guiada: Callable[[list[ConferenciaAluno]], int] | None = None,
                              so_pendentes: bool | None = None) -> int:
    """0 = conferido até o fim; 1 = parou antes; 2 = cancelado/nada a conferir.
    ``ler`` (testes): substitui o navegador (recebe cfg, conferências, saida).
    ``depois`` (T53): recebe as fotos que certamente faltam no site, para
    oferecer o envio só delas (o main decide; aqui nada é enviado).
    ``guiada`` (#55): recebe as contas com problema para a conferência manual; devolve quantos cadastros
    mudaram (se mudou algum, a conferência feita aqui já não vale: não oferece enviar).
    ``so_pendentes`` (#57): True = só as contas que a conferência de hoje não leu; None = pergunta."""
    from modulos.base.trava import TravaOcupada, trava_de_envio
    conferencias = alunos_para_conferir(resultado)
    pendencias.cadastro_mudou = False
    tela.titulo("CONFERÊNCIA NO SITE  ·  só leitura, nada é enviado", saida)
    if not conferencias:
        tela.aviso("Nenhuma redação conferida na pasta (nome exato + tema aprovado). Rode a revisão antes.", saida)
        return 2
    a_ler = _contas_a_ler(cfg, conferencias, so_pendentes, entrada, saida)
    if not a_ler:
        return 0
    total = sum(len(c.itens) for c in a_ler)
    tela.texto(f"Vou entrar na conta de {len(a_ler)} aluno(s), ler Minhas redações e comparar com as "
               f"{total} foto(s) da pasta. Não anexo nem envio nada, e o caderno de envios não muda.", saida)
    tela.status("fraco", "Cada aluno com a senha dele (alunos.csv). Conta que não abre é marcada e a conferência segue; "
                "só CAPTCHA/bloqueio ou o site fora do ar param.", saida)
    saida("")
    if tela.perguntar(f"  Digite {tela.c(PALAVRA, 'tecla')} para começar (qualquer outro texto cancela): ",
                      entrada) != PALAVRA:
        tela.aviso("Cancelado: nenhuma conta foi aberta.", saida)
        return 2
    tela.secao("Conferindo", saida)
    try:
        with trava_de_envio(Path(cfg.banco_progresso).parent / "envio.trava"):  # M3: trava global
            # M3: sem senha no alunos.csv a conta nem é aberta
            for conf in a_ler:
                if not conf.aluno.senha:
                    conf.erro = "sem senha no alunos.csv da turma"
                    _mostrar_aluno(conf, cfg.pasta_raiz, saida)
            try:
                parou = (ler or _ler_no_navegador)(cfg, [c for c in a_ler if not c.erro], saida)
            except Exception as e:  # noqa: BLE001 - T56: o que já foi lido ainda vai para o relatório
                log.exception("Conferencia: parou com erro inesperado")
                tela.erro(f"Erro inesperado ({type(e).__name__}): a conferência parou.", saida)
                parou = True
    except TravaOcupada:
        tela.erro("Um envio está rodando agora (outra janela?). Espere ele acabar.", saida)
        return 2

    contagem = {NO_SITE: 0, EM_PARTE: 0, FORA_DO_SITE: 0, OUTRO_TEMA: 0, CANCELADA: 0, NAO_CONFERIDO: 0,
                NAO_TENTADO: 0}
    for conf in conferencias:
        if not conf.linhas:
            comparar(conf)
        for _, estado, _ in conf.linhas:
            contagem[NAO_CONFERIDO if conf.erro else estado] += 1
    log.info("Conferencia no site: %s%s", ", ".join(f"{k}={v}" for k, v in contagem.items()),
             " (PAROU antes do fim)" if parou else "", extra={"so_no_arquivo": True})  # T57
    tela.secao("Resumo da conferência no site", saida)
    tela.contagens([("Já estão no site", contagem[NO_SITE], "ok"),
                    ("Tema no site, mas menos vezes que as fotos", contagem[EM_PARTE], "aviso"),
                    ("Talvez no site com outro tema (não envia)", contagem[OUTRO_TEMA], "aviso"),
                    ("Ainda não estão no site", contagem[FORA_DO_SITE], "info"),
                    ("Canceladas no site (conferir; não envia)", contagem[CANCELADA], "aviso"),
                    ("Não conferidas (conta não abriu)", contagem[NAO_CONFERIDO], "erro"),
                    ("Não tentadas (parou antes)", contagem[NAO_TENTADO], "aviso")], saida)
    if parou:
        tela.erro("Conferência PARADA antes do fim (veja o motivo acima).", saida)
    problemas = contas_com_problema(conferencias)
    if problemas:
        _mostrar_problemas(problemas, saida)
    tela.info(f"Relatório: {tela.caminho(gravar_csv(conferencias, cfg.pasta_relatorios, cfg.id_turma))}", saida)
    tela.status("fraco", "Nada foi enviado e o caderno não mudou.", saida)
    if contagem[OUTRO_TEMA]:
        tela.status("fraco", "\"Outro tema?\": o site tem redações a mais de outro tema (ex.: mandada como 000).",
                    saida)
        tela.status("fraco", "Confira no site se quiser; essas nunca entram no envio.", saida)
    faltam = faltam_enviar(conferencias)
    if parou:
        return 1
    if problemas and guiada and guiada(problemas):
        pendencias.cadastro_mudou = True  # o menu oferece conferir de novo, ali mesmo
        tela.aviso("O cadastro mudou: a conferência acima já não vale. É preciso \"Conferir contas no site\" "
                   "de novo antes de enviar.", saida)
        return 0
    # T60: pasta com TODAS as fotos no site pode ser marcada "ENVIADA - "
    from modulos.ferramentas.pastas_enviadas import marcar_pastas_enviadas, pastas_prontas
    marcar_pastas_enviadas(cfg.pasta_raiz, pastas_prontas(resultado, conferencias), cfg.pasta_relatorios,
                           entrada, saida)
    if not faltam:  # T54: dizer por que não pergunta "Montar o envio?"
        tela.ok("Não falta enviar nenhuma: nada para montar.", saida)
    elif depois:
        depois(faltam)
    return 1 if parou else 0
