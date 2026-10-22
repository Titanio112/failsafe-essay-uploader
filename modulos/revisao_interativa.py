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
from datetime import datetime
from pathlib import Path
from typing import Callable

from rapidfuzz import fuzz

from modulos.estados import REVISAO_MANUAL
from modulos.nomes_aprovados import _sugestoes_para
from modulos.normalizacao import PADRAO_CODIGO_ARQUIVO, extrair_codigo_tema, normalizar_nome
from modulos.planilha_arquivos import Aluno, ResultadoConciliacao, eh_folha_em_branco
from modulos.progresso_relatorio import ENVIADO, ENVIANDO, JA_ENVIADO
from modulos.sugestao_temas import SCORE_PROVAVEL, _titulo, aprovar_pasta

ESTADOS_TRAVADOS = {ENVIADO, ENVIANDO, JA_ENVIADO, REVISAO_MANUAL}
COLUNAS_LOG = ["pasta", "antes", "depois", "aluno_email"]
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


def buscar_temas(texto: str, temas: list[tuple[str, str]], n: int = 5) -> list[tuple[str, str, float]]:
    titulo = _titulo(texto)
    vistos: set[str] = set()
    pontuados = []
    for codigo, tema in temas:
        if codigo in vistos:
            continue
        vistos.add(codigo)
        pontuados.append((codigo, tema, float(fuzz.token_set_ratio(titulo, _titulo(tema)))))
    pontuados.sort(key=lambda t: t[2], reverse=True)
    return pontuados[:n]


# ─── Pastas ──────────────────────────────────────────────────

