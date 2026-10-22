# -*- coding: utf-8 -*-
"""Testes offline da T35: várias redações do mesmo tema (ex.: genérico 000)
no mesmo dia, conferidas por CONTAGEM (site x caderno). Sem navegador."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.estados import EXATO_UNICO, REVISAO_MANUAL
from modulos.fila_producao import montar_lote_producao
from modulos.fila_teste import ItemFilaTeste
from modulos.lista_redacoes import ItemListaRedacao, contar_tema_hoje
from modulos.planilha_arquivos import Aluno, conciliar
from modulos.progresso_relatorio import ENVIADO, ERRO, JA_ENVIADO, Progresso
from tests.test_lista_redacoes_layout_real import PaginaFalsa, _html_lista

ANA = Aluno(nome="ANA LALARA LARILI DOS LARITO", email="ana@escola.com")
ARQ = "ANA LALARA LARILI DOS LARITO.JPG"
HOJE = "22/10/2026"


def _linha(codigo, data=HOJE, situacao="Pendente"):
    return ItemListaRedacao(codigo=codigo, tema=f"{codigo}- Tema", data=data, situacao=situacao)


# ─── Conciliação e lote ──────────────────────────────────────

def test_mesmo_tema_em_pastas_diferentes_entra_na_fila():
    resultado = conciliar([ANA], {"3B - Aporofobia": [ARQ], "3B - Discriminacao": [ARQ]},
                          codigos_site=["000"],
                          codigos_pasta={"3B - Aporofobia": "000", "3B - Discriminacao": "000"})
    assert [i.estado for i in resultado.itens if i.arquivo] == [EXATO_UNICO, EXATO_UNICO]


def test_mesmo_tema_na_mesma_pasta_continua_revisao_manual():
    resultado = conciliar([ANA], {"000 - Tema": [ARQ, "ANA LALARA LARILI DOS LARITO - Red2.JPG"]},
                          codigos_site=["000"])
    assert {i.estado for i in resultado.itens if i.arquivo} == {REVISAO_MANUAL}


def test_lote_leva_os_dois_com_total_do_tema(tmp_path):
    for pasta in ("3B - Aporofobia", "3B - Discriminacao"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / ARQ).write_bytes(b"x")
    resultado = conciliar([ANA], {"3B - Aporofobia": [ARQ], "3B - Discriminacao": [ARQ]},
                          codigos_site=["000"],
                          codigos_pasta={"3B - Aporofobia": "000", "3B - Discriminacao": "000"})
    lotes, ignorados = montar_lote_producao(resultado, tmp_path)
    assert ignorados == []
    assert [(i.codigo, i.total_mesmo_tema) for i in lotes[0].itens] == [("000", 2), ("000", 2)]


# ─── Contagens ───────────────────────────────────────────────

def test_contar_tema_hoje_ignora_outro_dia_outro_tema_e_cancelada():
    lista = [_linha("000"), _linha("000"), _linha("000", data="21/10/2026"),
             _linha("100"), _linha("000", situacao="Cancelada")]
    assert contar_tema_hoje(lista, "000", data_hoje=HOJE) == 2
    assert contar_tema_hoje([], "000", data_hoje=HOJE) == 0


def test_contar_tema_hoje_lista_ilegivel_bloqueia():
    with pytest.raises(RuntimeError):
        contar_tema_hoje([ItemListaRedacao()], "000", data_hoje=HOJE)


def test_caderno_conta_so_os_de_hoje_deste_tema(tmp_path):
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ANA.id, "a/1.JPG", ENVIADO, pasta="000")
        prog.marcar(ANA.id, "b/1.JPG", JA_ENVIADO, pasta="000")
        prog.marcar(ANA.id, "c/1.JPG", ERRO, pasta="000")
        prog.marcar(ANA.id, "d/1.JPG", ENVIADO, pasta="100")
        prog.marcar(ANA.id, "e/1.JPG", ENVIADO, pasta="000")
        ontem = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
        prog.con.execute("UPDATE progresso SET atualizado_em = ? WHERE arquivo = 'e/1.JPG'", (ontem,))
        assert prog.enviados_hoje(ANA.id, "000") == 2


# ─── Decisão do envio ────────────────────────────────────────

@pytest.fixture
def envio(tmp_path):
    from modulos import envio_item
    prog = Progresso(tmp_path / "p.db")
    pagina = MagicMock()
    pagina.locator.return_value.first.inner_text.return_value = "000- DISSERTATIVO ARGUMENTATIVO"
    with patch.object(envio_item, "ler_saldo_creditos", return_value=10), \
         patch.object(envio_item, "ler_lista_redacoes", return_value=[]), \
         patch.object(envio_item, "contar_tema_hoje") as no_site, \
         patch.object(envio_item, "abrir_formulario_envio"), \
         patch.object(envio_item, "ler_combo_temas", return_value=[("000", "000- DISSERTATIVO")]), \
         patch.object(envio_item, "selecionar_tema_por_codigo", return_value=True), \
         patch.object(envio_item, "selecionar_criterio"), \
         patch.object(envio_item, "anexar_arquivo"), \
         patch.object(envio_item, "aguardar_upload_aceito", return_value=True), \
         patch.object(envio_item, "clicar_enviar") as clicar, \
         patch.object(envio_item, "aguardar_confirmacao", return_value=True) as confirma:
        yield {"mod": envio_item, "prog": prog, "page": pagina, "no_site": no_site,
               "clicar": clicar, "confirma": confirma}
    prog.close()


def _enviar(envio, pasta, total=2):
    item = ItemFilaTeste(pasta, ARQ, "000", Path(pasta) / ARQ, f"{pasta}/{ARQ}", total_mesmo_tema=total)
    return envio["mod"].enviar_item(envio["page"], ANA.id, item, envio["prog"])


def test_duas_redacoes_do_mesmo_tema_no_mesmo_dia(envio):
    """Ana: 2 redações no 000. Site 0 -> envia (espera 1); site 1 e caderno 1 -> envia (espera 2)."""
    envio["no_site"].return_value = 0
    assert _enviar(envio, "3B - Aporofobia") == ENVIADO
    assert envio["confirma"].call_args.kwargs["linhas_esperadas"] == 1

    envio["no_site"].return_value = 1
    assert _enviar(envio, "3B - Discriminacao") == ENVIADO
    assert envio["confirma"].call_args.kwargs["linhas_esperadas"] == 2
    assert envio["clicar"].call_count == 2


def test_site_ja_tem_todas_pula_sem_clicar(envio):
    envio["no_site"].return_value = 2
    assert _enviar(envio, "3B - Aporofobia") == JA_ENVIADO
    assert envio["clicar"].call_count == 0


def test_site_com_mais_que_o_caderno_nao_clica(envio):
    """Site tem 1 hoje, caderno 0, e são 2 redações: alguém enviou à mão ou o
    caderno se perdeu -> ERRO, sem clique, sem marcar como enviada."""
    envio["no_site"].return_value = 1
    assert _enviar(envio, "3B - Aporofobia") == ERRO
    assert envio["clicar"].call_count == 0
    assert "Contagem diverge" in envio["prog"].obter(ANA.id, f"3B - Aporofobia/{ARQ}")["detalhe"]


def test_tema_com_uma_redacao_mantem_a_regra_antiga(envio):
    """1 arquivo no tema e o site já tem esse tema hoje -> já enviado (regra de 21/10)."""
    envio["no_site"].return_value = 1
    assert _enviar(envio, "3B - Filiacao", total=1) == JA_ENVIADO
    assert envio["clicar"].call_count == 0


# ─── Confirmação ─────────────────────────────────────────────

def _pagina(*situacoes):
    hoje = datetime.now().strftime("%d/%m/%Y")
    linhas = "".join(f"<tr><td>{hoje}</td><td>000- DISSERTATIVO</td><td>0.0</td><td>{s}</td>"
                     f"<td><a>x</a></td></tr>" for s in situacoes)
    return PaginaFalsa(_html_lista(linhas))


def test_confirmacao_espera_a_linha_nova_e_nao_aceita_a_antiga():
    from modulos import confirmacao
    from modulos.excecoes import ConfirmacaoInconclusiva
    with patch("modulos.confirmacao.time.sleep"):
        # só a linha da 1ª redação: a 2ª ainda não chegou -> inconclusivo
        with pytest.raises(ConfirmacaoInconclusiva):
            confirmacao.aguardar_confirmacao(_pagina("Pendente"), "000", timeout_segundos=0.05,
                                             linhas_esperadas=2)
        assert confirmacao.aguardar_confirmacao(_pagina("Pendente", "Pendente"), "000",
                                                timeout_segundos=5, linhas_esperadas=2) is True
