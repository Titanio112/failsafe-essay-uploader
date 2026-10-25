"""Leitura do XLSX, listagem de JPGs, normalizacao e conciliacao.

Estados de cada arquivo conciliado:

- ``EXATO_UNICO``: correspondência normalizada exata e única com um aluno.
- ``SUGESTAO_FUZZY``: melhor candidato aproximado acima do limiar e com
  margem para o segundo. NUNCA entra na fila real sem revisão humana.
- ``AMBIGUO``: correspondência exata com mais de um aluno, ou fuzzy com
  margem insuficiente / mais de um candidato no limiar.
- ``ARQUIVO_SEM_ALUNO``: nenhum candidato acima do limiar.
- ``ALUNO_SEM_ARQUIVO``: aluno da planilha sem nenhum arquivo associado.
- ``SEM_CODIGO``: arquivo sem código no nome nem na pasta.
- ``CODIGO_INVALIDO``: código extraído não existe no combo do site.
- ``REVISAO_MANUAL``: casos que exigem revisão humana (duplicatas, conflitos, etc.)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

import openpyxl
from rapidfuzz import fuzz

from modulos.base.config import Config
from modulos.base.estados import (
    EXATO_UNICO,
    SUGESTAO_FUZZY,
    AMBIGUO,
    ARQUIVO_SEM_ALUNO,
    ALUNO_SEM_ARQUIVO,
    SEM_CODIGO,
    CODIGO_INVALIDO,
    REVISAO_MANUAL,
    SIMULADO,
    ESTADOS_CONCILIACAO,
    MARCADOR_PESSOA,
)

class PlanilhaError(RuntimeError):
    """Planilha ausente ou sem as colunas esperadas."""

from modulos.dados.normalizacao import (
    normalizar_nome,
    sem_numero_final,
    extrair_pessoa,
    extrair_codigo_do_arquivo,
    extrair_codigo_do_tema_site,
    extrair_codigo_tema,
    PADRAO_CODIGO_ARQUIVO,
    PADRAO_CODIGO_TEMA_SITE,
)


@dataclass
class Aluno:
    nome: str
    email: str
    creditos: int | None = None

    @property
    def nome_norm(self) -> str:
        return normalizar_nome(self.nome)

    @property
    def id(self) -> str:
        return self.email.casefold() if self.email else self.nome_norm


@dataclass
class ItemConciliacao:
    pasta: str
    arquivo: str
    pessoa: str
    estado: str
    aluno: Aluno | None = None
    candidatos: list | None = None
    score_fuzzy: float = 0.0
    segundo_score: float = 0.0
    observacao: str = ""
    codigo_tema: str = ""
    codigo_valido: bool = True

    @property
    def chave(self) -> str:
        return f"{self.pasta}/{self.arquivo}"


@dataclass
class ResultadoConciliacao:
    itens: list

    def por_estado(self, estado: str) -> list:
        return [i for i in self.itens if i.estado == estado]

    def fila_validada(self) -> list:
        return [i for i in self.itens if i.estado == EXATO_UNICO]

    def resumo(self) -> dict:
        return {e: len(self.por_estado(e)) for e in ESTADOS_CONCILIACAO}


def _emitir_aviso(mensagem: str) -> None:
    from modulos.base import tela
    tela.aviso(mensagem)
    warnings.warn(f"[AVISO] {mensagem}", UserWarning, stacklevel=3)


def _sugerir_fuzzy(norm: str, alunos: list, limiar: float, margem: float):
    pontuacoes = sorted(
        ((fuzz.token_set_ratio(norm, a.nome_norm), a) for a in alunos),
        key=lambda t: t[0],
        reverse=True,
    )
    if not pontuacoes or pontuacoes[0][0] < limiar:
        return ARQUIVO_SEM_ALUNO, None, [], 0.0, 0.0
    melhor_score, melhor_aluno = pontuacoes[0]
    segundo_score = pontuacoes[1][0] if len(pontuacoes) > 1 else 0.0
    if melhor_score - segundo_score < margem:
        candidatos = [a for s, a in pontuacoes if s >= limiar]
        return AMBIGUO, None, candidatos, melhor_score, segundo_score
    return SUGESTAO_FUZZY, melhor_aluno, [melhor_aluno], melhor_score, segundo_score


def _coluna(nome: str) -> str:
    """Cabeçalho comparável: "E-mail", "e mail", "EMAIL" -> "email" (T43)."""
    return normalizar_nome(nome).replace(" ", "")


def _carregar_alunos_csv(cfg: Config) -> list[Aluno]:
    """Lista de alunos em CSV (``;`` ou ``,``), colunas nome/e-mail sem
    diferenciar maiúsculas. Coluna de senha é ignorada: a senha vem só do
    .env (ESQUEMA_SENHA_PADRAO) e nunca é lida de arquivo."""
    import csv
    from modulos.dados.arquivos_csv import abrir_csv
    with abrir_csv(cfg.planilha) as f:
        cabecalho = f.readline()
        if cabecalho.strip().lower().startswith("sep="):  # linha que o Excel às vezes põe
            cabecalho = f.readline()
        inicio = f.tell() - len(cabecalho)
        f.seek(inicio)
        delimitador = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
        leitor = csv.reader(f, delimiter=delimitador)
        colunas = [_coluna(c) for c in next(leitor, [])]
        if _coluna(cfg.coluna_nome) not in colunas or _coluna(cfg.coluna_email) not in colunas:
            raise PlanilhaError(
                f"Cabeçalho do CSV sem as colunas '{cfg.coluna_nome}' e '{cfg.coluna_email}'. "
                f"Colunas encontradas: {colunas}"
            )
        if "senha" in colunas:
            # T57: aparecia em toda tela sem ajudar; agora só no log (e no warning, para testes)
            mensagem = "Coluna 'Senha' da lista de alunos ignorada; a senha vem de ESQUEMA_SENHA_PADRAO no .env."
            import logging
            logging.getLogger("automacao_redacoes").info(mensagem, extra={"so_no_arquivo": True})
            warnings.warn(f"[AVISO] {mensagem}", UserWarning, stacklevel=2)
        idx_nome = colunas.index(_coluna(cfg.coluna_nome))
        idx_email = colunas.index(_coluna(cfg.coluna_email))
        alunos = []
        for row in leitor:
            if len(row) <= max(idx_nome, idx_email):
                continue
            nome, email = row[idx_nome].strip(), row[idx_email].strip()
            if nome and email:
                alunos.append(Aluno(nome=nome, email=email))
    return alunos


def carregar_alunos(cfg: Config) -> list[Aluno]:
    if Path(cfg.planilha).suffix.lower() == ".csv":
        return _carregar_alunos_csv(cfg)
    wb = openpyxl.load_workbook(cfg.planilha, data_only=True)
    ws = wb[cfg.aba_planilha] if cfg.aba_planilha else wb.active

    # Localizar linha de cabeçalho pelo conteúdo (colunas "nome" e "email")
    # Procura nas primeiras 10 linhas
    header_row = None
    header_cols = None
    for row_idx in range(1, min(11, ws.max_row + 1)):
        row_vals = [_coluna(str(c.value)) if c.value else "" for c in ws[row_idx]]
        if _coluna(cfg.coluna_nome) in row_vals and _coluna(cfg.coluna_email) in row_vals:
            header_row = row_idx
            header_cols = row_vals
            break
    
    if header_row is None:
        # Listar colunas encontradas nas primeiras 10 linhas para erro claro
        found_cols = set()
        for row_idx in range(1, min(11, ws.max_row + 1)):
            row_vals = [str(c.value).strip().lower() if c.value else "" for c in ws[row_idx]]
            found_cols.update(row_vals)
        raise PlanilhaError(
            f"Cabeçalho não encontrado (colunas 'nome' e 'email' obrigatórias). "
            f"Colunas encontradas nas primeiras 10 linhas: {sorted(found_cols)}"
        )

    def find_col(col_name: str) -> int:
        """Encontra índice da coluna pelo nome."""
        try:
            return header_cols.index(_coluna(col_name))
        except ValueError:
            raise PlanilhaError(f"Coluna não encontrada: {col_name}")

    idx_nome = find_col(cfg.coluna_nome)
    idx_email = find_col(cfg.coluna_email)
    # Só nome e e-mail são lidos; outras colunas da planilha são ignoradas.

    alunos = []
    for row in ws.iter_rows(min_row=header_row + 1, values_only=True):
        if len(row) <= max(idx_nome, idx_email):
            continue
        nome = str(row[idx_nome]).strip() if row[idx_nome] else ""
        email = str(row[idx_email]).strip() if row[idx_email] else ""
        if not nome or not email:
            continue
        alunos.append(Aluno(nome=nome, email=email))
    return alunos


def descobrir_pastas(cfg: Config) -> list[Path]:
    raiz = cfg.pasta_raiz
    if not raiz.exists():
        return []
    return sorted([p for p in raiz.iterdir() if p.is_dir() and not p.name.startswith(".")])


ARQUIVOS_DO_SISTEMA = {"thumbs.db", "desktop.ini"}


def descobrir_arquivos(cfg: Config) -> dict[str, list[str]]:
    extensoes_permitidas = {ext.lower() for ext in cfg.extensoes}
    resultado = {}
    if cfg.pasta_raiz.exists():
        # Bug 015: foto solta na raiz não tem tema; avisa em vez de sumir
        for f in sorted(cfg.pasta_raiz.iterdir(), key=lambda x: x.name):
            if f.is_file() and f.suffix.lower() in extensoes_permitidas and not f.name.startswith((".", "~$")):
                _emitir_aviso(f"Arquivo fora de pasta de tema ignorado: {f.name} "
                              "(coloque dentro da pasta do tema)")
    for pasta in descobrir_pastas(cfg):
        arquivos = []
        for f in sorted(pasta.iterdir(), key=lambda x: x.name):
            if f.name.startswith((".", "~$")) or f.name.casefold() in ARQUIVOS_DO_SISTEMA:
                continue  # T43: ._ do Mac, temporário do Office, Thumbs.db, desktop.ini
            if f.is_dir():
                _emitir_aviso(f"Subpasta ignorada: {pasta.name}/{f.name} (coloque os JPGs direto na pasta do tema)")
                continue
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in extensoes_permitidas:
                _emitir_aviso(f"Arquivo ignorado (extensão não permitida): {pasta.name}/{f.name} (ext: {ext})")
                continue
            arquivos.append(f.name)
        if arquivos:
            resultado[pasta.name] = arquivos
    return resultado


def eh_folha_em_branco(norm: str) -> bool:
    """Nome do arquivo (normalizado) marca folha em branco: "x em branco" (T27)."""
    return " em branco" in f" {norm}"


def candidatos_nome_parcial(norm: str, alunos: list[Aluno]) -> list[Aluno]:
    """Alunos cujo nome contém TODAS as palavras do nome do arquivo (T26).

    Só para SUGERIR em dados/nomes_aprovados.csv; nunca envia sozinho.
    Exige ao menos 2 palavras e a mesma 1ª palavra."""
    palavras = norm.split()
    if len(palavras) < 2:
        return []
    return [
        a for a in alunos
        if a.nome_norm.split()[:1] == palavras[:1] and set(palavras) <= set(a.nome_norm.split())
    ]


def _resolver_alunos(norm: str, por_norm: dict,
                     nomes_aprovados: Optional[dict] = None) -> tuple[list[Aluno], bool]:
    """(candidatos, aprovado): nome exato primeiro; sem exato, o nome do
    arquivo aprovado por humano em dados/nomes_aprovados.csv (T26).
    T43: sem achar, tenta de novo sem o número do fim ("Ana Souza 2")."""
    for chave in dict.fromkeys((norm, sem_numero_final(norm))):
        exatos = por_norm.get(chave, [])
        if exatos:
            return exatos, False
        if nomes_aprovados and chave in nomes_aprovados:
            return [nomes_aprovados[chave]], True
    return [], False


def conciliar(
    alunos: list[Aluno],
    arquivos_por_pasta: dict[str, list[str]],
    codigos_site: Set[str],
    limiar: float = 95.0,
    margem: float = 8.0,
    nomes_aprovados: Optional[dict] = None,
    codigos_pasta: Optional[dict] = None,
) -> ResultadoConciliacao:
    """``nomes_aprovados``: {nome normalizado do arquivo: Aluno}, aprovado por
    humano em dados/nomes_aprovados.csv; conta como nome exato.
    ``codigos_pasta``: {pasta sem código: código}, aprovado por humano em
    dados/pastas_aprovadas.csv (T28); vale só para pasta SEM código no nome."""
    # Pasta usada só para extrair o código ("3B - X" aprovada como 9 -> "9 - 3B - X");
    # item.pasta continua o nome real (caminho do arquivo).
    pasta_cod = {
        pasta: (f"{codigos_pasta[pasta]} - {pasta}"
                if codigos_pasta and pasta in codigos_pasta and not PADRAO_CODIGO_ARQUIVO.match(pasta)
                else pasta)
        for pasta in arquivos_por_pasta
    }
    por_norm = {}
    for a in alunos:
        por_norm.setdefault(a.nome_norm, []).append(a)

    # Detectar códigos duplicados no combo do site (ex.: 0000 aparece 2x para Simulados)
    codigos_duplicados_site: Set[str] = set()
    if codigos_site:
        contagem_codigos: dict[str, int] = {}
        for cod in codigos_site:
            contagem_codigos[cod] = contagem_codigos.get(cod, 0) + 1
        codigos_duplicados_site = {cod for cod, count in contagem_codigos.items() if count > 1}

    # Contar quantos arquivos cada aluno tem por código NA MESMA PASTA (antes
    # de processar): dois arquivos do aluno na mesma pasta = duplicata.
    # T35: mesmo código em pastas diferentes (ex.: tema genérico 000) é
    # permitido; o envio confere pela contagem do dia (envio_item).
    from collections import defaultdict
    contagem_aluno_codigo: dict[tuple[str, str, str], int] = defaultdict(int)

    # Primeira passada: contar
    for pasta, arquivos in arquivos_por_pasta.items():
        for nome_arquivo in arquivos:
            pessoa = extrair_pessoa(nome_arquivo)
            norm = normalizar_nome(pessoa)
            codigo = extrair_codigo_tema(nome_arquivo, pasta_cod[pasta])
            if codigo and codigo != "" and not eh_folha_em_branco(norm):
                exatos, _ = _resolver_alunos(norm, por_norm, nomes_aprovados)
                if len(exatos) == 1:
                    aluno_match = exatos[0]
                    key = (aluno_match.id, codigo, pasta)
                    contagem_aluno_codigo[key] += 1

    itens = []
    vistos_por_aluno_codigo: dict[tuple[str, str, str], int] = {}

    for pasta, arquivos in arquivos_por_pasta.items():
        for nome_arquivo in arquivos:
            pessoa = extrair_pessoa(nome_arquivo)
            norm = normalizar_nome(pessoa)

            # Folha em branco nunca entra na fila, nem com nome aprovado (T27)
            if eh_folha_em_branco(norm):
                itens.append(ItemConciliacao(
                    pasta=pasta, arquivo=nome_arquivo, pessoa=pessoa,
                    estado=REVISAO_MANUAL, observacao="folha em branco: decidir à mão",
                    codigo_tema=extrair_codigo_tema(nome_arquivo, pasta_cod[pasta]) or "",
                ))
                continue

            # Extrair códigos do arquivo e da pasta separadamente para detectar conflito
            stem = Path(nome_arquivo).stem
            match_arquivo = PADRAO_CODIGO_ARQUIVO.match(stem)
            codigo_arquivo = match_arquivo.group(1) if match_arquivo else None
            
            codigo_pasta = None
            if pasta:
                match_pasta = PADRAO_CODIGO_ARQUIVO.match(pasta_cod[pasta])
                if match_pasta:
                    codigo_pasta = match_pasta.group(1)
            
            # Detectar conflito: ambos existem e são diferentes
            conflito_pasta_arquivo = (
                codigo_arquivo is not None and 
                codigo_pasta is not None and 
                codigo_arquivo != codigo_pasta
            )
            
            # Código efetivo (prioridade: arquivo > pasta)
            codigo = codigo_arquivo or codigo_pasta
            codigo_valido = True
            estado_inicial = ""
            obs_inicial = ""

            if conflito_pasta_arquivo:
                estado_inicial = REVISAO_MANUAL
                codigo_valido = False
                obs_inicial = f"codigo {codigo_arquivo} no arquivo e {codigo_pasta} na pasta"
            elif codigo_arquivo is not None and codigo_pasta is None:
                # T43: "1 Ana.jpg" numa pasta sem tema: número de página, não tema
                estado_inicial = REVISAO_MANUAL
                codigo_valido = False
                obs_inicial = f"numero {codigo_arquivo} no inicio do arquivo numa pasta sem tema: pagina? decidir à mão"
            elif codigo is None:
                estado_inicial = SEM_CODIGO
                codigo_valido = False
            elif codigos_site and codigo not in codigos_site:
                estado_inicial = CODIGO_INVALIDO
                codigo_valido = False
            elif codigo and codigo in codigos_duplicados_site:
                estado_inicial = SIMULADO
                codigo_valido = True  # Código existe, mas é ambíguo no site
            else:
                estado_inicial = ""

            exatos, aprovado = _resolver_alunos(norm, por_norm, nomes_aprovados)

            if len(exatos) == 1:
                aluno_match = exatos[0]
                # Verificar se há duplicatas para este aluno+código
                key = (aluno_match.id, codigo, pasta) if codigo and codigo != "" else None
                tem_duplicata = key and contagem_aluno_codigo.get(key, 0) > 1

                numerado = (norm not in por_norm and not (nomes_aprovados and norm in nomes_aprovados)
                            and sem_numero_final(norm) != norm)
                if tem_duplicata:
                    estado = REVISAO_MANUAL
                    obs_inicial = obs_inicial or "mais de um arquivo do aluno nesta pasta (pagina 2? copia?): decidir à mão"
                elif numerado:
                    # T48: "Ana Souza 2.jpg" sozinho pode ser só a página 2 (a 1ª
                    # com o nome errado); quem decide é a pessoa.
                    estado = REVISAO_MANUAL
                    obs_inicial = obs_inicial or "numero no fim do nome (pagina 2? copia?): decidir à mão"
                else:
                    estado = EXATO_UNICO
                    if key:
                        vistos_por_aluno_codigo[key] = 1

                # Sobrescrever com estado_inicial se houver (SEM_CODIGO, CODIGO_INVALIDO)
                if estado_inicial:
                    estado = estado_inicial

                itens.append(ItemConciliacao(
                    pasta=pasta, arquivo=nome_arquivo, pessoa=pessoa,
                    estado=estado, aluno=aluno_match,
                    observacao=obs_inicial or (f"nome aprovado: arquivo -> {aluno_match.nome}" if aprovado else ""),
                    codigo_tema=codigo or "", codigo_valido=codigo_valido,
                ))

            elif len(exatos) > 1:
                obs = f"{len(exatos)} alunos com o mesmo nome normalizado"
                itens.append(ItemConciliacao(
                    pasta=pasta, arquivo=nome_arquivo, pessoa=pessoa,
                    estado=AMBIGUO, candidatos=list(exatos),
                    observacao=obs,
                    codigo_tema=codigo or "", codigo_valido=codigo_valido,
                ))

            else:
                estado, sugerido, candidatos, melhor, segundo = _sugerir_fuzzy(
                    sem_numero_final(norm), alunos, limiar, margem
                )
                obs = ""
                if estado == SUGESTAO_FUZZY:
                    obs = "revisao humana obrigatoria antes de validar"
                    if sugerido is not None:
                        if codigo and codigo != "":
                            key = (sugerido.id, codigo, pasta)
                            if key in vistos_por_aluno_codigo:
                                estado = REVISAO_MANUAL
                            else:
                                vistos_por_aluno_codigo[key] = 1
                elif estado == AMBIGUO:
                    obs = "candidatos fuzzy sem margem suficiente"
                if estado_inicial:
                    estado = estado_inicial
                    obs = obs_inicial or obs or ("aluno nao identificado" if estado_inicial == SEM_CODIGO else "codigo ausente ou invalido")

                itens.append(ItemConciliacao(
                    pasta=pasta, arquivo=nome_arquivo, pessoa=pessoa,
                    estado=estado, aluno=sugerido, candidatos=candidatos,
                    score_fuzzy=round(melhor, 2), segundo_score=round(segundo, 2),
                    observacao=obs,
                    codigo_tema=codigo or "", codigo_valido=codigo_valido,
                ))

    alunos_com_arquivo = set()
    for item in itens:
        if item.aluno:
            alunos_com_arquivo.add(id(item.aluno))

    for a in alunos:
        if id(a) not in alunos_com_arquivo:
            itens.append(ItemConciliacao(
                pasta="", arquivo="", pessoa=a.nome,
                estado=ALUNO_SEM_ARQUIVO, aluno=a,
            ))

    return ResultadoConciliacao(itens=itens)


def mascarar_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    local, dominio = email.split("@", 1)
    return f"{local[:2]}***@{dominio}" if local else f"***@{dominio}"