"""Progresso em SQLite, logs sanitizados e relatórios CSV/TXT.

Estados por aluno+arquivo: A_ENVIAR, ENVIANDO, ENVIADO, JA_ENVIADO,
ERRO, REVISAO_MANUAL, PULADO.
"""

from __future__ import annotations

import csv
import logging
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from modulos.dados.planilha_arquivos import (
    ResultadoConciliacao,
    mascarar_email,
    normalizar_nome,
)

A_ENVIAR = "A_ENVIAR"
ENVIANDO = "ENVIANDO"
ENVIADO = "ENVIADO"
JA_ENVIADO = "JA_ENVIADO"
ERRO = "ERRO"
REVISAO_MANUAL = "REVISAO_MANUAL"
PULADO = "PULADO"


class LimiteEnvios(RuntimeError):
    """Aluno atingiu o máximo de envios permitidos."""


# ─── Logging sanitizado ──────────────────────────────────────

# T48: segredo = o VALOR das senhas do .env, ou "senha=..."/"password: ...".
# Antes qualquer mensagem com a palavra "senha" sumia, inclusive as que
# explicam o problema ("senha padrao errada?").
_PADRAO_SEGREDO = re.compile(r"(senha|password|passwd|token|secret|cookie)\s*[:=]\s*\S", re.IGNORECASE)
_VARIAVEIS_SECRETAS = ("ESQUEMA_SENHA_PADRAO", "ESQUEMA_SENHA_TESTE")


def _tem_segredo(texto: str) -> bool:
    import os
    if _PADRAO_SEGREDO.search(texto):
        return True
    valores = (os.environ.get(v, "") for v in _VARIAVEIS_SECRETAS)
    return any(len(valor) >= 3 and valor in texto for valor in valores)


class _FiltroSanitizador(logging.Filter):
    """Suprime mensagens que contenham segredos."""

    def filter(self, record: logging.LogRecord) -> bool:
        if _tem_segredo(str(record.getMessage())):
            record.msg = "[suprimido: possível segredo no log]"
            record.args = ()
        if record.exc_info:
            # T44: o traceback também passa pelo filtro
            import traceback
            texto = "".join(traceback.format_exception(*record.exc_info))
            if _tem_segredo(texto):
                record.msg = f"{record.msg} [traceback suprimido: possível segredo]"
                record.exc_info = None
                record.exc_text = None
        return True


