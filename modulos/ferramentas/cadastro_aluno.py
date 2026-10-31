"""Cadastrar aluno novo no alunos.csv ao fim da Revisão (issue #54).

Só ACRESCENTA uma linha no fim (nunca reescreve as que existem; cópia antes) e nunca mostra nem
registra a senha. A foto fica ligada ao aluno do mesmo jeito da Revisão: renomeada para o nome dele.
"""

from __future__ import annotations

import csv
import getpass
import io
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from modulos.base import tela
from modulos.dados.arquivos_csv import garantir_quebra_final, ler_texto
from modulos.dados.normalizacao import normalizar_nome
from modulos.dados.planilha_arquivos import SENHAS_LIDAS, Aluno

Entrada = Callable[[str], str] | None
EMAIL = re.compile(r"^[^@\s;,]+@[^@\s;,]+\.[^@\s;,]+$")


def validar_novo(nome: str, email: str, senha: str, alunos: list[Aluno]) -> str:
    """Motivo da recusa, ou "" se pode cadastrar."""
    if not nome.strip() or any(c in nome for c in "\r\n"):
        return "nome vazio"
    if not EMAIL.match(email.strip()):
        return "e-mail inválido"
    if not senha or any(c in senha for c in "\r\n"):
        return "senha vazia"
    if any(a.email.strip().casefold() == email.strip().casefold() for a in alunos):
        return "já existe aluno com esse e-mail"
    if any(a.nome_norm == normalizar_nome(nome) for a in alunos):
        return "já existe aluno com esse nome (o site não distingue homônimos)"
    return ""


def acrescentar_aluno(planilha: Path, nome: str, email: str, senha: str) -> Path:
    """Põe o aluno na última linha de ``planilha``. Retorna a cópia feita antes."""
    planilha = Path(planilha)
    copia = planilha.with_name(f"{planilha.stem}.{datetime.now():%Y%m%d_%H%M%S}.bak{planilha.suffix}")
    shutil.copy2(planilha, copia)
    garantir_quebra_final(planilha)  # cp1252 do Excel vira UTF-8 e a última linha ganha a quebra
    cabecalho = ler_texto(planilha).splitlines()[0]
    sep = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
    colunas = [c.strip().casefold() for c in next(csv.reader(io.StringIO(cabecalho), delimiter=sep))]
    linha = [""] * len(colunas)
    for chave, valor in (("nome", nome.strip()), ("email", email.strip()), ("senha", senha)):
        linha[colunas.index(chave)] = valor
    with open(planilha, "a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=sep, lineterminator="\n").writerow(linha)
    SENHAS_LIDAS.add(senha)  # o filtro do log passa a esconder esta senha
    return copia


def trocar_nome(planilha: Path, email: str, novo_nome: str) -> Path:
    """Troca o NOME do aluno de ``email`` no alunos.csv (issue #55); o resto de cada linha fica como está.
    Levanta ValueError se o e-mail não existir ou se repetir. Retorna a cópia feita antes."""
    planilha = Path(planilha)
    texto = ler_texto(planilha)
    cabecalho = texto.splitlines()[0]
    sep = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
    linhas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    colunas = [c.strip().casefold() for c in linhas[0]]
    i_nome, i_email = colunas.index("nome"), colunas.index("email")
    alvo = [r for r in linhas[1:] if len(r) > max(i_nome, i_email) and r[i_email].strip().casefold() == email.strip().casefold()]
    if len(alvo) != 1:
        raise ValueError(f"e-mail encontrado {len(alvo)} vez(es) no alunos.csv")
    alvo[0][i_nome] = novo_nome.strip()
    copia = planilha.with_name(f"{planilha.stem}.{datetime.now():%Y%m%d_%H%M%S}.bak{planilha.suffix}")
    shutil.copy2(planilha, copia)
    with open(planilha, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, delimiter=sep, lineterminator="\n").writerows(linhas)
    return copia


def _senha(entrada: Entrada, prompt: str) -> str:
    try:
        return entrada(prompt) if entrada else getpass.getpass(prompt)  # sem eco no terminal de verdade
    except (EOFError, OSError, KeyboardInterrupt):
        return ""


def cadastrar_pulados(pulados: list[tuple[str, list]], alunos: list[Aluno], planilha: Path, pasta_raiz: Path,
                      banco: Path, log_csv: Path, entrada: Entrada = None, saida: Callable = print) -> tuple[int, int]:
    """Pergunta e cadastra os nomes que ficaram sem aluno. Retorna (alunos cadastrados, fotos renomeadas)."""
    from modulos.ferramentas.revisao_interativa import renomear
    n = len(pulados)
    if not tela.sim(f"Ficaram {n} nome(s) sem aluno correspondente na lista. Deseja cadastrá-los manualmente "
                    f"no alunos.csv agora?", entrada):
        return 0, 0
    tela.info(f"Lista: {tela.caminho(planilha)}  (a pessoa vai no fim; uma cópia fica ao lado)", saida)
    feitos = fotos = 0
    for i, (nome_arquivo, itens) in enumerate(pulados, 1):
        tela.cabecalho(f"CADASTRAR {i} de {n}:  \"{nome_arquivo}\"  ({len(itens)} arquivo(s))", saida)
        tela.status("fraco", "O nome tem de ser igual ao que o site mostra no menu do aluno.", saida, recuo=4)
        while True:
            nome = tela.perguntar(f"  1) Nome do aluno (Enter = \"{nome_arquivo}\", p = pular): ", entrada)
            if nome.lower() == "p":
                break
            nome = nome or nome_arquivo
            email = tela.perguntar("  2) E-mail do aluno: ", entrada)
            senha = _senha(entrada, "  3) Senha do aluno (não aparece): ")
            motivo = validar_novo(nome, email, senha, alunos)
            if motivo:
                tela.erro(f"Não cadastrei: {motivo}. Tente de novo ou digite p no nome para pular.", saida)
                continue
            try:
                copia = acrescentar_aluno(planilha, nome, email, senha)
            except (OSError, ValueError, KeyError) as e:
                tela.erro(f"Não consegui gravar no alunos.csv ({type(e).__name__}): nada foi cadastrado.", saida)
                break
            novo = Aluno(nome.strip(), email.strip(), senha=senha)
            alunos.append(novo)
            feitos += 1
            tela.ok(f"Cadastrado: {novo.nome} (cópia: {copia.name})", saida)
            for item in itens:
                feito, porque = renomear(pasta_raiz, item.pasta, item.arquivo, novo, banco, log_csv)
                if feito:
                    fotos += 1
                    tela.ok(f"Foto ligada ao aluno: {item.pasta}/{feito}", saida)
                elif porque.startswith("ja esta"):
                    tela.ok(f"Foto já tem o nome do aluno: {item.pasta}/{item.arquivo}", saida)
                else:
                    tela.erro(f"Foto NÃO renomeada: {item.pasta}/{item.arquivo}: {porque}", saida)
            break
    if feitos:
        tela.info("Faça \"Conferir contas no site\" para testar o login dos alunos novos.", saida)
    return feitos, fotos