def revisar_pastas(pastas: list[str], temas: list[tuple[str, str]], caminho_aprovadas: Path,
                   entrada: Entrada | None = None, saida: Callable = print) -> tuple[int, bool]:
    """Pergunta o código de cada pasta sem código. Retorna (aprovadas, saiu)."""
    contagem = {}
    for codigo, _ in temas:
        contagem[codigo] = contagem.get(codigo, 0) + 1
    texto_de = {codigo: tema for codigo, tema in temas}
    aprovadas = 0
    for n, pasta in enumerate(pastas, 1):
        busca = pasta
        while True:
            opcoes = buscar_temas(busca, temas)
            saida("")
            saida(f"[Pasta {n}/{len(pastas)}] {pasta}")
            if busca != pasta:
                saida(f"  (busca: {busca})")
            for codigo, tema, score in opcoes:
                saida(f"  [{codigo}] {tema}  ({score:.0f}%)")
            melhor = opcoes[0] if opcoes and opcoes[0][2] >= SCORE_PROVAVEL else None
            dica = f"Enter = {melhor[0]} | " if melhor else ""
            resp = _perguntar(entrada, f"  {dica}codigo = escolher | texto = buscar tema | p = pular | q = sair: ")
            low = resp.lower()
            if low == "q":
                return aprovadas, True
            if low == "p" or (not resp and not melhor):
                saida("  Pulada (nada desta pasta sera enviado).")
                break
            codigo = melhor[0] if not resp else resp
            if codigo.isdigit():
                if codigo not in contagem:
                    saida(f"  Codigo {codigo} nao esta em dados/temas_site.csv. Confira no site.")
                    continue
                if contagem[codigo] > 1:
                    saida(f"  Codigo {codigo} aparece {contagem[codigo]}x no combo do site: nao da para enviar automaticamente.")
                    continue
                aprovar_pasta(caminho_aprovadas, pasta, codigo, texto_de[codigo])
                saida(f"  OK: {pasta} -> tema {codigo}")
                aprovadas += 1
                break
            busca = resp
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
    except sqlite3.Error:
        return ""
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
    origem.rename(origem.with_name(novo))
    log_csv = Path(log_csv)
    log_csv.parent.mkdir(parents=True, exist_ok=True)
    novo_log = not log_csv.is_file()
    with open(log_csv, "a", encoding="utf-8-sig" if novo_log else "utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        if novo_log:
            escritor.writerow(COLUNAS_LOG)
        escritor.writerow([pasta, arquivo, novo, aluno.email])
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
            saida("")
            saida(f"[Nome {n}/{len(grupos)}] \"{nome}\" em {len(itens)} arquivo(s):")
            for item in itens:
                saida(f"    {item.pasta}/{item.arquivo}")
            for i, (aluno, info) in enumerate(opcoes, 1):
                extra = f"{info:.0f}%" if isinstance(info, float) else info
                saida(f"  {i}) {aluno.nome}  ({extra})")
            unico = len(sugestoes) == 1 and opcoes[0][0] is sugestoes[0]
            dica = "Enter = 1 | " if unico else ""
            resp = _perguntar(entrada, f"  {dica}numero = escolher | texto = buscar aluno | p = pular | q = sair: ")
            low = resp.lower()
            if low == "q":
                return renomeados, True
            if low == "p" or (not resp and not unico):
                saida("  Pulado (esses arquivos nao serao enviados).")
                break
            if not resp:
                escolhido = opcoes[0][0]
            elif resp.isdigit() and 1 <= int(resp) <= len(opcoes):
                escolhido = opcoes[int(resp) - 1][0]
            elif resp.isdigit():
                saida("  Numero fora da lista.")
            else:
                opcoes = buscar_alunos(resp, alunos)
        if escolhido is None:
            continue
        for item in itens:
            novo, motivo = renomear(pasta_raiz, item.pasta, item.arquivo, escolhido, banco, log_csv)
            if novo:
                renomeados += 1
                saida(f"  Renomeado: {item.pasta}/{item.arquivo} -> {novo}")
            else:
                saida(f"  NAO renomeado: {item.pasta}/{item.arquivo}: {motivo}")
    return renomeados, False


# ─── Orquestração e desfazer ─────────────────────────────────

def executar_revisao(resultado: ResultadoConciliacao, alunos: list[Aluno], arquivos: dict,
                     temas: list[tuple[str, str]], codigos_pasta: dict, pasta_raiz: Path,
                     caminho_pastas: Path, banco: Path, pasta_relatorios: Path,
                     nomes_aprovados: dict | None = None,
                     entrada: Entrada | None = None, saida: Callable = print) -> int:
    log_csv = Path(pasta_relatorios) / f"renomeacoes_{datetime.now():%Y%m%d_%H%M%S}.csv"
    saida("")
    saida("=== Revisao interativa (nada e enviado) ===")
    pastas = sorted(p for p in arquivos if p not in codigos_pasta and not extrair_codigo_tema("", p))
    aprovadas, saiu = (0, False)
    if pastas and temas:
        saida(f"Parte 1: {len(pastas)} pasta(s) sem codigo de tema.")
        aprovadas, saiu = revisar_pastas(pastas, temas, caminho_pastas, entrada, saida)
    elif pastas:
        saida("Parte 1 pulada: dados/temas_site.csv vazio (rode --analise-remota).")
    renomeados = 0
    grupos = grupos_para_revisar(resultado, alunos)
    if not saiu and grupos:
        saida("")
        saida(f"Parte 2: {len(grupos)} nome(s) de arquivo que nao sao o nome exato de um aluno.")
        renomeados, saiu = revisar_nomes(grupos, alunos, pasta_raiz, banco, log_csv,
                                         nomes_aprovados, entrada, saida)
    saida("")
    saida(f"Fim da revisao{' (interrompida)' if saiu else ''}: {aprovadas} pasta(s) aprovada(s), "
          f"{renomeados} arquivo(s) renomeado(s).")
    if renomeados:
        saida(f"Log das renomeacoes: {log_csv}")
        saida(f'Para desfazer: python main.py --desfazer-renomeacao "{log_csv}" --pasta "{pasta_raiz}"')
    saida("Rode o dry-run de novo para conferir a fila.")
    return 0


def desfazer_renomeacoes(log_csv: Path, pasta_raiz: Path, saida: Callable = print) -> int:
    """Volta os nomes do log, do último para o primeiro. Retorna quantos voltaram."""
    with open(log_csv, encoding="utf-8-sig", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    voltaram = 0
    for linha in reversed(linhas):
        atual = Path(pasta_raiz) / linha["pasta"] / linha["depois"]
        antigo = atual.with_name(linha["antes"])
        if atual.is_file() and not antigo.exists():
            atual.rename(antigo)
            voltaram += 1
        else:
            saida(f"  Nao desfeito: {linha['pasta']}/{linha['depois']}")
    saida(f"{voltaram} de {len(linhas)} arquivo(s) voltaram ao nome antigo.")
    return voltaram
