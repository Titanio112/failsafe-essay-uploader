"""Auditoria antes do push (bug 025): ``python -m modulos.ferramentas.auditoria_publica``.

O repositório é público. Confere os arquivos que o git vai publicar
(``git ls-files``) e diz ONDE há problema, nunca o valor:

- nome de arquivo proibido: anotação/memória de IA, foto, banco, planilha,
  ``.env``, CSV fora da lista permitida (M3: ``exemplos/**/alunos.csv`` é
  permitido se só tiver e-mail de exemplo, ``@example.com``);
- conteúdo com nome, e-mail ou senha de aluno (``dados/dados_alunos.csv`` e
  ``alunos.csv`` de cada turma), valor do ``.env`` ou o usuário do Windows
  (caminho deve usar ``%USERNAME%``).

Saída 0 = nada encontrado; 1 = achou algo (não faça push).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

NOMES_PROIBIDOS = re.compile(
    r"(^|/)(AGENTS\.md|PROJECT_MEMORY\.md|MUDANCA_DE_PASTA\.md|CLAUDE(\.local)?\.md|\.clinerules"
    r"|REGRAS_CLINE[^/]*|PROMPT_CLINE[^/]*|HANDOFF[^/]*|TAREFAS_ATUAIS\.md|PENDENCIAS\.md|\.env)$"
    r"|(^|/)(\.claude|\.cline|\.cursor|\.windsurf|memory|historico|relatorios|logs|diagnosticos)/"
    r"|\.(jpe?g|png|heic|webp|pdf|db|sqlite3?|xlsx?)$",
    re.IGNORECASE,
)
CSV_PERMITIDOS = {"dados/temas_site.csv"}
# M3: lista de alunos inventada da demonstração; só com e-mail de exemplo (RFC 2606)
EXEMPLO_ALUNOS = re.compile(r"^exemplos/(.+/)?alunos\.csv$")
DOMINIOS_EXEMPLO = {"example.com", "example.org", "example.net"}


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


def nome_proibido(caminho: str) -> str | None:
    """Motivo se o arquivo não pode ser público pelo nome; senão None."""
    if caminho.endswith("/.gitkeep"):
        return None  # só guarda a pasta vazia
    if NOMES_PROIBIDOS.search(caminho):
        return "arquivo que nao pode ser publico (IA, foto, banco, planilha, .env ou pasta local)"
    if caminho.lower().endswith(".csv") and caminho not in CSV_PERMITIDOS and not EXEMPLO_ALUNOS.match(caminho):
        return "CSV fora da lista permitida (pode ter dados de alunos)"
    return None


def alvos_locais(raiz: Path) -> dict[str, str]:
    """{rótulo: texto normalizado} a procurar. Os valores ficam só na memória."""
    from modulos.dados.arquivos_csv import ler_texto
    alvos: dict[str, str] = {}
    lista = raiz / "dados" / "dados_alunos.csv"
    if lista.is_file():
        linhas = [l.split(";" if ";" in l else ",") for l in ler_texto(lista).splitlines()[1:]]
        for n, partes in enumerate(linhas, 1):
            if partes and partes[0].strip():
                alvos[f"nome do aluno {n}"] = _norm(partes[0])
            if len(partes) > 1 and "@" in partes[1]:
                alvos[f"e-mail do aluno {n}"] = _norm(partes[1])
    # M3: a lista de cada turma (nome, e-mail e senha)
    from modulos.base.config import PASTA_REDACOES, Config
    from modulos.dados.planilha_arquivos import carregar_alunos
    for t, planilha in enumerate(sorted((raiz / PASTA_REDACOES).glob("*/*/alunos.csv")), 1):
        cfg = Config()
        cfg.planilha = planilha
        try:
            alunos = carregar_alunos(cfg)
        except Exception:  # noqa: BLE001 - lista ilegível não derruba a auditoria
            alunos = []
        for n, aluno in enumerate(alunos, 1):
            alvos[f"nome do aluno {n} da turma {t}"] = _norm(aluno.nome)
            alvos[f"e-mail do aluno {n} da turma {t}"] = _norm(aluno.email)
            alvos[f"senha do aluno {n} da turma {t}"] = _norm(aluno.senha)
    env = raiz / ".env"
    if env.is_file():
        for linha in ler_texto(env).splitlines():
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.+)$", linha)
            if m and not m.group(2).strip().startswith("<"):
                alvos[f"valor de {m.group(1)} (.env)"] = _norm(m.group(2).strip().strip('"'))
    usuario = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if usuario:
        alvos["usuario do Windows (use %USERNAME%)"] = _norm(usuario)
    return {k: v for k, v in alvos.items() if len(v) >= 4}


def auditar(arquivos: dict[str, str], alvos: dict[str, str]) -> list[tuple[str, str]]:
    """[(arquivo, motivo)] para {caminho: conteúdo} contra os alvos."""
    achados = []
    for caminho, conteudo in sorted(arquivos.items()):
        motivo = nome_proibido(caminho)
        if motivo:
            achados.append((caminho, motivo))
        dominios = {d.lower() for d in re.findall(r"@([\w.-]+)", conteudo)}
        if EXEMPLO_ALUNOS.match(caminho) and not dominios <= DOMINIOS_EXEMPLO:
            achados.append((caminho, "lista de exemplos/ com e-mail que nao e de exemplo (use @example.com)"))
        texto = _norm(conteudo)
        achados.extend((caminho, rotulo) for rotulo, valor in alvos.items() if valor in texto)
    return achados


def _arquivos_do_git(raiz: Path) -> dict[str, str]:
    nomes = subprocess.run(["git", "ls-files", "-z"], cwd=raiz, capture_output=True, check=True).stdout
    arquivos = {}
    for nome in filter(None, nomes.decode("utf-8").split("\0")):
        caminho = raiz / nome
        arquivos[nome] = caminho.read_bytes().decode("utf-8", "replace") if caminho.is_file() else ""
    return arquivos


def main() -> int:
    raiz = Path(__file__).resolve().parents[2]
    alvos = alvos_locais(raiz)
    achados = auditar(_arquivos_do_git(raiz), alvos)
    print(f"Auditoria: {len(alvos)} valor(es) procurado(s) nos arquivos do git (nada e mostrado).")
    for caminho, motivo in achados:
        print(f"  !! {caminho}: {motivo}")
    print("Nada encontrado: pode fazer push." if not achados else
          f"{len(achados)} problema(s): NAO faca push antes de resolver.")
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
