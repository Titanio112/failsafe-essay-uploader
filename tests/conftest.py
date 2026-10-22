import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def raiz_temporaria(request, tmp_path_factory, monkeypatch):
    """Nenhum teste escreve em relatorios/ ou dados/ de verdade (T36).

    Os caminhos padrão do Config (banco de progresso, relatórios, nomes e
    pastas aprovados) são calculados a partir de modulos.config.RAIZ na hora
    em que o Config é criado; aqui RAIZ aponta para uma pasta temporária.
    Teste que confere os caminhos reais usa ``@pytest.mark.raiz_real``
    (só lê os caminhos; não grava nada)."""
    if request.node.get_closest_marker("raiz_real"):
        return
    from modulos import config
    monkeypatch.setattr(config, "RAIZ", tmp_path_factory.mktemp("raiz"))
