"""Gerenciar escolas e turmas depois de prontas (issue #35): menu 13 Configurações.

Adicionar escola/turma e renomear escola/turma. Renomear acompanha a pasta, o
"Arquivo morto" da turma e a coluna ``turma`` do caderno (cópia antes), e não
roda durante um envio (mesma trava). Nada é apagado nem enviado.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
import textwrap
from pathlib import Path
from typing import Callable

from modulos.base import config as config_mod
from modulos.base import tela
from modulos.base.copia_seguranca import copiar_caderno
from modulos.base.trava import TravaOcupada, trava_de_envio
from modulos.base.turma import PASTA_GUIA, _eh_link, listar_escolas, listar_turmas, pasta_da_turma, raiz_redacoes
from modulos.ferramentas.arquivo_morto import PASTA_ARQUIVO
from modulos.ferramentas.assistente_inicial import _nome, _numero, _sim, criar_turma

Entrada = Callable[[str], str] | None

FRASE_APAGAR = "Sim eu tenho certeza disso e estou ciente dos riscos e quero apagar"
_AVISO = "ESPERO QUE VOCÊ TENHA CERTEZA DO QUE ESTÁ FAZENDO! ISSO VAI APAGAR COMPLETAMENTE OS ALUNOS, OS TEMAS, AS REDAÇÕES"
AVISO_ESCOLA = f"{_AVISO}, AS TURMAS E A ESCOLA."
AVISO_TURMA = f"{_AVISO} E A TURMA."


def _nomes_na_pasta(pasta: Path) -> set[str]:
    return {p.name.casefold() for p in pasta.iterdir()} if pasta.is_dir() else set()


def _mostrar(criados: list[Path]) -> None:
    for c in criados:
        tela.status("fraco", tela.caminho(c), recuo=4)
    tela.ok(f"Pronto. Em temas/ está a pasta {PASTA_GUIA}: é só renomear para o tema.")


def adicionar_escola(entrada: Entrada = None, saida: Callable = print) -> bool:
    escola = _nome(entrada, "Nome da nova escola:", "Escola", _nomes_na_pasta(raiz_redacoes()))
    n = _numero(entrada, f"São quantas turmas na {escola}?") if escola else None
    if n is None:
        tela.aviso("Cancelado. Nada foi criado.", saida)
        return False
    turmas: set[str] = set()
    criados: list[Path] = []
    for j in range(1, n + 1):
        turma = _nome(entrada, f"Nome da turma {j} de {n} ({escola}):", "Turma", turmas)
        if turma is None:
            tela.aviso("Cancelado no meio: as turmas já criadas ficam.", saida)
            break
        turmas.add(turma.casefold())
        criar_turma(escola, turma, criados)
    _mostrar(criados)
    return bool(criados)


def adicionar_turma(entrada: Entrada = None, saida: Callable = print) -> bool:
    from modulos.ferramentas.menu import _escolher
    escola = _escolher(listar_escolas(), "Escola", entrada, saida)
    if escola is None:
        return False
    turma = _nome(entrada, f"Nome da nova turma da {escola}:", "Turma", _nomes_na_pasta(raiz_redacoes() / escola))
    if turma is None:
        tela.aviso("Cancelado. Nada foi criado.", saida)
        return False
    criados: list[Path] = []
    criar_turma(escola, turma, criados)
    _mostrar(criados)
    return True


def _fechar_logs(pasta: Path) -> None:
    """O Windows não deixa renomear pasta com o log aberto dentro dela."""
    logger = logging.getLogger("automacao_redacoes")
    for h in [h for h in logger.handlers if isinstance(h, logging.FileHandler)]:
        if Path(h.baseFilename).is_relative_to(pasta.resolve()):
            h.close()
            logger.removeHandler(h)


def _atualizar_caderno(banco: Path, antigo: str, novo: str, escola: bool) -> int:
    """Troca ``antigo`` por ``novo`` na coluna turma ("Escola/Turma"). Cópia do caderno antes."""
    if not banco.is_file():
        return 0
    con = sqlite3.connect(banco)
    try:
        if "turma" not in {r[1] for r in con.execute("PRAGMA table_info(progresso)")}:
            return 0
        copiar_caderno(con, banco.parent / "copias")
        if escola:
            n = len(antigo) + 1
            cur = con.execute("UPDATE progresso SET turma = ? || substr(turma, ?) WHERE substr(turma, 1, ?) = ?",
                              (novo, n, n, antigo + "/"))
        else:
            cur = con.execute("UPDATE progresso SET turma = ? WHERE turma = ?", (novo, antigo))
        con.commit()
        return cur.rowcount
    finally:
        con.close()


def renomear(antigo: Path, novo: Path, id_antigo: str, id_novo: str, escola: bool,
             banco: Path | None = None, saida: Callable = print) -> bool:
    """Renomeia a pasta (e o arquivo morto e o caderno junto). Se algo falhar, volta tudo ao que era."""
    banco = banco or config_mod.RAIZ / "relatorios" / "progresso.db"
    morto = config_mod.RAIZ / PASTA_ARQUIVO
    morto_antigo = morto / id_antigo
    morto_novo = morto / id_novo
    try:
        with trava_de_envio(banco.parent / "envio.trava"):
            _fechar_logs(antigo)
            antigo.rename(novo)
            movido = False
            try:
                if morto_antigo.is_dir() and not morto_novo.exists():
                    morto_novo.parent.mkdir(parents=True, exist_ok=True)
                    morto_antigo.rename(morto_novo)
                    movido = True
                registros = _atualizar_caderno(banco, id_antigo, id_novo, escola)
            except Exception as e:  # noqa: BLE001 - desfaz e avisa
                if movido:
                    morto_novo.rename(morto_antigo)
                novo.rename(antigo)
                tela.erro(f"Não consegui atualizar o caderno ({type(e).__name__}: {e}). Nada foi renomeado.", saida)
                return False
    except TravaOcupada:
        tela.erro("Tem um envio rodando agora. Espere terminar para renomear.", saida)
        return False
    except OSError as e:
        tela.erro(f"Não consegui renomear (a pasta está aberta em outro programa?): {e}. Nada mudou.", saida)
        return False
    tela.ok(f"Renomeado: {id_antigo}  →  {id_novo}", saida)
    tela.status("fraco", f"{registros} registro(s) do caderno acompanharam o novo nome (cópia antes em relatorios/copias).",
                saida, recuo=4)
    tela.status("fraco", "Logs de renomeação antigos (menu 10) dessa pasta deixam de poder ser desfeitos.", saida, recuo=4)
    return True


def renomear_escola(entrada: Entrada = None, saida: Callable = print) -> bool:
    from modulos.ferramentas.menu import _escolher
    escola = _escolher(listar_escolas(), "Escola a renomear", entrada, saida)
    if escola is None:
        return False
    outros = _nomes_na_pasta(raiz_redacoes()) - {escola.casefold()}
    novo = _nome(entrada, f"Novo nome para a escola {escola}:", "Escola", outros)
    if novo is None or novo == escola or not _sim(entrada, f"Renomear a escola {escola} para {novo}?"):
        tela.aviso("Nada mudou.", saida)
        return False
    return renomear(raiz_redacoes() / escola, raiz_redacoes() / novo, escola, novo, True, saida=saida)


def renomear_turma(entrada: Entrada = None, saida: Callable = print) -> bool:
    from modulos.ferramentas.menu import _escolher
    escola = _escolher(listar_escolas(), "Escola", entrada, saida)
    turma = _escolher(listar_turmas(escola), f"Turma de {escola} a renomear", entrada, saida) if escola else None
    if turma is None:
        return False
    outros = _nomes_na_pasta(raiz_redacoes() / escola) - {turma.casefold()}
    novo = _nome(entrada, f"Novo nome para a turma {turma}:", "Turma", outros)
    if novo is None or novo == turma or not _sim(entrada, f"Renomear a turma {turma} para {novo}?"):
        tela.aviso("Nada mudou.", saida)
        return False
    antigo = pasta_da_turma(escola, turma)
    return renomear(antigo, antigo.parent / novo, f"{escola}/{turma}", f"{escola}/{novo}", False, saida=saida)


def _apagar_pasta(pasta: Path, banco: Path | None = None) -> bool:
    """rmtree da escola/turma, sempre dentro de Redações plataforma e sob a trava de envio."""
    banco = banco or config_mod.RAIZ / "relatorios" / "progresso.db"
    raiz = raiz_redacoes().resolve()
    if _eh_link(pasta) or pasta.resolve() == raiz or not pasta.resolve().is_relative_to(raiz):
        tela.erro(f"Recusei: {pasta} não está dentro de {raiz} (ou é um atalho). Nada foi apagado.")
        return False
    try:
        with trava_de_envio(banco.parent / "envio.trava"):
            _fechar_logs(pasta)
            shutil.rmtree(pasta)
    except TravaOcupada:
        tela.erro("Tem um envio rodando agora. Espere terminar para apagar.")
        return False
    except OSError as e:
        tela.erro(f"Deu erro ao apagar ({e}). Pode ter ficado pela metade: confira a pasta {tela.caminho(pasta)}.")
        return False
    return True


def apagar(entrada: Entrada = None, saida: Callable = print) -> bool:
    """Opção x: apagar uma escola ou uma turma, com aviso, escolha, aviso crítico e frase digitada."""
    from modulos.ferramentas.menu import _escolher
    if not _sim(entrada, "Você tem certeza que quer fazer isso? É uma ação sem volta."):
        tela.aviso("Nada foi apagado.", saida)
        return False
    tipo = tela.perguntar("  Apagar uma Turma ou uma Escola? (t = turma, e = escola, Enter = cancelar): ",
                          entrada).lower()
    if tipo not in ("t", "e"):
        tela.aviso("Nada foi apagado.", saida)
        return False
    escola = _escolher(listar_escolas(), "Escola", entrada, saida)
    turma = _escolher(listar_turmas(escola), f"Turma de {escola} a apagar", entrada, saida)         if tipo == "t" and escola else None
    if escola is None or (tipo == "t" and turma is None):
        tela.aviso("Nada foi apagado.", saida)
        return False
    pasta = pasta_da_turma(escola, turma) if tipo == "t" else raiz_redacoes() / escola
    saida("")
    for linha in textwrap.wrap(AVISO_TURMA if tipo == "t" else AVISO_ESCOLA, 76):
        saida(tela.c(linha, "erro"))
    saida(f"  Vai apagar: {tela.caminho(pasta)}")
    tela.status("fraco", "O caderno de envios e o Arquivo morto não são apagados.", saida, recuo=4)
    saida("  Para confirmar, digite exatamente:")
    saida(f"    {FRASE_APAGAR}")
    if tela.perguntar("  > ", entrada) != FRASE_APAGAR:
        tela.aviso("A frase não confere. Nada foi apagado.", saida)
        return False
    if not _apagar_pasta(pasta):
        return False
    tela.ok(f"Apagada: {escola if tipo == 'e' else f'{escola} / {turma}'}", saida)
    if tipo == "e":
        tela.secao("Escolas disponíveis", saida)
        restantes = listar_escolas()
    else:
        tela.secao(f"Turmas disponíveis de {escola}", saida)
        restantes = listar_turmas(escola)
    for r in restantes or ["(nenhuma)"]:
        tela.status("fraco", r, saida, recuo=4)
    return True


def executar_configuracoes_e_estrutura(entrada: Entrada = None, saida: Callable = print) -> None:
    """Menu 13: navegador + gerenciar escolas e turmas."""
    from modulos.ferramentas.configuracoes import executar_configuracoes
    tela.titulo("CONFIGURAÇÕES", saida)
    tela.menu([("1", "navegador: mostrar ou esconder"), ("2", "adicionar uma escola"),
               ("3", "adicionar uma turma a uma escola"), ("4", "renomear uma escola"),
               ("5", "renomear uma turma"), ("x", "deletar escola ou turma (sem volta)")], saida)
    escolha = tela.perguntar("  > ", entrada)
    {"1": executar_configuracoes, "2": adicionar_escola, "3": adicionar_turma,
     "4": renomear_escola, "5": renomear_turma, "x": apagar}.get(escolha.lower(), lambda *a, **k: None)(entrada=entrada, saida=saida)

