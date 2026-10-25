# -*- coding: utf-8 -*-
"""Testes offline da T58 (auditoria de 24/10: bugs 007 a 027). Sem navegador."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modulos.base import relogio
from modulos.base.excecoes import ConfirmacaoInconclusiva
from modulos.base.progresso_relatorio import ENVIADO, JA_ENVIADO, REVISAO_MANUAL, Progresso
from modulos.dados.planilha_arquivos import Aluno
from modulos.envio import envio_item
from modulos.envio.fila_teste import ItemFilaTeste
from modulos.site import confirmacao
from modulos.site.lista_redacoes import ItemListaRedacao, contar_tema_hoje, ler_lista_redacoes_html
from tests.test_lista_redacoes_layout_real import PaginaFalsa, _html_lista

ANA = Aluno("Ana Souza", "ana@x.com")


# ─── Bug 007: lote montado antes da trava não reenvia ────────

@pytest.fixture
def envio(tmp_path):
    prog = Progresso(tmp_path / "p.db")
    pagina = MagicMock()
    pagina.locator.return_value.first.inner_text.return_value = "000- D"
    with patch.object(envio_item, "ler_saldo_creditos", autospec=True, return_value=10), \
         patch.object(envio_item, "ler_lista_redacoes", autospec=True, return_value=[]), \
         patch.object(envio_item, "contar_tema_hoje", autospec=True) as no_site, \
         patch.object(envio_item, "abrir_formulario_envio", autospec=True), \
         patch.object(envio_item, "ler_combo_temas", autospec=True, return_value=[("000", "000- D")]), \
         patch.object(envio_item, "selecionar_tema_por_codigo", autospec=True, return_value=True), \
         patch.object(envio_item, "selecionar_criterio", autospec=True, return_value=True), \
         patch.object(envio_item, "anexar_arquivo", autospec=True), \
         patch.object(envio_item, "aguardar_upload_aceito", autospec=True, return_value=True), \
         patch.object(envio_item, "clicar_enviar", autospec=True) as clicar, \
         patch.object(envio_item, "aguardar_confirmacao", autospec=True, return_value=True), \
         patch.object(envio_item.relogio, "perto_da_meia_noite", return_value=False):
        yield {"prog": prog, "page": pagina, "no_site": no_site, "clicar": clicar}
    prog.close()


def _item(hash_arquivo=""):
    return ItemFilaTeste("000 - D", "Ana Souza.jpg", "000", Path("x"), "000 - D/Ana Souza.jpg",
                         hash_arquivo=hash_arquivo)


def test_item_ja_enviado_por_outra_janela_nao_e_enviado_de_novo(envio):
    """Duas janelas montaram o lote; a 1ª enviou. A 2ª pega a trava depois:
    site 1, caderno 1 -> antes clicava de novo (total = caderno + 1)."""
    envio["prog"].marcar(ANA.id, "000 - D/Ana Souza.jpg", ENVIADO, pasta="000")
    envio["no_site"].return_value = 1
    assert envio_item.enviar_item(envio["page"], ANA.id, _item(), envio["prog"]) == JA_ENVIADO
    assert envio["clicar"].call_count == 0
    assert envio["prog"].obter(ANA.id, "000 - D/Ana Souza.jpg")["estado"] == ENVIADO  # não sobrescreve


def test_item_em_revisao_manual_para_sem_clicar(envio):
    envio["prog"].marcar(ANA.id, "000 - D/Ana Souza.jpg", REVISAO_MANUAL, pasta="000")
    envio["no_site"].return_value = 1
    assert envio_item.enviar_item(envio["page"], ANA.id, _item(), envio["prog"]) == REVISAO_MANUAL
    assert envio["clicar"].call_count == 0


def test_mesma_foto_ja_enviada_com_outro_nome_nao_vai(envio):
    envio["prog"].marcar(ANA.id, "outra/Ana.jpg", ENVIADO, pasta="000", hash_arquivo="abc")
    envio["no_site"].return_value = 1
    assert envio_item.enviar_item(envio["page"], ANA.id, _item("abc"), envio["prog"]) == JA_ENVIADO
    assert envio["clicar"].call_count == 0


def test_item_novo_continua_sendo_enviado(envio):
    envio["no_site"].return_value = 0
    assert envio_item.enviar_item(envio["page"], ANA.id, _item("abc"), envio["prog"]) == ENVIADO
    assert envio["clicar"].call_count == 1


# ─── Bug 008: só Pendente (ou Processando no prazo) confirma ─

def _pagina(*situacoes):
    hoje = relogio.data_site()
    linhas = "".join(f"<tr><td>{hoje}</td><td>000- D</td><td>0.0</td><td>{s}</td><td></td></tr>"
                     for s in situacoes)
    return PaginaFalsa(_html_lista(linhas))


@pytest.mark.parametrize("situacao", ["Recusada", "Falha no upload", "Arquivo inválido"])
def test_linha_nova_em_situacao_desconhecida_e_inconclusiva(situacao):
    with patch("modulos.site.confirmacao.time.sleep"), pytest.raises(ConfirmacaoInconclusiva):
        confirmacao.aguardar_confirmacao(_pagina(situacao), "000", timeout_segundos=1,
                                         linhas_esperadas=1, antes=[])


def test_linha_nova_pendente_confirma():
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(_pagina("Pendente"), "000", timeout_segundos=1,
                                                linhas_esperadas=1, antes=[]) is True


def test_linha_antiga_desconhecida_nao_atrapalha():
    """A linha de antes já estava numa situação estranha; a nova é Pendente."""
    with patch("modulos.site.confirmacao.time.sleep"):
        assert confirmacao.aguardar_confirmacao(_pagina("Em correção", "Pendente"), "000",
                                                timeout_segundos=1, linhas_esperadas=2,
                                                antes=["em correção"]) is True


# ─── Bug 009: lista com layout mudado é ilegível ────────────

def _tabela_com(cabecalho, linhas):
    ths = "".join(f"<th>{c}</th>" for c in cabecalho)
    return f"<table><thead><tr>{ths}</tr></thead><tbody>{linhas}</tbody></table>"


@pytest.mark.parametrize("extra", [
    "<table><tbody><tr><td>a</td><td>b</td><td>c</td></tr></tbody></table>",
    "<table></table>",
])
def test_cabecalho_mudado_com_outra_tabela_sem_th_e_ilegivel(extra):
    hoje = relogio.data_site()
    lista = _tabela_com(["Data", "Tema", "Situação", "Nota"],
                        f"<tr><td>{hoje}</td><td>000- D</td><td>Pendente</td><td></td></tr>")
    with pytest.raises(RuntimeError, match="Cabecalho"):
        ler_lista_redacoes_html(extra + lista)


def test_tabela_certa_com_outra_sem_th_continua_lida():
    hoje = relogio.data_site()
    lista = _tabela_com(["Data", "Tema", "Nota", "Situação"],
                        f"<tr><td>{hoje}</td><td>000- D</td><td></td><td>Pendente</td></tr>")
    assert len(ler_lista_redacoes_html("<table></table>" + lista)) == 1


def _linha(data, tema):
    return ItemListaRedacao(codigo="", tema=tema, data=data, situacao="Pendente", nota="", botao_texto="")


@pytest.mark.parametrize("data, tema", [
    ("24/10/2026 14:05", "000- D"),
    ("2026-10-24", "000- D"),
    ("24/10/2026", "Tema 000 - D"),
])
def test_data_ou_tema_em_formato_inesperado_bloqueia_a_contagem(data, tema):
    with pytest.raises(RuntimeError):
        contar_tema_hoje([_linha(data, tema)], "000", "24/10/2026")


def test_formato_observado_continua_contando():
    assert contar_tema_hoje([_linha("24/10/2026", "000- D"), _linha("23/10/2026", "5- X")],
                            "000", "24/10/2026") == 1


# ─── Bugs 010 a 015: dados ───────────────────────────────────

from modulos.dados.arquivos_csv import CsvIlegivel  # noqa: E402
from modulos.dados.nomes_aprovados import carregar_nomes_aprovados  # noqa: E402
from modulos.dados.normalizacao import extrair_pessoa  # noqa: E402
from modulos.dados.planilha_arquivos import conciliar, descobrir_arquivos  # noqa: E402
from modulos.dados.sugestao_temas import aprovar_pasta, carregar_codigos_pasta  # noqa: E402
from modulos.envio.fila_producao import hash_do_arquivo, montar_lote_producao  # noqa: E402


@pytest.mark.parametrize("arquivo", ["Ana Souza - Red 2.jpg", "Ana Souza - Redação (2).jpg",
                                     "Ana Souza - Red - Copia.jpg"])
def test_pagina_2_depois_do_marcador_vai_para_revisao(arquivo):
    assert extrair_pessoa(arquivo) != "Ana Souza"
    item = conciliar([ANA], {"100 - T": [arquivo]}, codigos_site={"100"}).itens[0]
    assert item.estado == "REVISAO_MANUAL"


def test_marcador_sem_numero_continua_identificando():
    assert extrair_pessoa("Ana Souza - Redação.jpg") == "Ana Souza"


def test_aprovacao_parecido_cai_quando_entra_outro_aluno_igual(tmp_path):
    caminho = tmp_path / "nomes.csv"
    caminho.write_text("nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo\n"
                       "Ana;Ana Souza;ana@x.com;sim;parecido 100%\n", encoding="utf-8")
    assert "ana" in carregar_nomes_aprovados(caminho, [ANA])
    assert carregar_nomes_aprovados(caminho, [ANA, Aluno("Ana Lima", "lima@x.com")]) == {}


def test_aprovacao_com_erro_de_digitacao_continua_com_outro_aluno_diferente(tmp_path):
    caminho = tmp_path / "nomes.csv"
    caminho.write_text("nome_no_arquivo;aluno_nome;aluno_email;aprovado;motivo\n"
                       "Ana Sousa;Ana Souza;ana@x.com;sim;parecido 94%\n", encoding="utf-8")
    alunos = [ANA, Aluno("Bruno Lima", "bruno@x.com")]
    assert "ana sousa" in carregar_nomes_aprovados(caminho, alunos)


def test_csv_de_aprovacao_com_virgula_avisa_e_nao_e_regravado(tmp_path, capsys):
    caminho = tmp_path / "pastas.csv"
    original = "pasta,codigo,tema,aprovado,semelhanca\n3B - X,000,000- D,sim,\n"
    caminho.write_text(original, encoding="utf-8")
    assert carregar_codigos_pasta(caminho) == {}
    assert "vírgula" in capsys.readouterr().out
    with pytest.raises(CsvIlegivel):
        aprovar_pasta(caminho, "3B - Y", "000", "000- D")
    assert caminho.read_text(encoding="utf-8") == original


def test_mesma_foto_ja_registrada_para_outro_aluno_nao_entra(tmp_path):
    (tmp_path / "100 - T").mkdir()
    foto = tmp_path / "100 - T" / "Ana Souza.jpg"
    foto.write_bytes(b"foto da bia")
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar("bia@x.com", "antiga/Bia Lima.jpg", ENVIADO, pasta="100", hash_arquivo=hash_do_arquivo(foto))
        resultado = conciliar([ANA], {"100 - T": ["Ana Souza.jpg"]}, codigos_site={"100"})
        lotes, ignorados = montar_lote_producao(resultado, tmp_path, prog)
    assert lotes == [] and "OUTRO aluno" in ignorados[0][1]


def test_foto_que_so_passou_pelo_ensaio_continua_podendo_ir(tmp_path):
    (tmp_path / "100 - T").mkdir()
    foto = tmp_path / "100 - T" / "Ana Souza.jpg"
    foto.write_bytes(b"foto da ana")
    with Progresso(tmp_path / "p.db") as prog:
        prog.marcar("teste@x.com", "ensaio/100 - T/Ana Souza.jpg", ENVIADO, pasta="100",
                    hash_arquivo=hash_do_arquivo(foto))
        resultado = conciliar([ANA], {"100 - T": ["Ana Souza.jpg"]}, codigos_site={"100"})
        lotes, _ = montar_lote_producao(resultado, tmp_path, prog)
    assert len(lotes) == 1


def test_foto_solta_na_raiz_gera_aviso(tmp_path, capsys):
    from modulos.base.config import Config
    cfg = Config()
    cfg.pasta_raiz = tmp_path
    (tmp_path / "Ana Souza.jpg").write_bytes(b"x")
    (tmp_path / "LEIA-ME.md").write_text("x", encoding="utf-8")
    with pytest.warns(UserWarning):
        assert descobrir_arquivos(cfg) == {}
    saida = capsys.readouterr().out
    assert "Ana Souza.jpg" in saida and "LEIA-ME" not in saida


# ─── Bugs 016 a 022: menu e ferramentas ──────────────────────

from modulos.ferramentas import arquivo_morto, menu  # noqa: E402
from modulos.ferramentas.revisao_interativa import COLUNAS_LOG, desfazer_renomeacoes  # noqa: E402
from modulos.site.conferencia_site import CANCELADA, ConferenciaAluno, comparar, faltam_enviar  # noqa: E402


@pytest.mark.skipif(sys.platform != "win32", reason="só o Windows trava arquivo aberto")
def test_arquivo_morto_com_foto_aberta_nao_deixa_pasta_pela_metade(tmp_path):
    pasta = tmp_path / "100 - Tema"
    pasta.mkdir()
    for nome in ("a.jpg", "b.jpg", "c.jpg"):
        (pasta / nome).write_bytes(nome.encode())
    with open(pasta / "b.jpg", "rb"):
        assert arquivo_morto._mover(pasta, tmp_path / "morto" / "100 - Tema") == "nada"
    assert sorted(p.name for p in pasta.iterdir()) == ["a.jpg", "b.jpg", "c.jpg"]
    assert arquivo_morto._mover(pasta, tmp_path / "100 - Tema movida") == "ok"


@pytest.mark.parametrize("tecla", ["²", "³"])
def test_digito_sobrescrito_no_menu_nao_derruba(tecla):
    respostas = iter([tecla])
    assert menu.argumentos_da_opcao("3", entrada=lambda _: next(respostas), saida=lambda *_: None) is None


def test_erro_na_pergunta_da_opcao_nao_fecha_o_menu():
    respostas = iter(["3", "", "0"])
    with patch.object(menu, "argumentos_da_opcao", side_effect=ValueError("x")):
        assert menu.executar_menu(lambda a: 0, entrada=lambda _: next(respostas), saida=lambda *_: None) == 0


@pytest.mark.skipif(sys.platform != "win32", reason="só o Windows trava arquivo aberto")
def test_desfazer_continua_quando_um_arquivo_esta_aberto(tmp_path):
    import csv
    (tmp_path / "P").mkdir()
    (tmp_path / "P" / "Aluno Um.jpg").write_bytes(b"1")
    (tmp_path / "P" / "Aluno Dois.jpg").write_bytes(b"2")
    log = tmp_path / "log.csv"
    with open(log, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(COLUNAS_LOG)
        w.writerow(["P", "um.jpg", "Aluno Um.jpg", "", str(tmp_path)])
        w.writerow(["P", "dois.jpg", "Aluno Dois.jpg", "", str(tmp_path)])
    with open(tmp_path / "P" / "Aluno Dois.jpg", "rb"):
        assert desfazer_renomeacoes(log, tmp_path, saida=lambda *_: None) == 1
    assert (tmp_path / "P" / "um.jpg").is_file()


def _conferencia(*linhas_site):
    itens = conciliar([ANA], {"100 - T": ["Ana Souza.jpg"]}, codigos_site={"100"}).fila_validada()
    lista = [ItemListaRedacao(codigo=c, tema=f"{c}- T", data="01/10/2026", situacao=s, nota="", botao_texto="")
             for c, s in linhas_site]
    conf = ConferenciaAluno(ANA, list(itens), lista=lista)
    comparar(conf)
    return conf


def test_cancelada_no_site_nao_conta_como_no_site_nem_entra_no_envio():
    conf = _conferencia(("100", "Cancelada"))
    assert conf.linhas[0][1] == CANCELADA
    assert faltam_enviar([conf]) == []


def test_cancelada_de_outro_tema_nao_vira_sobra():
    conf = _conferencia(("000", "Cancelada"))
    assert [i.arquivo for i in faltam_enviar([conf])] == ["Ana Souza.jpg"]


@pytest.mark.parametrize("argv", [
    ["--arquivar", "--conferir-site"], ["--arquivar", "--resolver"], ["--preparar", "--envio-real"],
    ["--resolver", "--ensaio", "3"], ["--resolver", "--modo-teste"], ["--conferir-site", "--enviar-faltantes"],
])
def test_acoes_que_rodam_sozinhas_recusam_combinacao(argv):
    import main as main_mod
    assert main_mod.main(argv) == 2


def test_config_que_nao_existe_e_recusado(tmp_path, capsys):
    import main as main_mod
    assert main_mod.main(["--config", str(tmp_path / "nao_existe.ini")]) == 2
    assert "nao encontrado" in capsys.readouterr().out


def test_link_da_pasta_de_tema_no_dry_run_usa_pasta_true():
    texto = (Path(__file__).resolve().parent.parent / "main.py").read_text(encoding="utf-8")
    assert 'Path(cfg.pasta_raiz) / tema, pasta=True)' in texto


# ─── Bugs 023 a 026: repositório público ─────────────────────

from modulos.ferramentas.auditoria_publica import auditar, nome_proibido  # noqa: E402


@pytest.mark.parametrize("caminho", ["AGENTS.md", "docs/PENDENCIAS.md", "docs/historico/x.md", ".claude/a.json",
                                     "Redações plataforma/x/A.JPG", "relatorios/progresso.db", ".env",
                                     "dados/turma_3B.csv", "memory/x.md"])
def test_auditoria_recusa_arquivo_proibido(caminho):
    assert nome_proibido(caminho)


@pytest.mark.parametrize("caminho", ["README.md", "dados/temas_site.csv", "logs/.gitkeep", "modulos/base/tela.py"])
def test_auditoria_aceita_arquivo_publico(caminho):
    assert nome_proibido(caminho) is None


def test_auditoria_acha_valor_sem_mostrar():
    achados = auditar({"docs/x.md": "a aluna Ána Souza mandou"}, {"nome do aluno 1": "ana souza"})
    assert achados == [("docs/x.md", "nome do aluno 1")]


def test_gitignore_cobre_fotos_em_maiuscula_e_historico():
    import subprocess
    raiz = Path(__file__).resolve().parent.parent
    caminhos = ["Redações plataforma/x/A.JPG", "testes/redacoes_teste/0 - N/a.JPG", "foto.HEIC", "docs/historico/x.md"]
    r = subprocess.run(["git", "-c", "core.ignorecase=false", "check-ignore", "--no-index", *caminhos],
                       cwd=raiz, capture_output=True, text=True, encoding="utf-8")
    if r.returncode == 128:
        pytest.skip("sem git")
    assert len(r.stdout.strip().splitlines()) == len(caminhos)


def test_temas_site_nao_grava_email(tmp_path):
    from modulos.site.analise_remota import gravar_temas_csv
    texto = (Path(__file__).resolve().parent.parent / "modulos" / "site" / "analise_remota.py").read_text(
        encoding="utf-8")
    assert "mascarar_email" not in texto
    gravar_temas_csv([("0", "0- N")], tmp_path / "t.csv", "teste")
    assert "@" not in (tmp_path / "t.csv").read_text(encoding="utf-8-sig")


def test_valor_de_exemplo_do_env_nao_e_senha(monkeypatch):
    from modulos.base import config
    monkeypatch.setenv("ESQUEMA_SENHA_PADRAO", "<definir-no-.env>")
    with patch.object(config, "getpass", return_value="digitada") as pergunta:
        assert config.obter_senha() == "digitada"
    assert pergunta.called
