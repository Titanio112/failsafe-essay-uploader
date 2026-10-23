"""Créditos e versão (T53): aparecem no menu. Para mudar o texto, mexa só aqui."""

AUTOR = "Antônio"
GITHUB = "Titanio112"
AJUDA = "com ajuda do Claude (Anthropic)"
VERSAO = "2026.10.23"


def creditos() -> str:
    """"Feito por Antônio (Titanio112) · com ajuda do Claude (Anthropic) · versão 2026.10.23"."""
    return f"Feito por {AUTOR} ({GITHUB}) · {AJUDA} · versão {VERSAO}"
