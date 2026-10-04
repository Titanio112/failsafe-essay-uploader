"""Configuração central: caminhos, parâmetros e trava de envio.

Padrão é dry-run. Envio real só é liberado pela combinação de
``--envio-real`` + resumo do lote + confirmação textual (ver main.py).
"""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from getpass import getpass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

MENSAGEM_BLOQUEIO = "[BLOQUEADO] Envio real desativado."


class EnvioBloqueado(RuntimeError):
    """Levantada quando uma ação de envio real é tentada sem autorização."""


def exigir_envio_real(envio_real: bool) -> None:
    """Trava central de envio. Qualquer envio real deve passar por aqui."""
    if not envio_real:
        raise EnvioBloqueado(MENSAGEM_BLOQUEIO)


class ConfigInvalida(RuntimeError):
    """Configuração ausente ou inconsistente."""


@dataclass
class Config:
    base_url: str = "https://www.esquemaredacao.com.br"
    login_path: str = "/auth/users/sign_in"
    tema: str = "000 dissertação"
    estilo_correcao: str = "ENEM"
    headless: bool = False
    slow_mo_ms: int = 500

    pasta_raiz: Path = field(default_factory=lambda: RAIZ / "Redações plataforma")
    planilha: Path = field(default_factory=Path)
    extensoes: tuple[str, ...] = (".jpg", ".jpeg")

    aba_planilha: str = "Planilha1"
    coluna_nome: str = "nome"
    coluna_email: str = "email"

    limiar_fuzzy: float = 95.0
    margem_minima: float = 8.0
    max_envios_por_aluno: int = 4
    max_envios_teste: int = 1  # config.ini pode sobrescrever
    exigir_aprovacao_fuzzy: bool = True

    max_envios_por_aluno: int = 4

    upload_timeout_segundos: int = 120
    confirmacao_timeout_segundos: int = 120
    poll_lista_segundos: int = 10
    pausa_envio_min_segundos: int = 8
    pausa_envio_max_segundos: int = 15

    banco_progresso: Path = field(default_factory=lambda: RAIZ / "relatorios" / "progresso.db")
    pasta_relatorios: Path = field(default_factory=lambda: RAIZ / "relatorios")

    def __post_init__(self) -> None:
        if not self.planilha or str(self.planilha) == ".":
            self.planilha = self.pasta_raiz / "Alunos para corrigir redacoes.xlsx"


def _ler_ini(caminho: Path) -> Config:
    cfg = Config()
    parser = configparser.ConfigParser()
    parser.read(caminho, encoding="utf-8")

    if parser.has_section("plataforma"):
        sec = parser["plataforma"]
        cfg.base_url = sec.get("base_url", cfg.base_url)
        cfg.login_path = sec.get("login_path", cfg.login_path)
        cfg.tema = sec.get("tema", cfg.tema)
        cfg.estilo_correcao = sec.get("estilo_correcao", cfg.estilo_correcao)
        cfg.headless = sec.getboolean("headless", cfg.headless)
        cfg.slow_mo_ms = sec.getint("slow_mo_ms", cfg.slow_mo_ms)

    if parser.has_section("dados"):
        sec = parser["dados"]
        pasta = sec.get("pasta_raiz", "")
        if pasta:
            cfg.pasta_raiz = (RAIZ / pasta).resolve()
        planilha = sec.get("planilha", "")
        if planilha:
            p = Path(planilha)
            cfg.planilha = p if p.is_absolute() else (cfg.pasta_raiz / p).resolve()
        exts = sec.get("extensoes", "")
        if exts:
            cfg.extensoes = tuple(
                e.strip().lower() for e in exts.split(",") if e.strip()
            )

    if parser.has_section("planilha"):
        sec = parser["planilha"]
        cfg.aba_planilha = sec.get("aba", cfg.aba_planilha)
        cfg.coluna_nome = sec.get("coluna_nome", cfg.coluna_nome)
        cfg.coluna_email = sec.get("coluna_email", cfg.coluna_email)
        cfg.coluna_sala = sec.get("coluna_sala", cfg.coluna_sala)

    if parser.has_section("conciliacao"):
        sec = parser["conciliacao"]
        cfg.limiar_fuzzy = sec.getfloat("limiar_fuzzy", cfg.limiar_fuzzy)
        cfg.margem_minima = sec.getfloat("margem_minima", cfg.margem_minima)
        cfg.max_envios_por_aluno = sec.getint("max_envios_por_aluno", cfg.max_envios_por_aluno)
        cfg.max_envios_teste = sec.getint("max_envios_teste", cfg.max_envios_teste)
        cfg.exigir_aprovacao_fuzzy = sec.getboolean(
            "exigir_aprovacao_fuzzy", cfg.exigir_aprovacao_fuzzy
        )

    if parser.has_section("seguranca"):
        cfg.max_envios_por_aluno = parser["seguranca"].getint(
            "max_envios_por_aluno", cfg.max_envios_por_aluno
        )

    if parser.has_section("esperas"):
        sec = parser["esperas"]
        cfg.upload_timeout_segundos = sec.getint(
            "upload_timeout_segundos", cfg.upload_timeout_segundos
        )
        cfg.confirmacao_timeout_segundos = sec.getint(
            "confirmacao_timeout_segundos", cfg.confirmacao_timeout_segundos
        )
        cfg.poll_lista_segundos = sec.getint("poll_lista_segundos", cfg.poll_lista_segundos)
        cfg.pausa_envio_min_segundos = sec.getint(
            "pausa_envio_min_segundos", cfg.pausa_envio_min_segundos
        )
        cfg.pausa_envio_max_segundos = sec.getint(
            "pausa_envio_max_segundos", cfg.pausa_envio_max_segundos
        )

    return cfg


def carregar_config(caminho: str | Path | None = None) -> Config:
    """Lê ``config.ini`` se existir; senão cai no ``config.example.ini``.

    Nunca falha por ausência de arquivo na Fase 1 (dry-run), apenas usa
    os padrões. Erros de conteúdo levantam :class:`ConfigInvalida`.
    """
    candidatos = []
    if caminho:
        candidatos.append(Path(caminho))
    candidatos.append(RAIZ / "config.ini")
    candidatos.append(RAIZ / "config.example.ini")

    for c in candidatos:
        if c.is_file():
            try:
                return _ler_ini(c)
            except configparser.Error as exc:
                raise ConfigInvalida(f"Erro ao ler {c}: {exc}") from exc
    return Config()


def obter_senha(senha_env: str = "ESQUEMA_SENHA_PADRAO") -> str:
    """Senha somente por variável de ambiente ou getpass. Nunca em arquivo/log."""
    senha = os.environ.get(senha_env)
    if senha:
        return senha
    prompt = "Senha padrão da plataforma (entrada oculta): " if senha_env == "ESQUEMA_SENHA_PADRAO" else "Senha de teste (entrada oculta): "
    return getpass(prompt)


def obter_email_teste() -> str:
    """E-mail da conta de teste via variável de ambiente."""
    email = os.environ.get("ESQUEMA_EMAIL_TESTE")
    if email:
        return email
    return input("E-mail da conta de teste: ")
