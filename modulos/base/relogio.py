"""Data e hora do Brasil (T44).

O site mostra a data em dd/mm/aaaa no horário de Brasília. O "hoje" do
script tem de ser o mesmo, mesmo que o relógio do PC esteja em outro fuso.
O Brasil não tem horário de verão desde 2019, então UTC-3 fixo basta (e não
depende do pacote tzdata no Windows).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

FUSO_BRASILIA = timezone(timedelta(hours=-3), "BRT")

# Perto da meia-noite o "hoje" da contagem e o da confirmação podem ser dias
# diferentes: não envia nessa janela.
MINUTOS_PERTO_DA_MEIA_NOITE = 5


def agora() -> datetime:
    return datetime.now(FUSO_BRASILIA)


def hoje() -> date:
    return agora().date()


def data_site(dia: date | None = None) -> str:
    """Data no formato da lista do site: dd/mm/aaaa."""
    return (dia or hoje()).strftime("%d/%m/%Y")


def perto_da_meia_noite(momento: datetime | None = None) -> bool:
    momento = momento or agora()
    minutos = momento.hour * 60 + momento.minute
    return minutos >= 24 * 60 - MINUTOS_PERTO_DA_MEIA_NOITE or minutos < MINUTOS_PERTO_DA_MEIA_NOITE
