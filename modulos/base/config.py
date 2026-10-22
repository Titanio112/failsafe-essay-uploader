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

# Raiz do projeto (este arquivo fica em modulos/base/)
RAIZ = Path(__file__).resolve().parents[2]

MENSAGEM_BLOQUEIO = "[BLOQUEADO] Envio real desativado."

# Pasta padrão das redações (T38): o Antônio guarda as redações aqui.
PASTA_REDACOES = "Redações plataforma"
RAIZ_PASTA_REDACOES_LEIAME = """# 📂 Redações para enviar

Coloque aqui as redações que o script vai enviar para a plataforma.

## Como organizar

```
Redações plataforma/
├── 100 - Impactos da invisibilidade da filiação/
│   ├── Ana Lalara Larili.JPG
│   └── Bruno Silva.JPG
└── 3B - Efeitos da aporofobia/
    ├── Ana Lalara Larili.JPG
    └── Cecília em branco.JPG
```

| O quê | Regra |
|---|---|
| **Subpasta** | Uma por tema. Se começar com o código do tema do site (`100 - ...`), o script já sabe o tema. |
| **Pasta sem código** | Rode `python main.py --revisar` e escolha o tema (ou `g` = tema genérico 000, quando o tema não existe no site). |
| **Arquivo** | Um JPG por aluno, com o **nome do aluno**. Nome curto ou com erro: a revisão pergunta quem é. |
| **Folha sem redação** | Coloque `em branco` no nome. Ela nunca é enviada. |

## Depois de colocar as redações

1. `python main.py` — confere tudo, sem enviar nada.
2. `python main.py --revisar` — escolhe temas e confirma nomes.
3. `python main.py` de novo — confere a fila.
"""

# Regra do Antônio (22/10/2026): por enquanto NENHUMA redação é enviada nas
# contas dos alunos de verdade. Só o modo teste (conta de teste) envia.
# Liberar = trocar para False, só com ordem expressa do Antônio.
PRODUCAO_BLOQUEADA = True
MENSAGEM_PRODUCAO_BLOQUEADA = (
    "[BLOQUEADO] Envio para alunos reais desativado por decisao do Antonio (22/10).\n"
    "[BLOQUEADO] So o modo teste envia (--modo-teste --envio-real). Nada foi enviado."
)


class EnvioBloqueado(RuntimeError):
    """Levantada quando uma ação de envio real é tentada sem autorização."""


def exigir_envio_real(envio_real: bool) -> None:
    """Trava antiga (F1), mantida pelo teste protegido. As travas de verdade
    são a confirmação digitada e PRODUCAO_BLOQUEADA (main e fluxo)."""
    if not envio_real:
        raise EnvioBloqueado(MENSAGEM_BLOQUEIO)


class ConfigInvalida(RuntimeError):
    """Configuração ausente ou inconsistente."""


@dataclass
class Config:
    headless: bool = False
    slow_mo_ms: int = 500

    pasta_raiz: Path = field(default_factory=lambda: RAIZ / PASTA_REDACOES)
    planilha: Path = field(default_factory=Path)
    extensoes: tuple[str, ...] = (".jpg", ".jpeg")

    aba_planilha: str = "Planilha1"
    coluna_nome: str = "nome"
    coluna_email: str = "email"

    limiar_fuzzy: float = 95.0
    margem_minima: float = 8.0

    pausa_envio_min_segundos: int = 8
    pausa_envio_max_segundos: int = 15

    banco_progresso: Path = field(default_factory=lambda: RAIZ / "relatorios" / "progresso.db")
    pasta_relatorios: Path = field(default_factory=lambda: RAIZ / "relatorios")
    # Nomes de arquivo aprovados por humano -> aluno (T26)
    arquivo_nomes_aprovados: Path = field(default_factory=lambda: RAIZ / "dados" / "nomes_aprovados.csv")
    # Código de tema aprovado por humano para pasta sem código (T28)
    arquivo_pastas_aprovadas: Path = field(default_factory=lambda: RAIZ / "dados" / "pastas_aprovadas.csv")

    def __post_init__(self) -> None:
        if not self.planilha or str(self.planilha) == ".":
            # Lista de alunos (T26): CSV em dados/ com Nome;Email (Senha é ignorada)
            self.planilha = RAIZ / "dados" / "dados_alunos.csv"


def _ler_ini(caminho: Path) -> Config:
    cfg = Config()
    parser = configparser.ConfigParser()
    parser.read(caminho, encoding="utf-8")

    if parser.has_section("plataforma"):
        sec = parser["plataforma"]
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

    if parser.has_section("conciliacao"):
        sec = parser["conciliacao"]
        cfg.limiar_fuzzy = sec.getfloat("limiar_fuzzy", cfg.limiar_fuzzy)
        cfg.margem_minima = sec.getfloat("margem_minima", cfg.margem_minima)

    if parser.has_section("esperas"):
        sec = parser["esperas"]
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
