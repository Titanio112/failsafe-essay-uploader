# -*- coding: utf-8 -*-
"""Testes offline da lista /minhas-redacoes no layout real (T18E).

Layout observado em 21/10/2026: Data | Tema | Nota | Situação | (botão),
data sem hora. Sem navegador, sem login, sem envio.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.site.login import DOMINIO_ESPERADO
from modulos.site.lista_redacoes import (
    ItemListaRedacao,
    contar_tema_hoje,
    ler_lista_redacoes,
    ler_lista_redacoes_html,
)


def _html_lista(linhas: str, cabecalho=("Data", "Tema", "Nota", "Situação", "")) -> str:
    ths = "".join(f"<th>{c}</th>" for c in cabecalho)
    return f"""
    <p>Você tem <strong>998 crédito(s)</strong>.</p>
    <table class="table table-bordered">
      <tbody><tr>{ths}</tr>
      {linhas}
      </tbody>
    </table>
    """


LINHA_REAL = (
    "<tr><td>21/10/2026</td><td>0- Narração</td><td>0.0</td>"
    "<td>Pendente</td><td><a>Aguarde a correção</a></td></tr>"
)


class PaginaFalsa:
    """Imita o mínimo de Page usado por ler_lista_redacoes."""

    def __init__(self, html: str):
        self.url = f"https://{DOMINIO_ESPERADO}/minhas-redacoes"
        self._html = html

    def goto(self, url, wait_until=None):
        self.url = url

    def wait_for_load_state(self, estado):
        pass

    def content(self):
        return self._html


# ---- E2: colunas no layout real ----

def test_layout_real_le_data_na_primeira_coluna():
    itens = ler_lista_redacoes_html(_html_lista(LINHA_REAL))
    assert len(itens) == 1
    assert itens[0].data == "21/10/2026"
    assert itens[0].tema == "0- Narração"
    assert itens[0].codigo == "0"
    assert itens[0].nota == "0.0"
    assert itens[0].situacao == "Pendente"


def test_ler_lista_redacoes_da_pagina_usa_layout_real():
    itens = ler_lista_redacoes(PaginaFalsa(_html_lista(LINHA_REAL)))
    assert [(i.data, i.codigo, i.situacao) for i in itens] == [
        ("21/10/2026", "0", "Pendente")
    ]


def test_envio_do_dia_detectado_como_ja_enviado():
    """Era o risco da T20: o envio de hoje precisa ser visto como duplicado."""
    itens = ler_lista_redacoes(PaginaFalsa(_html_lista(LINHA_REAL)))
    assert contar_tema_hoje(itens, "0", data_hoje="21/10/2026") == 1
    # "00" é outro código: não é duplicado
    assert contar_tema_hoje(itens, "00", data_hoje="21/10/2026") == 0
    # Outro dia: pode enviar
    assert contar_tema_hoje(itens, "0", data_hoje="22/10/2026") == 0


# ---- Lista ilegível -> fail-closed ----

def test_cabecalho_diferente_levanta():
    html = _html_lista(
        "<tr><td>21/10/2026 18:38</td><td>ENEM</td><td>0- Narração</td><td>Pendente</td></tr>",
        cabecalho=("Data do envio", "Pasta", "Proposta", "Status", ""),
    )
    with pytest.raises(RuntimeError, match="Cabecalho inesperado"):
        ler_lista_redacoes_html(html)


def test_linhas_de_dados_ilegiveis_levanta():
    html = _html_lista("<tr><td colspan='5'>???</td></tr>")
    with pytest.raises(RuntimeError, match="nao puderam ser lidas"):
        ler_lista_redacoes_html(html)


def test_detectar_lista_com_itens_sem_dados_levanta():
    lista = [ItemListaRedacao(data="", tema="", situacao="Pendente")]
    with pytest.raises(RuntimeError, match="ilegivel"):
        contar_tema_hoje(lista, "0", data_hoje="21/10/2026")


# ---- D1 opção (a): lista vazia pode enviar ----

def test_tabela_so_com_cabecalho_e_lista_vazia():
    assert ler_lista_redacoes_html(_html_lista("")) == []


def test_detectar_lista_vazia_pode_enviar():
    assert contar_tema_hoje([], "0", data_hoje="21/10/2026") == 0


# ---- E1: confirmacao importa e usa a lista real ----

def test_aguardar_confirmacao_acha_pendente_de_hoje():
    from modulos.site import confirmacao

    hoje = datetime.now().strftime("%d/%m/%Y")
    linha = LINHA_REAL.replace("21/10/2026", hoje)
    pagina = PaginaFalsa(_html_lista(linha))
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(pagina, "0", timeout_segundos=5) is True
