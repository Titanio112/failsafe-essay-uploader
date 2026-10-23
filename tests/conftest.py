import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def raiz_temporaria(request, tmp_path_factory, monkeypatch):
    """Nenhum teste escreve em relatorios/ ou dados/ de verdade (T36).

    Os caminhos padrão do Config (banco de progresso, relatórios, nomes e
    pastas aprovados) são calculados a partir de modulos.base.config.RAIZ na hora
    em que o Config é criado; aqui RAIZ aponta para uma pasta temporária.
    Teste que confere os caminhos reais usa ``@pytest.mark.raiz_real``
    (só lê os caminhos; não grava nada)."""
    if request.node.get_closest_marker("raiz_real"):
        return
    from modulos.base import config
    monkeypatch.setattr(config, "RAIZ", tmp_path_factory.mktemp("raiz"))


@pytest.fixture(autouse=True)
def longe_da_meia_noite(monkeypatch):
    """Os testes não dependem do relógio: rodando entre 23:55 e 00:05 a trava
    da meia-noite (T44) daria ERRO em tudo. Quem passa um horário explícito
    continua usando a função de verdade; quem quer testar a trava faz patch."""
    from modulos.base import relogio
    original = relogio.perto_da_meia_noite
    monkeypatch.setattr(relogio, "perto_da_meia_noite",
                        lambda momento=None: original(momento) if momento else False)


@pytest.fixture(autouse=True)
def log_limpo():
    """T45: o main abre logs/automacao.log; cada teste começa sem handlers
    (o arquivo do teste anterior é fechado)."""
    import logging
    yield
    logger = logging.getLogger("automacao_redacoes")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