def configurar_logging(pasta_logs: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("automacao_redacoes")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console = logging.StreamHandler(sys.stdout)
    from modulos.base.tela import FormatoTerminal
    console.setFormatter(FormatoTerminal())  # T41: visual do terminal em tela.py
    console.addFilter(_FiltroSanitizador())
    # T54: log.info(..., extra={"so_no_arquivo": True}) vai só para o arquivo
    console.addFilter(lambda record: not getattr(record, "so_no_arquivo", False))
    logger.addHandler(console)
    if pasta_logs is not None:
        pasta_logs.mkdir(parents=True, exist_ok=True)
        arq = logging.FileHandler(pasta_logs / "automacao.log", encoding="utf-8")
        arq.setFormatter(fmt)
        arq.addFilter(_FiltroSanitizador())
        logger.addHandler(arq)
    return logger


# ─── SQLite ──────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS progresso (
    aluno_id     TEXT NOT NULL,
    arquivo      TEXT NOT NULL,
    pasta        TEXT DEFAULT '',
    estado       TEXT NOT NULL,
    tentativas   INTEGER NOT NULL DEFAULT 0,
    detalhe      TEXT DEFAULT '',
    hash_arquivo TEXT DEFAULT '',
    criado_em    TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    PRIMARY KEY (aluno_id, arquivo)
);
CREATE TABLE IF NOT EXISTS envios (
    aluno_id      TEXT NOT NULL,
    arquivo       TEXT NOT NULL,
    registrado_em TEXT NOT NULL
);
"""



class Progresso:
    """Persistência de estado. Fechar com :meth:`close` ou usar como contexto."""

    def __init__(self, caminho_db: Path):
        caminho_db = Path(caminho_db)
        if str(caminho_db) != ":memory:":
            caminho_db.parent.mkdir(parents=True, exist_ok=True)
        # T44: outro programa com o banco aberto -> espera até 30 s em vez de quebrar
        self.con = sqlite3.connect(caminho_db, timeout=30)
        self.con.executescript(_SCHEMA)
        self.resolver_enviando_pendentes()

    def __enter__(self) -> "Progresso":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @staticmethod
    def _agora() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def resolver_enviando_pendentes(self) -> int:
        """Retomada segura: converte ENVIANDO em REVISAO_MANUAL.

        A confirmação inequívoca depende da lista remota (Fase 2+); sem ela,
        nunca reenviar automaticamente.
        """
        cur = self.con.execute(
            "UPDATE progresso SET estado = ?, detalhe = ?, atualizado_em = ? "
            "WHERE estado = ?",
            (
                REVISAO_MANUAL,
                "retomada: era ENVIANDO; confirmar na plataforma antes de qualquer ação",
                self._agora(),
                ENVIANDO,
            ),
        )
        self.con.commit()
        return cur.rowcount

    def marcar(
        self,
        aluno_id: str,
        arquivo: str,
        estado: str,
        pasta: str = "",
        detalhe: str = "",
        hash_arquivo: str = "",
    ) -> None:
        agora = self._agora()
        self.con.execute(
            """
            INSERT INTO progresso (aluno_id, arquivo, pasta, estado, tentativas,
                                   detalhe, hash_arquivo, criado_em, atualizado_em)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
            ON CONFLICT(aluno_id, arquivo)
            DO UPDATE SET estado = excluded.estado,
                          pasta = excluded.pasta,
                          detalhe = excluded.detalhe,
                          hash_arquivo = COALESCE(NULLIF(excluded.hash_arquivo, ''), progresso.hash_arquivo),
                          atualizado_em = excluded.atualizado_em
            """,
            (aluno_id, arquivo, pasta, estado, detalhe, hash_arquivo, agora, agora),
        )
        self.con.commit()

    def obter(self, aluno_id: str, arquivo: str) -> dict | None:
        row = self.con.execute(
            "SELECT aluno_id, arquivo, pasta, estado, tentativas, detalhe, "
            "       criado_em, atualizado_em, hash_arquivo "
            "FROM progresso WHERE aluno_id = ? AND arquivo = ?",
            (aluno_id, arquivo),
        ).fetchone()
        if not row:
            return None
        chaves = ("aluno_id", "arquivo", "pasta", "estado",
                  "tentativas", "detalhe", "criado_em", "atualizado_em", "hash_arquivo")
        return dict(zip(chaves, row))



    def enviados_hoje(self, aluno_id: str, codigo: str) -> int:
        """Arquivos deste aluno neste código marcados ENVIADO ou JA_ENVIADO
        hoje (T35; T44: "hoje" no horário de Brasília, como o site). O envio
        grava o código do tema na coluna ``pasta`` (envio_item.marcar)."""
        from modulos.base import relogio
        hoje = relogio.hoje()
        linhas = self.con.execute(
            "SELECT atualizado_em FROM progresso WHERE aluno_id = ? AND pasta = ? AND estado IN (?, ?)",
            (aluno_id, codigo, ENVIADO, JA_ENVIADO),
        ).fetchall()
        return sum(1 for (quando,) in linhas
                   if datetime.fromisoformat(quando).astimezone(relogio.FUSO_BRASILIA).date() == hoje)

    def registro_do_conteudo(self, aluno_id: str, hash_arquivo: str, exceto: str) -> dict | None:
        """T44: o MESMO arquivo (mesmo conteúdo) já registrado para este aluno
        com outro nome/pasta, num estado que não reenvia. Pega arquivo
        renomeado, movido de pasta ou copiado de novo."""
        if not hash_arquivo:
            return None
        row = self.con.execute(
            "SELECT arquivo, estado FROM progresso WHERE aluno_id = ? AND hash_arquivo = ? "
            "AND arquivo != ? AND estado IN (?, ?, ?, ?) LIMIT 1",
            (aluno_id, hash_arquivo, exceto, ENVIADO, JA_ENVIADO, REVISAO_MANUAL, ENVIANDO),
        ).fetchone()
        return {"arquivo": row[0], "estado": row[1]} if row else None

    def conteudo_de_outro_aluno(self, aluno_id: str, hash_arquivo: str) -> dict | None:
        """Bug 013: a MESMA foto já registrada (enviada, pulada, em revisão)
        para OUTRO aluno. Uma foto é de uma pessoa só: não vai para a segunda.
        O ensaio (chave "ensaio/...") manda fotos reais para a conta de teste
        de propósito e não conta."""
        if not hash_arquivo:
            return None
        row = self.con.execute(
            "SELECT aluno_id, arquivo, estado FROM progresso WHERE aluno_id != ? AND hash_arquivo = ? "
            "AND arquivo NOT LIKE 'ensaio/%' AND estado IN (?, ?, ?, ?) LIMIT 1",
            (aluno_id, hash_arquivo, ENVIADO, JA_ENVIADO, REVISAO_MANUAL, ENVIANDO),
        ).fetchone()
        return {"aluno_id": row[0], "arquivo": row[1], "estado": row[2]} if row else None

    # ─── Envios por aluno (limite de 4) ──────────────────────

    def envios_de(self, aluno_id: str) -> int:
        row = self.con.execute(
            "SELECT COUNT(*) FROM envios WHERE aluno_id = ?", (aluno_id,)
        ).fetchone()
        return int(row[0])

    def registrar_envio(self, aluno_id: str, arquivo: str, max_envios: int = 4) -> int:
        """NÃO usado pelo fluxo (sem limite por aluno desde 22/10); mantido
        pelo teste protegido. Registra um envio, respeitando o limite.

        Levanta :class:`LimiteEnvios` ao atingir o teto; nesse caso o aluno
        deve ser parado.
        """
        if self.envios_de(aluno_id) >= max_envios:
            raise LimiteEnvios(
                f"Aluno atingiu o máximo de {max_envios} envios; parando este aluno."
            )
        self.con.execute(
            "INSERT INTO envios (aluno_id, arquivo, registrado_em) VALUES (?, ?, ?)",
            (aluno_id, arquivo, self._agora()),
        )
        self.con.commit()
        return self.envios_de(aluno_id)

    def close(self) -> None:
        self.con.close()


# ─── Relatórios ──────────────────────────────────────────────


def gerar_relatorio_conciliacao(resultado: ResultadoConciliacao, caminho_csv: Path) -> Path:
    """CSV para revisão humana. E-mails mascarados; nomes completos são
    necessários para a conciliação e o arquivo nunca é versionado."""
    caminho_csv = Path(caminho_csv)
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "pasta", "arquivo", "pessoa_arquivo", "estado",
        "aluno_nome", "aluno_email_mascarado",
        "score_fuzzy", "segundo_score", "candidatos_fuzzy", "observacao",
    ]
    itens = sorted(resultado.itens, key=lambda i: (normalizar_nome(i.pessoa), i.pasta))
    with caminho_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for item in itens:
            candidatos = ""
            if item.candidatos:
                candidatos = " | ".join(
                    f"{c.nome} ({mascarar_email(c.email)})" for c in item.candidatos
                )
            w.writerow({
                "pasta": item.pasta,
                "arquivo": item.arquivo,
                "pessoa_arquivo": item.pessoa,
                "estado": item.estado,
                "aluno_nome": item.aluno.nome if item.aluno else "",
                "aluno_email_mascarado": (
                    mascarar_email(item.aluno.email) if item.aluno else ""
                ),
                "score_fuzzy": item.score_fuzzy or "",
                "segundo_score": item.segundo_score or "",
                "candidatos_fuzzy": candidatos,
                "observacao": item.observacao,
            })
    return caminho_csv


def gerar_fila_dry_run(resultado: ResultadoConciliacao, caminho_txt: Path) -> Path:
    """TXT com a fila real (apenas EXATO_UNICO), e-mails mascarados."""
    caminho_txt = Path(caminho_txt)
    caminho_txt.parent.mkdir(parents=True, exist_ok=True)
    fila = resultado.fila_validada()
    linhas = [
        "DRY-RUN — fila de envio (somente correspondências exatas únicas)",
        f"Total: {len(fila)} arquivo(s)",
        "",
    ]
    for item in sorted(fila, key=lambda i: (i.aluno.nome_norm, i.pasta)):
        linhas.append(
            f"{item.aluno.nome} <{mascarar_email(item.aluno.email)}> "
            f"<- {item.pasta}/{item.arquivo}"
        )
    with caminho_txt.open("w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return caminho_txt
