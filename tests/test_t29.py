# -*- coding: utf-8 -*-
"""Testes offline da T29: revisão interativa no terminal e análise remota
na conta de um aluno. Sem navegador, sem dados reais."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base.config import Config
from modulos.dados.planilha_arquivos import Aluno, conciliar
from modulos.base.progresso_relatorio import ENVIADO, Progresso
from modulos.ferramentas.revisao_interativa import (
    desfazer_renomeacoes, grupos_para_revisar, nome_arquivo_para, revisar_nomes, revisar_pastas,
)
from modulos.dados.sugestao_temas import aprovar_pasta, carregar_codigos_pasta, registrar_sugestoes_pasta

ANA = Aluno(nome="ANA LALARA LARILI DOS LARITO", email="ana@escola.com")
ANA_M = Aluno(nome="ANA LALARA LARISA LAMORA", email="anam@escola.com")
DOUGLAS = Aluno(nome="DOUGLAS LARUTO DA LAMOLI", email="douglas@escola.com")
ALUNOS = [ANA, ANA_M, DOUGLAS]
TEMAS = [("100", "100- Impactos da invisibilidade de filiação para os cidadãos brasileiros"),
         ("9", "9- Expectativa de vida"), ("0000", "0000- Simulado 01"), ("0000", "0000- Simulado 02")]
FILIACAO = "3B - Impacatos da Invisibilidade da filiação para o cidadão brasileiro"
APOROFOBIA = "3B - Efeitos da aporofobia"


def respostas(*textos):
    """Simula o Antônio digitando, uma resposta por pergunta."""
    fila = list(textos)
    return lambda _prompt: fila.pop(0)


def _pastas(tmp_path, estrutura):
    raiz = tmp_path / "Redações plataforma"
    for pasta, arquivos in estrutura.items():
        (raiz / pasta).mkdir(parents=True)
        for a in arquivos:
            (raiz / pasta / a).write_bytes(b"x")
    return raiz


# ─── Pastas ──────────────────────────────────────────────────

def test_aprovar_pasta_atualiza_a_linha_e_mantem_as_outras(tmp_path):
    caminho = tmp_path / "pastas.csv"
    registrar_sugestoes_pasta([(FILIACAO, "100", "x", 95.0), (APOROFOBIA, "9", "y", 64.0)], caminho)

    aprovar_pasta(caminho, FILIACAO, "100", TEMAS[0][1])

    assert carregar_codigos_pasta(caminho) == {FILIACAO: "100"}
    assert len(list(csv.DictReader(open(caminho, encoding="utf-8-sig"), delimiter=";"))) == 2


def test_revisar_pastas_enter_aceita_provavel_e_pular_nao_aprova(tmp_path):
    caminho = tmp_path / "pastas.csv"
    aprovadas, saiu = revisar_pastas([APOROFOBIA, FILIACAO], TEMAS, caminho,
                                     entrada=respostas("p", ""), saida=lambda *_: None)
    assert (aprovadas, saiu) == (1, False)
    assert carregar_codigos_pasta(caminho) == {FILIACAO: "100"}


def test_revisar_pastas_enter_sem_sugestao_provavel_nao_aprova_o_fraco(tmp_path):
    caminho = tmp_path / "pastas.csv"
    assert revisar_pastas([APOROFOBIA], TEMAS, caminho, entrada=respostas(""),
                          saida=lambda *_: None) == (0, False)
    assert carregar_codigos_pasta(caminho) == {}


def test_revisar_pastas_recusa_codigo_inexistente_e_repetido_no_combo(tmp_path):
    caminho = tmp_path / "pastas.csv"
    saidas = []
    revisar_pastas([APOROFOBIA], TEMAS, caminho, entrada=respostas("77", "0000", "9"), saida=saidas.append)
    texto = "\n".join(saidas)
    assert "Tema 77 nao existe" in texto and "0000 aparece 2x" in texto
    assert carregar_codigos_pasta(caminho) == {APOROFOBIA: "9"}


def test_revisar_pastas_texto_busca_outro_tema(tmp_path):
    saidas = []
    revisar_pastas([APOROFOBIA], TEMAS, tmp_path / "p.csv", entrada=respostas("expectativa vida", "q"),
                   saida=saidas.append)
    assert '  Temas com "expectativa vida":' in saidas
    assert any(s.strip().startswith("[     9]") for s in saidas)


def test_revisar_pastas_busca_por_palavra_sem_acento_e_lista_todos(tmp_path):
    temas = TEMAS + [("102", "102- Arquitetura hostil - impactos da desumanização de pessoas em situação de rua")]
    saidas = []
    revisar_pastas([APOROFOBIA], temas, tmp_path / "p.csv", entrada=respostas("situacao rua", "t", "102"),
                   saida=saidas.append)
    assert '  Temas com "situacao rua":' in saidas
    assert not any("Expectativa" in s for s in saidas[saidas.index('  Temas com "situacao rua":'):saidas.index("  Todos os temas do site:")])
    assert "  Todos os temas do site:" in saidas
    assert carregar_codigos_pasta(tmp_path / "p.csv") == {APOROFOBIA: "102"}


def test_revisar_pastas_mostra_o_provavel_e_porcentagens_do_maior_para_o_menor(tmp_path):
    saidas = []
    revisar_pastas([FILIACAO], TEMAS, tmp_path / "p.csv", entrada=respostas("q"), saida=saidas.append)
    assert "✔ Provavelmente e o tema 100: Impactos da invisibilidade de filiação para os cidadãos brasileiros" in " ".join(s.strip() for s in saidas)
    import re
    pcts = [int(m.group(1)) for s in saidas if (m := re.search(r"(\d+)%", s))]
    assert pcts and pcts == sorted(pcts, reverse=True)
    assert any("█" in s and "100" in s for s in saidas)


def test_g_aprova_o_tema_generico_quando_o_tema_nao_existe(tmp_path):
    temas = TEMAS + [("000", "000- DISSERTATIVO ARGUMENTATIVO")]
    caminho = tmp_path / "p.csv"
    saidas = []
    revisar_pastas([APOROFOBIA], temas, caminho, entrada=respostas("g"), saida=saidas.append)
    assert any("g        = tema generico: DISSERTATIVO ARGUMENTATIVO (000)" in s for s in saidas)
    assert carregar_codigos_pasta(caminho) == {APOROFOBIA: "000"}


def test_sem_tema_generico_no_site_g_nao_aprova(tmp_path):
    caminho = tmp_path / "p.csv"
    revisar_pastas([APOROFOBIA], TEMAS, caminho, entrada=respostas("g", "p"), saida=lambda *_: None)
    assert carregar_codigos_pasta(caminho) == {}


# ─── Nomes ───────────────────────────────────────────────────

def test_grupos_juntam_o_mesmo_nome_e_ignoram_exato_e_branco():
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG", "Douglas em branco.JPG",
                                              "ANA LALARA LARILI DOS LARITO.JPG"],
                                   APOROFOBIA: ["Ana Lalara Larili.JPG"]}, codigos_site=["100"])
    grupos = grupos_para_revisar(resultado, ALUNOS)
    assert [(nome, len(itens)) for nome, itens in grupos] == [("Ana Lalara Larili", 2)]


def test_nome_novo_mantem_extensao_e_codigo():
    assert nome_arquivo_para("Ana Lalara.JPG", ANA) == "ANA LALARA LARILI DOS LARITO.JPG"
    assert nome_arquivo_para("100 - Ana.jpg", ANA) == "100 - ANA LALARA LARILI DOS LARITO.jpg"


def test_enter_renomeia_em_todas_as_pastas_e_desfazer_volta(tmp_path):
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG"], APOROFOBIA: ["Ana Lalara Larili.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG"], APOROFOBIA: ["Ana Lalara Larili.JPG"]},
                          codigos_site=["100"])
    log = tmp_path / "log.csv"

    renomeados, _ = revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                                  log, entrada=respostas(""), saida=lambda *_: None)

    assert renomeados == 2
    assert (raiz / FILIACAO / "ANA LALARA LARILI DOS LARITO.JPG").is_file()
    assert (raiz / APOROFOBIA / "ANA LALARA LARILI DOS LARITO.JPG").is_file()
    assert desfazer_renomeacoes(log, raiz, saida=lambda *_: None) == 2
    assert (raiz / FILIACAO / "Ana Lalara Larili.JPG").is_file()


def test_varias_sugestoes_enter_nao_escolhe_sozinho(tmp_path):
    """"Ana Lalara" cabe em 2 alunas: Enter pula, nada renomeado."""
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara.JPG"]}, codigos_site=["100"])
    renomeados, _ = revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                                  tmp_path / "log.csv", entrada=respostas(""), saida=lambda *_: None)
    assert renomeados == 0
    assert (raiz / FILIACAO / "Ana Lalara.JPG").is_file()


def test_busca_por_texto_e_escolha_por_numero(tmp_path):
    """Nome sem sugestão: o Antônio digita parte do nome e escolhe o número."""
    raiz = _pastas(tmp_path, {FILIACAO: ["Dg.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Dg.JPG"]}, codigos_site=["100"])
    renomeados, _ = revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                                  tmp_path / "log.csv", entrada=respostas("douglas", "1"),
                                  saida=lambda *_: None)
    assert renomeados == 1
    assert (raiz / FILIACAO / "DOUGLAS LARUTO DA LAMOLI.JPG").is_file()


def test_nao_renomeia_se_ja_existe_arquivo_do_aluno_na_pasta(tmp_path):
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG", "ANA LALARA LARILI DOS LARITO.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG", "ANA LALARA LARILI DOS LARITO.JPG"]},
                          codigos_site=["100"])
    saidas = []
    renomeados, _ = revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                                  tmp_path / "log.csv", entrada=respostas(""), saida=saidas.append)
    assert renomeados == 0
    assert any("ja existe" in s for s in saidas)
    assert (raiz / FILIACAO / "Ana Lalara Larili.JPG").is_file()


def test_nao_renomeia_arquivo_ja_enviado(tmp_path):
    """A chave do progresso é pasta/arquivo: renomear depois de enviar abriria reenvio."""
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG"]})
    banco = tmp_path / "p.db"
    with Progresso(banco) as prog:
        prog.marcar(ANA.id, f"{FILIACAO}/Ana Lalara Larili.JPG", ENVIADO, pasta=FILIACAO)
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG"]}, codigos_site=["100"])
    saidas = []
    renomeados, _ = revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, banco,
                                  tmp_path / "log.csv", entrada=respostas(""), saida=saidas.append)
    assert renomeados == 0
    assert any("ENVIADO" in s for s in saidas)


def test_q_sai_sem_renomear(tmp_path):
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG"]}, codigos_site=["100"])
    assert revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                         tmp_path / "log.csv", entrada=respostas("q"), saida=lambda *_: None) == (0, True)


def test_sem_terminal_sai_em_vez_de_travar(tmp_path):
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG"]})
    resultado = conciliar(ALUNOS, {FILIACAO: ["Ana Lalara Larili.JPG"]}, codigos_site=["100"])

    def sem_terminal(_):
        raise EOFError

    assert revisar_nomes(grupos_para_revisar(resultado, ALUNOS), ALUNOS, raiz, tmp_path / "p.db",
                         tmp_path / "log.csv", entrada=sem_terminal, saida=lambda *_: None) == (0, True)


# ─── main ────────────────────────────────────────────────────

def _cfg(tmp_path, raiz):
    cfg = Config()
    cfg.planilha = tmp_path / "dados_alunos.csv"
    cfg.planilha.write_text("Nome;Email\nANA LALARA LARILI DOS LARITO;ana@escola.com\n", encoding="utf-8")
    cfg.pasta_relatorios = tmp_path / "relatorios"
    cfg.banco_progresso = tmp_path / "relatorios" / "p.db"
    cfg.arquivo_nomes_aprovados = tmp_path / "nomes.csv"
    cfg.arquivo_pastas_aprovadas = tmp_path / "pastas.csv"
    (tmp_path / "dados").mkdir()
    (tmp_path / "dados" / "temas_site.csv").write_text(
        "codigo,texto\n100,100- Impactos da invisibilidade de filiação para os cidadãos brasileiros\n",
        encoding="utf-8")
    return cfg


def test_main_revisar_e_depois_o_dry_run_tem_fila(tmp_path, monkeypatch, capsys):
    import main as main_mod
    raiz = _pastas(tmp_path, {FILIACAO: ["Ana Lalara Larili.JPG"]})
    cfg = _cfg(tmp_path, raiz)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    monkeypatch.setattr("builtins.input", respostas("", ""))  # Enter no tema 100, Enter na Ana

    assert main_mod.main(["--pasta", str(raiz), "--revisar"]) == 0
    assert "1 pasta(s) aprovada(s), 1 arquivo(s) renomeado(s)" in capsys.readouterr().out

    assert main_mod.main(["--pasta", str(raiz)]) == 0
    assert "Prontas para enviar:" in capsys.readouterr().out


def test_main_revisar_nao_combina_com_envio_real(tmp_path, monkeypatch):
    import main as main_mod
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: Config())
    assert main_mod.main(["--revisar", "--envio-real"]) == 2


def test_main_conta_aluno_fora_da_lista_da_erro(tmp_path, monkeypatch, capsys):
    import main as main_mod
    cfg = _cfg(tmp_path, tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)
    assert main_mod.main(["--analise-remota", "--conta-aluno", "outro@escola.com"]) == 2
    assert "nao esta na lista" in capsys.readouterr().out


# ─── Análise remota na conta do aluno ────────────────────────

@pytest.fixture
def analise_mocks():
    from modulos.site import analise_remota as ar
    with patch.object(ar, "sync_playwright"), \
         patch.object(ar, "obter_email_teste", return_value="teste@x.com") as email_teste, \
         patch.object(ar, "obter_senha", return_value="s") as senha, \
         patch.object(ar, "verificar_dominio_autorizado"), \
         patch.object(ar, "login") as login, \
         patch.object(ar, "confirmar_identidade") as identidade, \
         patch.object(ar, "abrir_formulario_envio"), \
         patch.object(ar, "ler_combo_temas") as combo, \
         patch("builtins.input", return_value="ANALISAR"):
        yield {"login": login, "combo": combo, "senha": senha, "identidade": identidade,
               "email_teste": email_teste}


def test_analise_remota_na_conta_do_aluno_usa_senha_padrao(tmp_path, analise_mocks, capsys):
    from modulos.site.analise_remota import executar_analise_remota
    caminho = tmp_path / "temas_site.csv"
    caminho.write_text("codigo,texto\n100,100- Filiação\n", encoding="utf-8")
    analise_mocks["combo"].return_value = [("100", "100- Filiação"), ("102", "102- Aporofobia")]

    assert executar_analise_remota(Config(), caminho, aluno=ANA) == 0

    analise_mocks["senha"].assert_called_once_with("ESQUEMA_SENHA_PADRAO")
    assert analise_mocks["email_teste"].call_count == 0
    assert analise_mocks["login"].call_args.args[2] == ANA.email
    assert analise_mocks["identidade"].call_args.args[1] is ANA
    assert "Codigos novos em relacao ao CSV anterior: ['102']" in capsys.readouterr().out


# ─── Trava: nada vai para aluno real (Antônio, 22/10) ────────

def test_producao_bloqueada_por_padrao():
    from modulos.base import config as config_mod
    assert config_mod.PRODUCAO_BLOQUEADA is True


def test_main_envio_real_de_producao_bloqueado_sem_ler_alunos(tmp_path, monkeypatch, capsys):
    import main as main_mod
    cfg = _cfg(tmp_path, tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main_mod, "carregar_config", lambda caminho=None: cfg)

    def proibido(*a, **k):
        raise AssertionError("passou da trava")
    monkeypatch.setattr(main_mod, "carregar_alunos", proibido)
    monkeypatch.setattr(main_mod, "executar_envio_producao", proibido)

    assert main_mod.main(["--envio-real", "--pasta", str(tmp_path)]) == 2
    assert "Envio para alunos reais desativado" in capsys.readouterr().out


def test_fluxo_de_producao_bloqueado_mesmo_chamado_direto(tmp_path, monkeypatch):
    from modulos.envio import fluxo_envio_producao as fep
    monkeypatch.setattr(fep, "montar_lote_producao", lambda *a, **k: (_ for _ in ()).throw(AssertionError("montou lote")))
    with patch("builtins.input", side_effect=AssertionError("pediu ENVIAR")):
        assert fep.executar_envio_producao(Config(), conciliar([], {}, codigos_site=[])) == 2


# ─── Tela (T33) ──────────────────────────────────────────────

def test_nome_do_tema_aparece_inteiro_quebrado_em_linhas(tmp_path):
    longo = "102- Arquitetura hostil - impactos da desumanização de pessoas em situação de rua no Brasil e muito mais"
    saidas = []
    revisar_pastas(["3B - Arquitetura hostil"], TEMAS + [("102", longo)], tmp_path / "p.csv",
                   entrada=respostas("q"), saida=saidas.append)
    juntos = " ".join(s.strip() for s in saidas)
    assert "situação de rua no Brasil e muito mais" in juntos
    assert "…" not in juntos
    assert all(len(s) <= 80 for s in saidas if "Arquitetura" in s or "muito mais" in s)


def test_sem_terminal_nao_sai_codigo_de_cor(tmp_path):
    saidas = []
    revisar_pastas([FILIACAO], TEMAS, tmp_path / "p.csv", entrada=respostas("q"), saida=saidas.append)
    assert not any("\033[" in s for s in saidas)


def test_com_cores_a_barra_fica_verde_quando_provavel(monkeypatch):
    from modulos.base import tela  # T41: o visual mora em tela.py
    monkeypatch.setitem(tela._cores, "ativas", True)
    assert "\033[32m" in tela.barra(95.0)
    assert "\033[33m" in tela.barra(65.0)
