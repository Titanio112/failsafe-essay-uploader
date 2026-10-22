# -*- coding: utf-8 -*-
"""Testes offline da T46: combinações de opções que não valem são recusadas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.mark.parametrize("argv, mensagem", [
    (["--conta-aluno", "a@x.com"], "--conta-aluno so vale com --analise-remota"),
    (["--limite-alunos", "1"], "so valem no envio de producao"),
    (["--modo-teste", "--envio-real", "--limite-redacoes", "1"], "so valem no envio de producao"),
    (["--ensaio", "--envio-real", "--limite-redacoes", "1"], "no ensaio use --ensaio N"),
])
def test_opcao_fora_de_lugar_e_recusada(argv, mensagem, capsys):
    import main as main_mod
    assert main_mod.main(argv) == 2
    assert mensagem in capsys.readouterr().out


def test_aprovacao_antiga_cai_quando_entra_aluno_com_nome_parecido(tmp_path):
    from modulos.dados.nomes_aprovados import carregar_nomes_aprovados
    from modulos.dados.planilha_arquivos import Aluno
    ana = Aluno("Ana Lalara Souza", "ana@x.com")
    caminho = tmp_path / "nomes_aprovados.csv"
    caminho.write_text("nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo\n"
                       "Ana Lalara;Ana Lalara Souza;ana@x.com;sim;nome parcial\n", encoding="utf-8")
    assert list(carregar_nomes_aprovados(caminho, [ana]).values()) == [ana]
    nova = Aluno("Ana Lalara Lima", "lima@x.com")
    with pytest.warns(UserWarning, match="mais de um"):
        assert carregar_nomes_aprovados(caminho, [ana, nova]) == {}


@pytest.mark.parametrize("texto, saldo", [
    ("Olá! Você tem 999 crédito(s) disponíveis", 999),
    ("Você tem 1 crédito", 1),
    ("Saldo: 0 crédito(s)", 0),
    ("Cada envio usa 1 crédito por redação", None),
    ("Minhas redações", None),
])
def test_saldo_so_com_o_texto_conhecido(texto, saldo):
    from unittest.mock import MagicMock
    from modulos.site.lista_redacoes import ler_saldo_creditos
    page = MagicMock(url="https://www.esquemaredacao.com.br/minhas-redacoes")
    page.locator.return_value.inner_text.return_value = texto
    assert ler_saldo_creditos(page) == saldo
