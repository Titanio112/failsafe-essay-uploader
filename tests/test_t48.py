# -*- coding: utf-8 -*-
"""Testes offline da T48 (achados da 2ª varredura). Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import NOME_CONTA_TESTE, Config
from modulos.base.excecoes import BotaoEnviarAusente, LoginFalhou
from modulos.base.progresso_relatorio import ENVIADO, ERRO, Progresso
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.envio import envio_item
from modulos.envio import fluxo_envio_producao as fep
from modulos.envio.fila_teste import ItemFilaTeste
from modulos.site import confirmacao
from modulos.site.lista_redacoes import ler_lista_redacoes
from tests.test_lista_redacoes_layout_real import LINHA_REAL, PaginaFalsa, _html_lista

ANA = Aluno("Ana Souza", "ana@x.com")


# ─── Lista: só a página certa conta ──────────────────────────

class _Resposta:
    def __init__(self, status):
        self.status = status


@pytest.mark.parametrize("html, status, caminho", [
    ("<h1>502 Bad Gateway</h1>", 502, "/minhas-redacoes"),
    ("<h1>Em manutencao</h1>", 200, "/minhas-redacoes"),
    ("<form>Entrar</form>", 200, "/auth/users/sign_in"),
])
def test_pagina_de_erro_ou_outra_pagina_nunca_vira_lista_vazia(html, status, caminho):
    pagina = PaginaFalsa(html)
    pagina.goto = lambda url, wait_until=None: _Resposta(status)
    pagina.url = f"https://www.esquemaredacao.com.br{caminho}"
    with pytest.raises(RuntimeError):
        ler_lista_redacoes(pagina)


def test_lista_de_verdade_continua_lida():
    assert len(ler_lista_redacoes(PaginaFalsa(_html_lista(LINHA_REAL)))) == 1
    vazia = PaginaFalsa("<p>Você tem <strong>998 crédito(s)</strong>.</p>")
    assert ler_lista_redacoes(vazia) == []  # conta sem redação (D1)


# ─── Contagem: ensaio e modo teste na mesma conta ────────────

@pytest.fixture
def envio(tmp_path):
    prog = Progresso(tmp_path / "p.db")
    pagina = MagicMock()
    pagina.locator.return_value.first.inner_text.return_value = "0- Narração"
    with patch.object(envio_item, "ler_saldo_creditos", autospec=True, return_value=10), \
         patch.object(envio_item, "ler_lista_redacoes", autospec=True, return_value=[]), \
         patch.object(envio_item, "contar_tema_hoje", autospec=True) as no_site, \
         patch.object(envio_item, "abrir_formulario_envio", autospec=True), \
         patch.object(envio_item, "ler_combo_temas", autospec=True, return_value=[("0", "0- Narração")]), \
         patch.object(envio_item, "selecionar_tema_por_codigo", autospec=True, return_value=True), \
         patch.object(envio_item, "selecionar_criterio", autospec=True, return_value=True), \
         patch.object(envio_item, "anexar_arquivo", autospec=True), \
         patch.object(envio_item, "aguardar_upload_aceito", autospec=True, return_value=True), \
         patch.object(envio_item, "clicar_enviar", autospec=True) as clicar, \
         patch.object(envio_item, "aguardar_confirmacao", autospec=True, return_value=True), \
         patch.object(envio_item.relogio, "perto_da_meia_noite", return_value=False):
        yield {"prog": prog, "page": pagina, "no_site": no_site, "clicar": clicar}
    prog.close()


def test_modo_teste_depois_do_ensaio_no_mesmo_tema_envia(envio):
    """Ensaio mandou 1 no tema 0 hoje (site 1, caderno 1). O modo teste tem 1
    arquivo no tema 0: antes virava JA_ENVIADO falso e nunca mais ia."""
    envio["prog"].marcar(ANA.id, "ensaio/x/Ana.JPG", ENVIADO, pasta="0")
    envio["no_site"].return_value = 1
    item = ItemFilaTeste("0 - Narração", "Ana.jpg", "0", Path("x"), "0 - Narração/Ana.jpg")
    assert envio_item.enviar_item(envio["page"], ANA.id, item, envio["prog"]) == ENVIADO
    assert envio["clicar"].call_count == 1


def test_enviado_a_mao_hoje_continua_pulando(envio):
    envio["no_site"].return_value = 1  # site tem, caderno não
    item = ItemFilaTeste("0 - Narração", "Ana.jpg", "0", Path("x"), "0 - Narração/Ana.jpg")
    assert envio_item.enviar_item(envio["page"], ANA.id, item, envio["prog"]) == "JA_ENVIADO"


def test_botao_ausente_e_erro_sem_clique():
    page = MagicMock()
    page.locator.return_value.first.count.return_value = 0
    with pytest.raises(BotaoEnviarAusente):
        confirmacao.clicar_enviar(page)
    assert page.locator.return_value.first.click.call_count == 0


def test_botao_ausente_vira_erro_e_nao_revisao(envio):
    envio["clicar"].side_effect = BotaoEnviarAusente("sem botao")
    item = ItemFilaTeste("0 - N", "Ana.jpg", "0", Path("x"), "0 - N/Ana.jpg")
    envio["no_site"].return_value = 0
    assert envio_item.enviar_item(envio["page"], ANA.id, item, envio["prog"]) == ERRO


# ─── Confirmação: linha antiga que muda não atrapalha ────────

def _pagina(*situacoes):
    from modulos.base import relogio
    hoje = relogio.data_site()
    linhas = "".join(f"<tr><td>{hoje}</td><td>000- D</td><td>0.0</td><td>{s}</td><td></td></tr>"
                     for s in situacoes)
    return PaginaFalsa(_html_lista(linhas))


def test_linha_antiga_corrigida_durante_a_espera_nao_da_falso_inconclusivo():
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(_pagina("Corrigida", "Pendente"), "000", timeout_segundos=5,
                                                linhas_esperadas=2, antes=["pendente"]) is True


# ─── Fluxo: meia-noite e logins seguidos ─────────────────────

def _cfg_lote(tmp_path, alunos):
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.pausa_envio_min_segundos = cfg.pausa_envio_max_segundos = 0
    (tmp_path / "100 - T").mkdir()
    arquivos = []
    for a in alunos:
        (tmp_path / "100 - T" / f"{a.nome}.JPG").write_bytes(a.nome.encode())
        arquivos.append(f"{a.nome}.JPG")
    return cfg, conciliar(alunos, {"100 - T": arquivos}, codigos_site=["100"])


def test_dois_logins_seguidos_falhando_param_tudo(tmp_path, caplog):
    alunos = [Aluno(n, f"{n.lower()}@x.com", senha="s") for n in ("Ana", "Bia", "Caio", "Davi")]  # M3
    cfg, resultado = _cfg_lote(tmp_path, alunos)
    with patch("modulos.base.config.PRODUCAO_BLOQUEADA", False), \
         patch.object(fep, "sync_playwright"), patch.object(fep, "obter_senha", return_value="s"), \
         patch.object(fep, "verificar_dominio_autorizado"), \
         patch.object(fep, "login", side_effect=LoginFalhou("sign_in")) as fazer_login, \
         patch.object(fep, "confirmar_identidade"), patch.object(fep, "logout"), \
         patch("builtins.input", return_value="ENVIAR"):
        assert fep.executar_envio_producao(cfg, resultado) == 1
    assert fazer_login.call_count == 2
    assert "senha do alunos.csv errada?" in caplog.text  # M3: não há mais senha padrão
    assert "2 logins seguidos falharam" in caplog.text


def test_perto_da_meia_noite_nem_abre_o_navegador(tmp_path, capsys):
    teste = Aluno(NOME_CONTA_TESTE, "teste@teste.com")
    cfg, resultado = _cfg_lote(tmp_path, [teste])
    with patch("modulos.base.relogio.perto_da_meia_noite", return_value=True), \
         patch.object(fep, "sync_playwright") as pw, patch("builtins.input", return_value="ENVIAR TESTE"):
        assert fep.executar_envio_producao(cfg, resultado, conta_teste=teste.email) == 2
    assert pw.call_count == 0
    assert "Perto da meia-noite" in capsys.readouterr().out


def test_modo_teste_com_lista_ilegivel_nao_envia(tmp_path):
    from modulos.envio.fluxo_envio_teste import executar_envio_teste
    cfg = Config()
    cfg.planilha = tmp_path / "alunos.csv"
    cfg.planilha.write_text("Aluno;Contato\n", encoding="utf-8")
    with patch("modulos.envio.fluxo_envio_teste.obter_email_teste", return_value="t@t.com"), \
         patch("modulos.envio.fluxo_envio_teste.executar_envio_producao") as fluxo:
        assert executar_envio_teste(cfg) == 2
    assert fluxo.call_count == 0


# ─── Desfazer usa a pasta do log ─────────────────────────────

def test_desfazer_log_do_modo_teste_nao_mexe_na_pasta_real(tmp_path):
    from modulos.ferramentas.revisao_interativa import desfazer_renomeacoes, renomear
    teste, real = tmp_path / "teste", tmp_path / "real"
    for raiz in (teste, real):
        (raiz / "Aporofobia").mkdir(parents=True)
        (raiz / "Aporofobia" / "Ana.jpg").write_bytes(b"x")
    log = tmp_path / "renomeacoes.csv"
    assert renomear(teste, "Aporofobia", "Ana.jpg", ANA, tmp_path / "p.db", log)[0] == "Ana Souza.jpg"
    (real / "Aporofobia" / "Ana.jpg").rename(real / "Aporofobia" / "Ana Souza.jpg")  # mesmo nome na real
    assert desfazer_renomeacoes(log, real, lambda *_: None) == 1
    assert (teste / "Aporofobia" / "Ana.jpg").is_file()
    assert (real / "Aporofobia" / "Ana Souza.jpg").is_file()  # a real ficou como estava


# ─── CSV do Excel + linha nova ───────────────────────────────

def test_acrescentar_em_csv_do_excel_converte_para_utf8(tmp_path):
    from modulos.dados.sugestao_temas import _ler_pastas, registrar_sugestoes_pasta
    caminho = tmp_path / "pastas.csv"
    caminho.write_bytes("pasta;codigo;tema;aprovado;semelhanca\nRedação A;100;;sim;\n".encode("cp1252"))
    registrar_sugestoes_pasta([("Redação B", "", "", 0.0)], caminho)
    assert [l["pasta"] for l in _ler_pastas(caminho)] == ["Redação A", "Redação B"]
    assert registrar_sugestoes_pasta([("Redação B", "", "", 0.0)], caminho) == 0  # não repete


# ─── Opções ──────────────────────────────────────────────────

@pytest.mark.parametrize("argv", [
    ["--desfazer-renomeacao", "x.csv", "--revisar"],
    ["--analise-remota", "--envio-real"],
    ["--analise-remota", "--modo-teste"],
    ["--ensaio", "0"],
])
def test_mais_combinacoes_recusadas(argv):
    import main as main_mod
    assert main_mod.main(argv) == 2


def test_planilha_xlsx_aceita_e_mail(tmp_path):
    from openpyxl import Workbook
    from modulos.dados.planilha_arquivos import carregar_alunos
    wb = Workbook()
    wb.active.title = "Planilha1"
    wb.active.append(["Nome", "E-mail"])
    wb.active.append(["Ana Souza", "ana@x.com"])
    wb.save(tmp_path / "alunos.xlsx")
    cfg = Config()
    cfg.planilha = tmp_path / "alunos.xlsx"
    assert [a.email for a in carregar_alunos(cfg)] == ["ana@x.com"]


def test_log_esconde_o_valor_da_senha_mas_nao_a_palavra(monkeypatch):
    import logging
    from modulos.base.progresso_relatorio import _FiltroSanitizador
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "Segredo#2026")
    def filtrado(msg):
        registro = logging.LogRecord("x", logging.ERROR, __file__, 1, msg, (), None)
        _FiltroSanitizador().filter(registro)
        return registro.getMessage()
    assert filtrado("login recusado (senha padrao errada?)") == "login recusado (senha padrao errada?)"
    assert "suprimido" in filtrado("tentou com Segredo#2026")
    assert "suprimido" in filtrado("senha: abc")
