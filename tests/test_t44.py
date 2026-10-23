# -*- coding: utf-8 -*-
"""Testes offline da T44: segurança do envio (critério conferido, CAPTCHA
para tudo, confirmação só da linha nova, lista achada pelo cabeçalho, mesma
foto não volta, fuso de Brasília, um envio por vez, domínio exato,
identidade exata na conta de teste). Sem navegador."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import relogio
from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.base.excecoes import CaptchaOuBloqueio, IdentidadeDivergente
from modulos.base.progresso_relatorio import (
    ENVIADO, ENVIANDO, ERRO, REVISAO_MANUAL, Progresso, _FiltroSanitizador,
)
from modulos.base.trava import TravaOcupada, trava_de_envio
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import envio_item
from modulos.envio import fluxo_envio_producao as fep
from modulos.envio.fila_producao import montar_lote_producao
from modulos.envio.fila_teste import ItemFilaTeste, hash_do_arquivo
from modulos.site import confirmacao, formulario_envio, login
from modulos.site.lista_redacoes import ler_lista_redacoes_html
from tests.test_lista_redacoes_layout_real import PaginaFalsa, _html_lista

ANA = Aluno(nome="ANA LALARA LARILI DOS LARITO", email="ana@escola.com")
BIA = Aluno(nome="BEATRIZ LANETO", email="bia@escola.com")
ARQ = "ANA LALARA LARILI DOS LARITO.JPG"


# ─── Critério ENEM conferido ─────────────────────────────────

def _pagina_criterio(marcado=None, timeout=False):
    from playwright.sync_api import TimeoutError as PWTimeoutError
    page = MagicMock()
    if timeout:
        page.select_option.side_effect = PWTimeoutError("sem select")
    page.locator.return_value.first.get_attribute.return_value = marcado
    return page


@pytest.mark.parametrize("marcado, timeout, esperado", [
    ("1", False, True), ("3", False, False), (None, False, False), ("1", True, False)])
def test_criterio_so_passa_com_enem_marcado(marcado, timeout, esperado):
    assert formulario_envio.selecionar_criterio(_pagina_criterio(marcado, timeout)) is esperado


@pytest.fixture
def envio(tmp_path):
    prog = Progresso(tmp_path / "p.db")
    pagina = MagicMock()
    pagina.locator.return_value.first.inner_text.return_value = "000- DISSERTATIVO"
    with patch.object(envio_item, "ler_saldo_creditos", autospec=True, return_value=10), \
         patch.object(envio_item, "ler_lista_redacoes", autospec=True, return_value=[]) as lista, \
         patch.object(envio_item, "abrir_formulario_envio", autospec=True), \
         patch.object(envio_item, "ler_combo_temas", autospec=True, return_value=[("000", "000- DISSERTATIVO")]), \
         patch.object(envio_item, "selecionar_tema_por_codigo", autospec=True, return_value=True), \
         patch.object(envio_item, "selecionar_criterio", autospec=True, return_value=True) as criterio, \
         patch.object(envio_item, "anexar_arquivo", autospec=True), \
         patch.object(envio_item, "aguardar_upload_aceito", autospec=True, return_value=True), \
         patch.object(envio_item, "clicar_enviar", autospec=True) as clicar, \
         patch.object(envio_item, "aguardar_confirmacao", autospec=True, return_value=True) as confirma, \
         patch.object(envio_item.relogio, "perto_da_meia_noite", return_value=False) as meia_noite:
        yield {"prog": prog, "page": pagina, "lista": lista, "criterio": criterio, "clicar": clicar,
               "confirma": confirma, "meia_noite": meia_noite}
    prog.close()


def _item(h="abc"):
    return ItemFilaTeste("000 - T", ARQ, "000", Path("x"), f"000 - T/{ARQ}", hash_arquivo=h)


def _enviar(envio, item=None):
    return envio_item.enviar_item(envio["page"], ANA.id, item or _item(), envio["prog"])


def test_criterio_nao_conferido_e_erro_sem_clique(envio):
    envio["criterio"].return_value = False
    assert _enviar(envio) == ERRO
    assert envio["clicar"].call_count == 0
    assert envio["prog"].obter(ANA.id, f"000 - T/{ARQ}")["detalhe"] == "Criterio ENEM nao conferido"


def test_enviando_e_gravado_antes_do_clique(envio):
    estados_no_clique = []
    envio["clicar"].side_effect = lambda page: estados_no_clique.append(
        envio["prog"].obter(ANA.id, f"000 - T/{ARQ}")["estado"])
    assert _enviar(envio) == ENVIADO
    assert estados_no_clique == [ENVIANDO]


def test_perto_da_meia_noite_nao_envia(envio):
    envio["meia_noite"].return_value = True
    assert _enviar(envio) == ERRO
    assert envio["clicar"].call_count == 0


def test_confirmacao_recebe_o_dia_e_as_linhas_de_antes(envio):
    from modulos.site.lista_redacoes import ItemListaRedacao
    hoje = relogio.data_site()
    envio["lista"].return_value = [ItemListaRedacao("000", "000- D", hoje, "Corrigida")]
    item = _item()
    item.total_mesmo_tema = 2
    envio["prog"].marcar(ANA.id, "outra/1.JPG", ENVIADO, pasta="000")  # caderno: 1 hoje
    assert _enviar(envio, item) == ENVIADO
    kwargs = envio["confirma"].call_args.kwargs
    assert kwargs["antes"] == ["corrigida"] and kwargs["data_hoje"] == hoje
    assert kwargs["linhas_esperadas"] == 2


def test_hash_fica_gravado_e_nao_some_quando_marca_sem_hash(envio):
    assert _enviar(envio, _item("h1")) == ENVIADO
    envio["prog"].marcar(ANA.id, f"000 - T/{ARQ}", ENVIADO, pasta="000")  # sem hash
    assert envio["prog"].registro_do_conteudo(ANA.id, "h1", "outro") == {
        "arquivo": f"000 - T/{ARQ}", "estado": ENVIADO}


@pytest.mark.parametrize("clicou", [False, True])
def test_captcha_grava_estado_e_sobe(envio, clicou):
    alvo = "clicar" if clicou else "lista"
    envio[alvo].side_effect = CaptchaOuBloqueio("captcha")
    with pytest.raises(CaptchaOuBloqueio) as erro:
        _enviar(envio)
    assert erro.value.estado == (REVISAO_MANUAL if clicou else ERRO)


# ─── CAPTCHA no meio do lote para a execução inteira ─────────

def test_captcha_num_item_para_tudo_e_nao_abre_o_proximo_aluno(tmp_path):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    arquivos = {"100 - T": [f"{ANA.nome}.JPG", f"{BIA.nome}.JPG"]}
    (tmp_path / "100 - T").mkdir()
    for nome in arquivos["100 - T"]:
        (tmp_path / "100 - T" / nome).write_bytes(nome.encode())
    resultado = conciliar([ANA, BIA], arquivos, codigos_site=["100"])

    def enviar(page, aluno_id, item, progresso=None):
        erro = CaptchaOuBloqueio("captcha")
        erro.estado = ERRO
        raise erro

    with patch("modulos.base.config.PRODUCAO_BLOQUEADA", False), \
         patch.object(fep, "sync_playwright"), patch.object(fep, "obter_senha", return_value="s"), \
         patch.object(fep, "verificar_dominio_autorizado"), patch.object(fep, "login") as fazer_login, \
         patch.object(fep, "confirmar_identidade"), patch.object(fep, "logout"), \
         patch.object(fep, "enviar_item", side_effect=enviar), \
         patch("builtins.input", return_value="ENVIAR"):
        assert fep.executar_envio_producao(cfg, resultado) == 1
    assert fazer_login.call_count == 1  # o 2º aluno nem chegou a logar


# ─── Confirmação: só a linha nova ────────────────────────────

def _pagina(*situacoes):
    hoje = relogio.data_site()
    linhas = "".join(f"<tr><td>{hoje}</td><td>000- DISSERTATIVO</td><td>0.0</td><td>{s}</td>"
                     f"<td><a>x</a></td></tr>" for s in situacoes)
    return PaginaFalsa(_html_lista(linhas))


def test_redacao_anterior_corrigida_nao_impede_confirmar_a_nova():
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(
            _pagina("Corrigida", "Pendente"), "000", timeout_segundos=5,
            linhas_esperadas=2, antes=["corrigida"]) is True


def test_erro_antigo_nao_vira_falso_erro_e_erro_novo_vira():
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(
            _pagina("Erro no arquivo", "Pendente"), "000", timeout_segundos=5,
            linhas_esperadas=2, antes=["erro no arquivo"]) is True
        assert confirmacao.aguardar_confirmacao(
            _pagina("Pendente", "Erro no arquivo"), "000", timeout_segundos=5,
            linhas_esperadas=2, antes=["pendente"]) is False


def test_captcha_na_espera_da_confirmacao_sobe_na_hora():
    pagina = _pagina("Pendente")
    with patch("modulos.site.confirmacao.verificar_dominio_autorizado",
               side_effect=CaptchaOuBloqueio("outro dominio")), \
         patch("modulos.site.confirmacao.time.sleep") as dormir:
        with pytest.raises(CaptchaOuBloqueio):
            confirmacao.aguardar_confirmacao(pagina, "000", timeout_segundos=60)
    assert dormir.call_count == 0


# ─── Lista: tabela pelo cabeçalho, paginação ─────────────────

_TABELA_LISTA = ("<table><thead><tr><th>Data</th><th>Tema</th><th>Nota</th><th>Situação</th><th></th></tr></thead>"
                 "<tbody><tr><td>22/10/2026</td><td>000- D</td><td></td><td>Pendente</td><td></td></tr></tbody></table>")


def test_lista_acha_a_tabela_certa_mesmo_com_outra_antes():
    outra = "<table><tr><th>Plano</th><th>Valor</th></tr><tr><td>a</td><td>b</td></tr></table>"
    itens = ler_lista_redacoes_html(f"<html>{outra}{_TABELA_LISTA}</html>")
    assert [(i.codigo, i.situacao) for i in itens] == [("000", "Pendente")]


def test_lista_so_com_outra_tabela_e_ilegivel():
    with pytest.raises(RuntimeError, match="Cabecalho inesperado"):
        ler_lista_redacoes_html("<table><tr><th>Plano</th><th>Valor</th></tr></table>")


def test_lista_paginada_bloqueia():
    with pytest.raises(RuntimeError, match="paginacao"):
        ler_lista_redacoes_html(f"<html>{_TABELA_LISTA}<ul class='pagination'><li>2</li></ul></html>")


# ─── Mesma foto ──────────────────────────────────────────────

def test_mesma_foto_em_duas_pastas_entra_uma_vez(tmp_path):
    for pasta in ("3B - A", "3B - B"):
        (tmp_path / pasta).mkdir()
        (tmp_path / pasta / ARQ).write_bytes(b"mesma foto")
    resultado = conciliar([ANA], {"3B - A": [ARQ], "3B - B": [ARQ]}, codigos_site=["000"],
                          codigos_pasta={"3B - A": "000", "3B - B": "000"})
    lotes, ignorados = montar_lote_producao(resultado, tmp_path)
    assert [i.pasta for i in lotes[0].itens] == ["3B - A"]
    assert ignorados == [(f"3B - B/{ARQ}", f"mesma foto que 3B - A/{ARQ} (copia? revisao manual)")]


def test_foto_ja_enviada_com_outro_nome_nao_volta(tmp_path):
    (tmp_path / "100 - T").mkdir()
    (tmp_path / "100 - T" / ARQ).write_bytes(b"foto da ana")
    resultado = conciliar([ANA], {"100 - T": [ARQ]}, codigos_site=["100"])
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ANA.id, "100 - T/Ana.JPG", ENVIADO, pasta="100",
                    hash_arquivo=hash_do_arquivo(tmp_path / "100 - T" / ARQ))
        lotes, ignorados = montar_lote_producao(resultado, tmp_path, prog)
    assert lotes == []
    assert "ja registrada como ENVIADO em 100 - T/Ana.JPG" in ignorados[0][1]


# ─── Retomada ────────────────────────────────────────────────

def test_retomada_de_enviando_vira_revisao_e_fica_fora_do_lote(tmp_path):
    (tmp_path / "100 - T").mkdir()
    (tmp_path / "100 - T" / ARQ).write_bytes(b"foto")
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ANA.id, f"100 - T/{ARQ}", ENVIANDO, pasta="100")
    with Progresso(tmp_path / "p.db") as prog:  # programa caiu e voltou
        registro = prog.obter(ANA.id, f"100 - T/{ARQ}")
        assert registro["estado"] == REVISAO_MANUAL and "retomada" in registro["detalhe"]
        resultado = conciliar([ANA], {"100 - T": [ARQ]}, codigos_site=["100"])
        lotes, ignorados = montar_lote_producao(resultado, tmp_path, prog)
    assert lotes == [] and "REVISAO_MANUAL" in ignorados[0][1]


# ─── Fuso de Brasília ────────────────────────────────────────

def test_perto_da_meia_noite():
    def br(h, m):
        return datetime(2026, 10, 22, h, m, tzinfo=relogio.FUSO_BRASILIA)
    assert relogio.perto_da_meia_noite(br(23, 56)) and relogio.perto_da_meia_noite(br(0, 3))
    assert not relogio.perto_da_meia_noite(br(23, 54)) and not relogio.perto_da_meia_noite(br(12, 0))


def test_caderno_usa_o_dia_de_brasilia(tmp_path):
    """01:30 UTC de amanhã ainda é hoje em Brasília (22:30)."""
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar(ANA.id, "a/1.JPG", ENVIADO, pasta="000")
        momento = datetime(2026, 10, 23, 1, 30, tzinfo=timezone.utc)
        prog.con.execute("UPDATE progresso SET atualizado_em = ?", (momento.isoformat(),))
        with patch.object(relogio, "hoje", return_value=datetime(2026, 10, 22).date()):
            assert prog.enviados_hoje(ANA.id, "000") == 1


# ─── Um envio por vez ────────────────────────────────────────

def test_segundo_envio_ao_mesmo_tempo_e_recusado(tmp_path):
    with trava_de_envio(tmp_path / "envio.trava"):
        with pytest.raises(TravaOcupada):
            with trava_de_envio(tmp_path / "envio.trava"):
                pass
    with trava_de_envio(tmp_path / "envio.trava"):  # solta no fim
        pass


def test_fluxo_com_trava_ocupada_nao_abre_o_navegador(tmp_path, capsys):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    teste = Aluno(NOME_CONTA_TESTE, "teste@teste.com")
    (tmp_path / "100 - T").mkdir()
    (tmp_path / "100 - T" / f"{teste.nome}.jpg").write_bytes(b"f")
    resultado = conciliar([teste], {"100 - T": [f"{teste.nome}.jpg"]}, codigos_site=["100"])
    with trava_de_envio(cfg.pasta_relatorios / "envio.trava"), \
         patch.object(fep, "sync_playwright") as pw, patch("builtins.input", return_value="ENVIAR TESTE"):
        assert fep.executar_envio_producao(cfg, resultado, conta_teste=teste.email) == 2
    assert pw.call_count == 0
    assert "Outro envio está rodando" in capsys.readouterr().out


# ─── Domínio e identidade ────────────────────────────────────

@pytest.mark.parametrize("url", ["https://www.esquemaredacao.com.br.evil.tld/x",
                                 "https://esquemaredacao.com.br/x", "about:blank"])
def test_dominio_tem_de_ser_exato(url):
    with pytest.raises(CaptchaOuBloqueio):
        login.verificar_dominio_autorizado(MagicMock(url=url))
    login.verificar_dominio_autorizado(MagicMock(url="https://www.esquemaredacao.com.br/minhas-redacoes"))


def _pagina_menu(texto):
    page = MagicMock(url="https://www.esquemaredacao.com.br/minhas-redacoes")
    page.locator.return_value.first.text_content.return_value = texto
    return page


def test_conta_de_teste_exige_nome_igual():
    conta = Aluno(NOME_CONTA_TESTE, "teste@teste.com")
    assert login.confirmar_identidade(_pagina_menu("Usuario Testes Ignorar "), conta, exato=True)
    with pytest.raises(IdentidadeDivergente):
        login.confirmar_identidade(_pagina_menu("Usuario Testes"), conta, exato=True)
    # aluno: nome abreviado no site continua aceito (T27)
    assert login.confirmar_identidade(_pagina_menu("Ana Lalara"), ANA)


def test_modo_teste_recusa_email_de_aluno(tmp_path, capsys):
    from modulos.envio.fluxo_envio_teste import executar_envio_teste
    cfg = Config()
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text(f"Nome;Email\n{ANA.nome};{ANA.email}\n", encoding="utf-8")
    with patch("modulos.envio.fluxo_envio_teste.obter_email_teste", return_value=" ANA@escola.com "), \
         patch("modulos.envio.fluxo_envio_teste.executar_envio_producao") as fluxo:
        assert executar_envio_teste(cfg) == 2
    assert fluxo.call_count == 0
    assert "e-mail de um aluno da lista" in capsys.readouterr().out


# ─── Log ─────────────────────────────────────────────────────

def test_traceback_com_segredo_nao_vai_para_o_log():
    try:
        raise ValueError("password=abc123")
    except ValueError:
        registro = logging.LogRecord("x", logging.ERROR, __file__, 1, "Erro inesperado", (), sys.exc_info())
    _FiltroSanitizador().filter(registro)
    assert registro.exc_info is None and "traceback suprimido" in registro.msg


def test_clique_espera_sair_do_formulario_e_nao_trava_se_nao_sair():
    from playwright.sync_api import TimeoutError as PWTimeoutError
    page = MagicMock()
    confirmacao.clicar_enviar(page)
    page.locator.return_value.first.click.assert_called_once_with()
    espera = page.wait_for_url.call_args
    assert espera.kwargs["timeout"] == 30000
    assert espera.args[0]("https://www.esquemaredacao.com.br/minhas-redacoes") is True
    assert espera.args[0]("https://www.esquemaredacao.com.br/wordings/new") is False

    page.wait_for_url.side_effect = PWTimeoutError("ficou no formulario")
    confirmacao.clicar_enviar(page)  # não levanta: a lista decide
    assert page.locator.return_value.first.click.call_count == 2  # um clique por chamada, sem retry
