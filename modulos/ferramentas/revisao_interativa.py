"""Revisão interativa no terminal (T29): `python main.py --pasta X --revisar`.

Em vez de editar CSV à mão, o Antônio responde uma pergunta por vez:

1. Pastas sem código de tema: escolhe o código (Enter aceita a sugestão
   provável, um número escolhe o código, texto busca outro tema). Grava
   ``aprovado=sim`` em ``dados/pastas_aprovadas.csv``. A pasta não é renomeada.
2. Nomes de arquivo que não são o nome exato de um aluno: confirma o aluno
   sugerido ou busca outro; o arquivo é RENOMEADO para o nome exato do aluno
   (em todas as pastas onde o mesmo nome aparece). Cada renomeação vai para
   ``relatorios/renomeacoes_<data_hora>.csv`` e pode ser desfeita com
   ``--desfazer-renomeacao``.

Nada é enviado. Folha "em branco" nunca é perguntada. Arquivo que já tem
estado de envio no banco (ENVIADO, ENVIANDO, JA_ENVIADO, REVISAO_MANUAL)
nunca é renomeado: a chave do progresso é pasta/arquivo e renomear abriria
caminho para reenvio.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Callable

from rapidfuzz import fuzz

from modulos.base import tela
from modulos.base.estados import REVISAO_MANUAL
from modulos.dados.nomes_aprovados import _sugestoes_para
from modulos.dados.normalizacao import PADRAO_CODIGO_ARQUIVO, extrair_codigo_tema, normalizar_nome
from modulos.dados.planilha_arquivos import Aluno, ResultadoConciliacao, eh_folha_em_branco
from modulos.base.progresso_relatorio import ENVIADO, ENVIANDO, JA_ENVIADO
from modulos.dados.sugestao_temas import SCORE_PROVAVEL, _titulo, aprovar_pasta

ESTADOS_TRAVADOS = {ENVIADO, ENVIANDO, JA_ENVIADO, REVISAO_MANUAL}
COLUNAS_LOG = ["pasta", "antes", "depois", "aluno_email", "raiz"]  # T48: raiz = pasta das redações
_PROIBIDOS_WINDOWS = re.compile(r'[<>:"/\\|?*]')

Entrada = Callable[[str], str]


def _perguntar(entrada: Entrada | None, texto: str) -> str:
    try:
        return (entrada or input)(texto).strip()
    except (EOFError, OSError, KeyboardInterrupt):
        return "q"  # sem terminal ou Ctrl+C: sai salvando o que já foi feito


# ─── Busca ───────────────────────────────────────────────────

def buscar_alunos(texto: str, alunos: list[Aluno], n: int = 5) -> list[tuple[Aluno, float]]:
    norm = normalizar_nome(texto)
    pontuados = [(a, max(fuzz.token_set_ratio(norm, a.nome_norm), fuzz.partial_ratio(norm, a.nome_norm)))
                 for a in alunos]
    pontuados.sort(key=lambda t: t[1], reverse=True)
    return pontuados[:n]


def buscar_temas(texto: str, temas: list[tuple[str, str]], n: int = 5,
                 por_palavras: bool = False) -> list[tuple[str, str, float]]:
    """Temas mais parecidos (sem repetir código). ``por_palavras``: busca
    digitada; tema que contém todas as palavras (sem acento) vem primeiro."""
    titulo = _titulo(texto)
    palavras = [w for w in normalizar_nome(texto).split() if len(w) >= 3]
    vistos: set[str] = set()
    pontuados = []
    for codigo, tema in temas:
        if codigo in vistos:
            continue
        vistos.add(codigo)
        score = float(fuzz.token_set_ratio(titulo, _titulo(tema)))
        if por_palavras and palavras and all(w in normalizar_nome(tema) for w in palavras):
            score = 100.0
        pontuados.append((codigo, tema, score))
    pontuados.sort(key=lambda t: t[2], reverse=True)
    return pontuados[:n]


def _sem_codigo(texto: str) -> str:
    """"100- Impactos..." -> "Impactos..." (o código já aparece na coluna)."""
    return re.sub(r"^\s*\d+\s*-\s*", "", texto)


# ─── Pastas ──────────────────────────────────────────────────

TEMA_GENERICO = "000"  # "000- DISSERTATIVO ARGUMENTATIVO": tema que não está na plataforma (22/10)
def _linha_tema(codigo: str, tema: str, score: float | None) -> list[str]:
    """Nome inteiro do tema, quebrado em linhas alinhadas abaixo do texto."""
    prefixo = f"   [{codigo:>6}]  "
    recuo = len(prefixo)
    if score is not None:
        prefixo += f"{tela.barra(score)} {tela.porcentagem(score)}  "
        recuo += tela.BARRA_TAMANHO + 1 + 4 + 2
    linhas = textwrap.wrap(_sem_codigo(tema), width=max(30, tela.LARGURA - recuo)) or [""]
    return [prefixo + linhas[0]] + [" " * recuo + linha for linha in linhas[1:]]


def revisar_pastas(pastas: list[str], temas: list[tuple[str, str]], caminho_aprovadas: Path,
                   entrada: Entrada | None = None, saida: Callable = print) -> tuple[int, bool]:
    """Pergunta o código de cada pasta sem código. Retorna (aprovadas, saiu).
    Temas do mais parecido para o menos, com barra e %; ``g`` = tema genérico."""
    contagem = {}
    for codigo, _ in temas:
        contagem[codigo] = contagem.get(codigo, 0) + 1
    texto_de = {codigo: tema for codigo, tema in temas}
    tem_generico = contagem.get(TEMA_GENERICO) == 1
    aprovadas = 0
    for n, pasta in enumerate(pastas, 1):
        busca = ""
        while True:
            opcoes = buscar_temas(busca or pasta, temas, n=len(temas) if busca else 5,
                                  por_palavras=bool(busca))
            melhor = opcoes[0] if not busca and opcoes and opcoes[0][2] >= SCORE_PROVAVEL else None
            tela.cabecalho(f"PASTA {n} de {len(pastas)}:  {pasta}", saida)
            if busca == "t":
                saida("  Todos os temas do site:")
                for codigo, tema, _ in sorted(opcoes, key=lambda t: (len(t[0]), t[0])):
                    for linha in _linha_tema(codigo, tema, None):
                        saida(linha)
            else:
                if busca:
                    achou = [o for o in opcoes if o[2] >= 100.0]
                    opcoes = achou or opcoes[:5]
                    saida(f"  Temas com \"{busca}\":" if achou
                          else f"  Nenhum tema tem \"{busca}\"; os mais parecidos (do maior para o menor):")
                else:
                    saida("  Temas do site mais parecidos (do maior para o menor):")
                for codigo, tema, score in opcoes:
                    for linha in _linha_tema(codigo, tema, None if score >= 100.0 and busca else score):
                        saida(linha)
                saida("")
                if melhor:
                    for linha in textwrap.wrap(f"✔ Provavelmente e o tema {melhor[0]}: {_sem_codigo(melhor[1])}",
                                               width=tela.LARGURA - 2, initial_indent="  ", subsequent_indent="    "):
                        saida(tela.c(linha, "ok"))
                elif not busca:
                    saida(tela.c("  ⚠ Nenhum tema e bem parecido. Se o tema nao existe no site,", "aviso"))
                    saida(f"    use g = tema generico ({TEMA_GENERICO})." if tem_generico
                          else "    pule (p) e decida depois.")
            menu = [("Enter", f"confirmar o tema {melhor[0]}")] if melhor else []
            menu.append(("numero", "escolher o tema (ex.: 100)"))
            if tem_generico:
                menu.append(("g", f"tema generico: {_sem_codigo(texto_de[TEMA_GENERICO])} ({TEMA_GENERICO})"))
            menu += [("palavra", "procurar tema (ex.: rua)"), ("t", "ver todos os temas"),
                     ("p", "pular esta pasta"), ("q", "sair (o que ja fez fica salvo)")]
            tela.menu(menu, saida)
            resp = _perguntar(entrada, "  > ")
            low = resp.lower()
            if low == "q":
                return aprovadas, True
            if low == "p" or (not resp and not melhor):
                saida(tela.c("  Pulada (nada desta pasta sera enviado).", "aviso"))
                break
            if low == "g" and tem_generico:
                resp = TEMA_GENERICO
            codigo = melhor[0] if not resp else resp
            if codigo.isdigit():
                if codigo not in contagem:
                    saida(tela.c(f"  ✘ Tema {codigo} nao existe na lista do site (dados/temas_site.csv).", "erro"))
                    continue
                if contagem[codigo] > 1:
                    saida(tela.c(f"  ✘ Tema {codigo} aparece {contagem[codigo]}x no site: nao da para enviar automaticamente.", "erro"))
                    continue
                aprovar_pasta(caminho_aprovadas, pasta, codigo, texto_de[codigo])
                saida(tela.c(f"  ✔ OK: {pasta} -> tema {codigo} ({_sem_codigo(texto_de[codigo])})", "ok"))
                aprovadas += 1
                break
            busca = low if low == "t" else resp
    return aprovadas, False


# ─── Nomes ───────────────────────────────────────────────────

def grupos_para_revisar(resultado: ResultadoConciliacao, alunos: list[Aluno]) -> list[tuple[str, list]]:
    """[(nome no arquivo, itens)] agrupados pelo nome normalizado, só os que
    não são o nome exato de um aluno (folha em branco fica de fora)."""
    exatos = {a.nome_norm for a in alunos}
    grupos: dict[str, list] = {}
    for item in resultado.itens:
        if not item.arquivo:
            continue
        norm = normalizar_nome(item.pessoa)
        if not norm or norm in exatos or eh_folha_em_branco(norm):
            continue
        grupos.setdefault(norm, []).append(item)
    return [(itens[0].pessoa, itens) for _, itens in sorted(grupos.items())]


def nome_arquivo_para(arquivo: str, aluno: Aluno) -> str:
    """Nome novo: nome exato do aluno + extensão; mantém código no início, se houver."""
    stem, ext = Path(arquivo).stem, Path(arquivo).suffix
    m = PADRAO_CODIGO_ARQUIVO.match(stem)
    prefixo = f"{m.group(1)} - " if m else ""
    return f"{prefixo}{_PROIBIDOS_WINDOWS.sub('', aluno.nome).strip()}{ext}"


def estado_travado(banco: Path, chave: str) -> str:
    """Estado de envio que impede renomear (vazio se pode)."""
    if not Path(banco).is_file():
        return ""
    con = sqlite3.connect(f"file:{Path(banco).as_posix()}?mode=ro", uri=True)
    try:
        linhas = con.execute("SELECT estado FROM progresso WHERE arquivo = ?", (chave,)).fetchall()
    except sqlite3.Error as e:
        return f"banco ilegivel ({type(e).__name__})"  # T43: na dúvida, não mexe
    finally:
        con.close()
    for (estado,) in linhas:
        if estado in ESTADOS_TRAVADOS:
            return estado
    return ""


def renomear(pasta_raiz: Path, pasta: str, arquivo: str, aluno: Aluno, banco: Path,
             log_csv: Path) -> tuple[str, str]:
    """Renomeia um arquivo. Retorna (novo_nome, "") ou ("", motivo)."""
    origem = Path(pasta_raiz) / pasta / arquivo
    novo = nome_arquivo_para(arquivo, aluno)
    travado = estado_travado(banco, f"{pasta}/{arquivo}")
    if travado:
        return "", f"ja tem estado {travado} no banco; nao renomeado"
    if not origem.is_file():
        return "", "arquivo nao encontrado"
    if novo == arquivo:
        return "", "ja esta com o nome do aluno"
    existentes = {p.name.casefold() for p in origem.parent.iterdir()}
    if novo.casefold() in existentes:
        return "", f"ja existe '{novo}' nesta pasta (duas redacoes do mesmo aluno?): decida a mao"
    # T43: log ANTES de renomear: renomeação sem log não teria como ser desfeita
    log_csv = Path(log_csv)
    log_csv.parent.mkdir(parents=True, exist_ok=True)
    novo_log = not log_csv.is_file()
    with open(log_csv, "a", encoding="utf-8-sig" if novo_log else "utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        if novo_log:
            escritor.writerow(COLUNAS_LOG)
        escritor.writerow([pasta, arquivo, novo, aluno.email, str(Path(pasta_raiz).resolve())])
    try:
        origem.rename(origem.with_name(novo))
    except OSError as e:
        return "", f"Windows nao deixou renomear ({type(e).__name__}): arquivo aberto?"
    return novo, ""


def revisar_nomes(grupos: list[tuple[str, list]], alunos: list[Aluno], pasta_raiz: Path,
                  banco: Path, log_csv: Path, nomes_aprovados: dict | None = None,
                  entrada: Entrada | None = None, saida: Callable = print) -> tuple[int, bool]:
    """Pergunta o aluno de cada nome. Retorna (arquivos renomeados, saiu)."""
    renomeados = 0
    for n, (nome, itens) in enumerate(grupos, 1):
        norm = normalizar_nome(nome)
        sugestoes = [a for a, _ in _sugestoes_para(norm, alunos)]
        if nomes_aprovados and norm in nomes_aprovados:
            aprovado = nomes_aprovados[norm]
            sugestoes = [aprovado] + [a for a in sugestoes if a is not aprovado]
        opcoes = [(a, "sugerido") for a in sugestoes] or buscar_alunos(nome, alunos, n=3)
        escolhido = None
        while escolhido is None:
            tela.cabecalho(f"NOME {n} de {len(grupos)}:  \"{nome}\"  ({len(itens)} arquivo(s))", saida)
            saida("  Arquivos:")
            for item in itens:
                saida(tela.c(f"    {item.pasta}/{item.arquivo}", "fraco"))
            saida("")
            saida("  Alunos da lista:")
            for i, (aluno, info) in enumerate(opcoes, 1):
                extra = (f"{tela.barra(info)} {tela.porcentagem(info)}" if isinstance(info, float)
                         else tela.c("✔ sugerido", "ok"))
                saida(f"    {tela.c(f'{i})', 'tecla')} {extra}  {aluno.nome}")
            unico = len(sugestoes) == 1 and opcoes[0][0] is sugestoes[0]
            menu = [("Enter", f"confirmar 1 ({opcoes[0][0].nome})")] if unico else []
            menu += [("numero", "escolher o aluno da lista"), ("texto", "procurar outro aluno (ex.: luiza)"),
                     ("p", "pular este nome"), ("q", "sair (o que ja fez fica salvo)")]
            tela.menu(menu, saida)
            resp = _perguntar(entrada, "  > ")
            low = resp.lower()
            if low == "q":
                return renomeados, True
            if low == "p" or (not resp and not unico):
                saida(tela.c("  Pulado (esses arquivos nao serao enviados).", "aviso"))
                break
            if not resp:
                escolhido = opcoes[0][0]
            elif resp.isdigit() and 1 <= int(resp) <= len(opcoes):
                escolhido = opcoes[int(resp) - 1][0]
            elif resp.isdigit():
                saida(tela.c("  ✘ Numero fora da lista.", "erro"))
            else:
                opcoes = buscar_alunos(resp, alunos)
        if escolhido is None:
            continue
        for item in itens:
            novo, motivo = renomear(pasta_raiz, item.pasta, item.arquivo, escolhido, banco, log_csv)
            if novo:
                renomeados += 1
                saida(tela.c(f"  ✔ Renomeado: {item.pasta}/{item.arquivo} -> {novo}", "ok"))
            else:
                saida(tela.c(f"  ✘ NAO renomeado: {item.pasta}/{item.arquivo}: {motivo}", "erro"))
    return renomeados, False


# ─── Orquestração e desfazer ─────────────────────────────────

def executar_revisao(resultado: ResultadoConciliacao, alunos: list[Aluno], arquivos: dict,
                     temas: list[tuple[str, str]], codigos_pasta: dict, pasta_raiz: Path,
                     caminho_pastas: Path, banco: Path, pasta_relatorios: Path,
                     nomes_aprovados: dict | None = None,
                     entrada: Entrada | None = None, saida: Callable = print) -> int:
    log_csv = Path(pasta_relatorios) / f"renomeacoes_{datetime.now():%Y%m%d_%H%M%S}.csv"
    tela.titulo("REVISÃO NO TERMINAL  ·  nada é enviado", saida)
    pastas = sorted(p for p in arquivos if p not in codigos_pasta and not extrair_codigo_tema("", p))
    aprovadas, saiu = (0, False)
    if pastas and temas:
        tela.secao(f"Parte 1: {len(pastas)} pasta(s) sem codigo de tema", saida)
        aprovadas, saiu = revisar_pastas(pastas, temas, caminho_pastas, entrada, saida)
    elif pastas:
        tela.aviso("Parte 1 pulada: dados/temas_site.csv vazio (rode --analise-remota).", saida)
    renomeados = 0
    grupos = grupos_para_revisar(resultado, alunos)
    if not saiu and grupos:
        tela.secao(f"Parte 2: {len(grupos)} nome(s) que nao sao o nome exato de um aluno", saida)
        renomeados, saiu = revisar_nomes(grupos, alunos, pasta_raiz, banco, log_csv,
                                         nomes_aprovados, entrada, saida)
    tela.secao("Fim da revisao" + (" (interrompida)" if saiu else ""), saida)
    tela.status("aviso" if saiu else "ok",
                f"{aprovadas} pasta(s) aprovada(s), {renomeados} arquivo(s) renomeado(s).", saida)
    if renomeados:
        tela.info(f"Log das renomeacoes: {tela.caminho(log_csv)}", saida)
        tela.comando(f'python main.py --desfazer-renomeacao "{log_csv}" --pasta "{pasta_raiz}"',
                     "para desfazer", saida)
    tela.comando("python main.py", "rode o dry-run de novo para conferir a fila", saida)
    return 0


def desfazer_renomeacoes(log_csv: Path, pasta_raiz: Path, saida: Callable = print,
                         banco: Path | None = None) -> int:
    """Volta os nomes do log, do último para o primeiro. Retorna quantos voltaram.
    T43: arquivo que já tem estado de envio no banco não volta (a chave do
    banco é o nome; voltar o nome apagaria o histórico e permitiria reenviar)."""
    log_csv = Path(log_csv)
    if not log_csv.is_file():
        tela.erro(f"Log nao encontrado: {log_csv}", saida)
        return 0
    with open(log_csv, encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    if linhas and not set(COLUNAS_LOG[:4]) <= set(linhas[0]):  # logs antigos não têm "raiz"
        tela.erro(f"Log sem as colunas {COLUNAS_LOG}: {log_csv.name}. Nada foi desfeito.", saida)
        return 0
    voltaram = 0
    for linha in reversed(linhas):
        # T48: a raiz gravada no log manda (log do modo teste não mexe na pasta real)
        raiz = Path(linha.get("raiz") or pasta_raiz)
        atual = raiz / linha["pasta"] / linha["depois"]
        antigo = atual.with_name(linha["antes"])
        travado = estado_travado(banco, f"{linha['pasta']}/{linha['depois']}") if banco else ""
        if travado:
            tela.erro(f"Nao desfeito: {linha['pasta']}/{linha['depois']} ja tem estado {travado} no banco", saida)
        elif atual.is_file() and not antigo.exists():
            atual.rename(antigo)
            voltaram += 1
        else:
            tela.erro(f"Nao desfeito: {linha['pasta']}/{linha['depois']}", saida)
    tela.status("ok" if voltaram == len(linhas) else "aviso",
                f"{voltaram} de {len(linhas)} arquivo(s) voltaram ao nome antigo.", saida)
    return voltaram
