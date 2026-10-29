# -*- coding: utf-8 -*-
"""Testes offline da T27: identidade tolerante, "Processando arquivo",
folha em branco, código repetido no combo, análise remota e relatório
do envio. Sem navegador, sem login, sem envio."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.base.estados import EXATO_UNICO, REVISAO_MANUAL, SIMULADO
from modulos.base.excecoes import ConfirmacaoInconclusiva
from modulos.envio.fila_teste import ItemFilaTeste
from modulos.site.lista_redacoes import ItemListaRedacao
from modulos.base.excecoes import IdentidadeDivergente
from modulos.site.login import DOMINIO_ESPERADO, confirmar_identidade
from modulos.dados.planilha_arquivos import Aluno, ItemConciliacao, ResultadoConciliacao, conciliar
from modulos.base.progresso_relatorio import Progresso, ENVIADO, ERRO


# ---- Q2: identidade (M3: estrita; a T27 tolerava nome abreviado) ----

@pytest.mark.parametrize("site, lista, esperado", [
    ("ana lalara larili dos larito", "ana lalara larili dos larito", True),
    ("Ána Lalara  Larili-dos Larito", "ana lalara larili dos larito", True),  # acento/pontuação não contam
    ("ana lalara", "ana lalara larili dos larito", False),        # site abrevia (M3: planilha leva o nome do site)
    ("ana lalara larili dos larito", "ana lalara larili", False),  # lista abreviada
    ("ana", "ana lalara larili dos larito", False),             # 1 palavra só
    ("lalara larili", "ana lalara larili dos larito", False),     # 1ª palavra diferente
    ("ana lalara larisa", "ana lalara larili dos larito", False),
    ("outro usuario qualquer", "usuario testes ignorar", False),
])
def test_identidade_so_aceita_o_nome_exato(site, lista, esperado):
    pagina = MagicMock(url=f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
    pagina.locator.return_value.count.return_value = 1
    pagina.locator.return_value.first.text_content.return_value = site
    aluno = Aluno(nome=lista, email="a@example.com")
    if esperado:
        assert confirmar_identidade(pagina, aluno) is True
    else:
        with pytest.raises(IdentidadeDivergente):
            confirmar_identidade(pagina, aluno)


# ---- Q3: "Processando arquivo" no fim do prazo = recebido ----

class _Relogio:
    """time.time falso que anda 10 s por chamada."""
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 10
        return self.t


def _aguardar(situacoes: list[str], data: str | None = None):
    from datetime import datetime
    from modulos.site import confirmacao
    hoje = data or datetime.now().strftime("%d/%m/%Y")
    itens = [[ItemListaRedacao(codigo="0", tema="0- Narração", data=hoje, situacao=s)] if s else []
             for s in situacoes]
    pagina = MagicMock(url=f"https://{DOMINIO_ESPERADO}/minhas-redacoes")
    with patch.object(confirmacao, "ler_lista_redacoes", side_effect=itens + [itens[-1]] * 50), \
         patch.object(confirmacao.time, "sleep"), \
         patch.object(confirmacao.time, "time", _Relogio()):
        return confirmacao.aguardar_confirmacao(pagina, "0", timeout_segundos=40)


def test_processando_ate_o_fim_conta_como_recebido():
    assert _aguardar(["Processando arquivo"]) is True


def test_processando_depois_pendente():
    assert _aguardar(["Processando arquivo", "Pendente"]) is True


def test_sem_linha_nenhuma_continua_inconclusivo():
    with pytest.raises(ConfirmacaoInconclusiva):
        _aguardar([""])


def test_linha_de_outro_dia_nao_conta():
    with pytest.raises(ConfirmacaoInconclusiva):
        _aguardar(["Processando arquivo"], data="01/01/2020")


# ---- Q4: folha em branco nunca entra na fila ----

def test_folha_em_branco_vai_para_revisao_mesmo_aprovada():
    ana = Aluno(nome="Ana Lalara Larili", email="ana@escola.com")
    from modulos.dados.normalizacao import normalizar_nome
    aprovados = {normalizar_nome("Ana em branco"): ana}

    resultado = conciliar([ana], {"100 - Tema": ["Ana em branco.JPG", "Ana Lalara Larili.JPG"]},
                          codigos_site=set(), nomes_aprovados=aprovados)

    estados = {i.arquivo: i.estado for i in resultado.itens if i.arquivo}
    assert estados == {"Ana em branco.JPG": REVISAO_MANUAL, "Ana Lalara Larili.JPG": EXATO_UNICO}
    assert [i.arquivo for i in resultado.fila_validada()] == ["Ana Lalara Larili.JPG"]


# ---- Bug 001: código repetido no combo (0000 = dois Simulados) ----

def test_main_le_codigos_com_repetidos(tmp_path):
    from main import ler_codigos_site_csv
    caminho = tmp_path / "temas.csv"
    caminho.write_text("codigo,texto\n0000,0000 Simulado 01\n0000,0000 Simulado 02\n1,1- Carta\n",
                       encoding="utf-8")
    assert ler_codigos_site_csv(caminho) == ["0000", "0000", "1"]


def test_conciliacao_marca_codigo_repetido_como_simulado():
    ana = Aluno(nome="Ana", email="ana@escola.com")
    resultado = conciliar([ana], {"0000 - Simulado": ["Ana.JPG"]}, codigos_site=["0000", "0000", "1"])
    assert [i.estado for i in resultado.itens if i.arquivo] == [SIMULADO]
    assert resultado.fila_validada() == []


def test_envio_item_nao_clica_com_codigo_repetido_no_combo(tmp_path):
    from modulos.envio import envio_item
    prog = Progresso(tmp_path / "p.db")
    item = ItemFilaTeste("0000 - Simulado", "Ana.JPG", "0000", tmp_path / "Ana.JPG", "0000 - Simulado/Ana.JPG")
    with patch.object(envio_item, "ler_saldo_creditos", return_value=10), \
         patch.object(envio_item, "ler_lista_redacoes", return_value=[]), \
         patch.object(envio_item, "abrir_formulario_envio"), \
         patch.object(envio_item, "ler_combo_temas",
                      return_value=[("0000", "0000 Simulado 01"), ("0000", "0000 Simulado 02")]), \
         patch.object(envio_item, "selecionar_tema_por_codigo") as sel, \
         patch.object(envio_item, "clicar_enviar") as clicar:
        assert envio_item.enviar_item(MagicMock(), "ana@escola.com", item, prog) == ERRO
    assert sel.call_count == 0
    assert clicar.call_count == 0
    assert "repetido no combo" in prog.obter("ana@escola.com", "0000 - Simulado/Ana.JPG")["detalhe"]
    prog.close()


# ---- Q1: análise remota ----

def test_gravar_temas_csv_mantem_repetidos_e_faz_backup(tmp_path):
    from modulos.site.analise_remota import gravar_temas_csv
    caminho = tmp_path / "temas_site.csv"
    caminho.write_text("codigo,texto\n9,antigo\n", encoding="utf-8")

    backup = gravar_temas_csv([("0000", "Sim 01"), ("0000", "Sim 02"), ("1", "1- Carta")], caminho, "***@x.com")

    assert backup is not None and backup.read_text(encoding="utf-8") == "codigo,texto\n9,antigo\n"
    linhas = list(csv.DictReader(open(caminho, encoding="utf-8-sig")))
    assert [l["codigo"] for l in linhas] == ["0000", "0000", "1"]
    assert linhas[0]["conta_mascarada"] == "***@x.com"


@pytest.fixture
def analise_mocks():
    from modulos.site import analise_remota as ar
    with patch.object(ar, "sync_playwright") as pw, \
         patch.object(ar, "obter_email_teste", return_value="teste@x.com"), \
         patch.object(ar, "obter_senha", return_value="s"), \
         patch.object(ar, "verificar_dominio_autorizado"), \
         patch.object(ar, "login") as login, \
         patch.object(ar, "confirmar_identidade"), \
         patch.object(ar, "abrir_formulario_envio"), \
         patch.object(ar, "ler_combo_temas") as combo, \
         patch("builtins.input", return_value="ANALISAR") as entrada:
        yield {"pw": pw, "login": login, "combo": combo, "input": entrada}


def test_analise_remota_grava_o_combo(tmp_path, analise_mocks):
    from modulos.site.analise_remota import executar_analise_remota
    analise_mocks["combo"].return_value = [("0", "0- Narração"), ("100", "100- Filiação")]
    caminho = tmp_path / "temas_site.csv"

    assert executar_analise_remota(Config(), caminho) == 0

    assert [l["codigo"] for l in csv.DictReader(open(caminho, encoding="utf-8-sig"))] == ["0", "100"]


def test_analise_remota_combo_vazio_nao_mexe_no_csv(tmp_path, analise_mocks):
    from modulos.site.analise_remota import executar_analise_remota
    analise_mocks["combo"].return_value = []
    caminho = tmp_path / "temas_site.csv"
    caminho.write_text("codigo,texto\n9,antigo\n", encoding="utf-8")

    assert executar_analise_remota(Config(), caminho) == 1

    assert caminho.read_text(encoding="utf-8") == "codigo,texto\n9,antigo\n"


def test_analise_remota_sem_ANALISAR_nao_faz_login(tmp_path, analise_mocks):
    from modulos.site.analise_remota import executar_analise_remota
    analise_mocks["input"].return_value = "analisar"

    assert executar_analise_remota(Config(), tmp_path / "t.csv") == 2

    assert analise_mocks["login"].call_count == 0
    assert not (tmp_path / "t.csv").exists()


# ---- Q5: relatório do envio de produção ----

def test_relatorio_do_envio_lista_estado_final_de_cada_item(tmp_path, monkeypatch):
    from modulos.base import config as config_mod
    from modulos.envio.fluxo_envio_producao import executar_envio_producao
    monkeypatch.setattr(config_mod, "PRODUCAO_BLOQUEADA", False)  # fluxo com mocks; trava testada na T29
    cfg = Config()
    cfg.pasta_raiz = tmp_path / "pend"
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.headless, cfg.slow_mo_ms = True, 0
    ana = Aluno(nome="Ana Lalara", email="ana@escola.com", senha="s")  # M3: senha do alunos.csv
    itens = []
    for pasta in ("1 - Carta", "2 - Tema"):
        (cfg.pasta_raiz / pasta).mkdir(parents=True)
        (cfg.pasta_raiz / pasta / "Ana Lalara.JPG").write_bytes(str(cfg.pasta_raiz / pasta / "Ana Lalara.JPG").encode())
        itens.append(ItemConciliacao(pasta=pasta, arquivo="Ana Lalara.JPG", pessoa="Ana Lalara",
                                     estado=EXATO_UNICO, aluno=ana, codigo_tema=pasta[0]))
    prog = Progresso(tmp_path / "p.db")

    def enviar_falso(page, aluno_id, item, progresso):
        progresso.marcar(aluno_id, item.chave_progresso, ERRO, pasta=item.codigo, detalhe="falha simulada")
        return ERRO

    from modulos.envio import fluxo_envio_producao as fluxo
    with patch.object(fluxo, "sync_playwright"), patch("builtins.input", return_value="ENVIAR"), \
         patch.object(fluxo, "obter_senha", return_value="s"), patch.object(fluxo, "time"), \
         patch.object(fluxo, "verificar_dominio_autorizado"), patch.object(fluxo, "login"), \
         patch.object(fluxo, "confirmar_identidade"), patch.object(fluxo, "logout"), \
         patch.object(fluxo, "enviar_item", side_effect=enviar_falso):
        assert executar_envio_producao(cfg, ResultadoConciliacao(itens=itens), prog) == 1

    relatorios = list((tmp_path / "relatorios").glob("envio_*.csv"))
    assert len(relatorios) == 1
    linhas = list(csv.DictReader(open(relatorios[0], encoding="utf-8-sig"), delimiter=";"))
    assert [(l["arquivo"], l["estado"]) for l in linhas] == [
        ("1 - Carta/Ana Lalara.JPG", ERRO),        # tentado: ERRO para o aluno
        ("2 - Tema/Ana Lalara.JPG", "NAO_TENTADO"),  # não chegou a ser tentado
    ]
    assert linhas[0]["detalhe"] == "falha simulada"
    assert "an***@escola.com" == linhas[0]["email_mascarado"]
    assert ENVIADO not in {l["estado"] for l in linhas}
    prog.close()
