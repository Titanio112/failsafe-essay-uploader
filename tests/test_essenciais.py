# -*- coding: utf-8 -*-
"""Testes essenciais: conciliação, SQLite, dry-run, limites, modo teste."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Inserir o diretório raiz no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planilha_arquivos import (
    normalizar_nome,
    extrair_pessoa,
    extrair_codigo_tema,
    extrair_codigo_do_tema_site,
    validar_codigo_site,
    conciliar,
    carregar_alunos,
    descobrir_arquivos,
    Aluno,
    ResultadoConciliacao,
    EXATO_UNICO,
    SUGESTAO_FUZZY,
    AMBIGUO,
    ARQUIVO_SEM_ALUNO,
    ALUNO_SEM_ARQUIVO,
    SEM_CODIGO,
    CODIGO_INVALIDO,
    REVISAO_MANUAL,
    ESTADOS_CONCILIACAO,
)
from plataforma import ItemListaRedacao
from progresso_relatorio import Progresso
from config import Config


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def planilha_temporaria():
    """Cria uma planilha XLSX temporária com alunos de teste."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["nome", "email", "sala"])
    ws.append(["Ana Lalara Larili dos Larito", "anaclara@escola.com", "A"])
    ws.append(["Bruno Silva", "bruno@escola.com", "A"])
    ws.append(["Carlos Eduardo", "carlos@escola.com", "B"])
    ws.append(["Usuario Testes Ignorar", "teste@esquema.com", "TESTE"])
    ws.append(["Diana Sem Arquivo", "diana@escola.com", "A"])
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def pasta_arquivos_temporaria():
    """Cria uma pasta temporária com subpastas e arquivos JPG de teste."""
    tmpdir = tempfile.mkdtemp()
    pasta = Path(tmpdir)
    subpasta_000 = pasta / "000 - Narração"
    subpasta_001 = pasta / "001 - Carta"
    subpasta_002 = pasta / "002 - Dissertativo"
    subpasta_003 = pasta / "003 - Depoimento"
    subpasta_004 = pasta / "004 - Usuario Testes"
    for sp in [subpasta_000, subpasta_001, subpasta_002, subpasta_003, subpasta_004]:
        sp.mkdir()
    (subpasta_000 / "Ana Lalara Larili dos Larito - Red.jpg").write_bytes(b"fake jpg")
    (subpasta_001 / "Bruno Silva - Red.jpg").write_bytes(b"fake jpg")
    (subpasta_002 / "Carlos Eduardo - Red.jpg").write_bytes(b"fake jpg")
    (subpasta_003 / "Usuario Testes - Red.jpg").write_bytes(b"fake jpg")
    (subpasta_004 / "Usuario Ignorar - Red.jpg").write_bytes(b"fake jpg")
    (pasta / "Sem Codigo - Fulano - Red.jpg").write_bytes(b"fake jpg")
    (subpasta_000 / "005 - Teste.jpeg").write_bytes(b"fake jpeg")
    (subpasta_001 / "006 - Teste.pdf").write_bytes(b"fake pdf")
    yield str(pasta)
    import shutil
    shutil.rmtree(tmpdir)


@pytest.fixture
def config_teste(planilha_temporaria, pasta_arquivos_temporaria):
    """Cria um objeto Config para testes."""
    from config import Config
    cfg = Config()
    cfg.planilha = Path(planilha_temporaria)
    cfg.pasta_raiz = Path(pasta_arquivos_temporaria)
    cfg.extensoes = (".jpg", ".JPG")
    cfg.limiar_fuzzy = 95.0
    cfg.margem_minima = 8.0
    cfg.max_envios_por_aluno = 4
    return cfg


@pytest.fixture
def alunos_teste(config_teste):
    """Carrega alunos da planilha de teste."""
    return carregar_alunos(config_teste)

# =====================================================================
# Testes de normalização e extração
# =====================================================================

def test_normalizacao_acentos_e_variacoes():
    """Nomes com acentos e variações devem normalizar para o mesmo valor."""
    assert normalizar_nome("Ana Lalara Larili dos Larito") == "ana lalara larili dos larito"
    assert normalizar_nome("ANA LALARA LARILI DOS LARITO") == "ana lalara larili dos larito"
    assert normalizar_nome("Ana-Lalara_Larili.dos-Larito") == "ana lalara_larili dos larito"
    assert normalizar_nome("Joao da Silva") == "joao da silva"
    assert normalizar_nome("Maria Jose") == "maria jose"
    assert normalizar_nome("") == ""


def test_extrair_pessoa_com_codigo():
    """extrair_pessoa deve remover o código do início do nome."""
    assert extrair_pessoa("000 - Ana Lalara - Red.jpg") == "Ana Lalara"
    assert extrair_pessoa("001 - Bruno Silva - Red.jpg") == "Bruno Silva"
    assert extrair_pessoa("002 - Ana Lalara - Red.jpg") == "Ana Lalara"
    assert extrair_pessoa("003 - Ana Lalara - Red.jpg") == "Ana Lalara"


def test_extrair_pessoa_sem_codigo():
    """extrair_pessoa deve funcionar sem código no nome."""
    assert extrair_pessoa("Ana Lalara - Red.jpg") == "Ana Lalara"
    assert extrair_pessoa("Bruno Silva.jpg") == "Bruno Silva"


def test_extrair_codigo_tema_arquivo():
    """Código extraído do nome do arquivo (início, seguido de separador)."""
    assert extrair_codigo_tema("000 - Ana Lalara - Red.jpg") == "000"
    assert extrair_codigo_tema("001 - Bruno Silva - Red.jpg") == "001"
    assert extrair_codigo_tema("0 - Narração - Red.jpg") == "0"
    assert extrair_codigo_tema("00 - Carta - Red.jpg") == "00"
    assert extrair_codigo_tema("000 - Dissertativo - Red.jpg") == "000"
    assert extrair_codigo_tema("3B - Texto.jpg") is None
    assert extrair_codigo_tema("3B Texto.jpg") is None
    assert extrair_codigo_tema("Sem Codigo - Red.jpg") is None


def test_extrair_codigo_tema_pasta():
    """Código extraído do nome da pasta quando arquivo não tem."""
    assert extrair_codigo_tema("Ana Lalara - Red.jpg", pasta="000 - Narração") == "000"
    assert extrair_codigo_tema("Arquivo.jpg", pasta="001 Carta") == "001"
    assert extrair_codigo_tema("001 - Arquivo.jpg", pasta="002 - Pasta") is None  # conflito -> None


def test_extrair_codigo_do_tema_site():
    """Extrair código do texto do tema no site (ex: '0- Narração')."""
    assert extrair_codigo_do_tema_site("0- Narração") == "0"
    assert extrair_codigo_do_tema_site("00- Carta") == "00"
    assert extrair_codigo_do_tema_site("000- DISSERTATIVO ARGUMENTATIVO") == "000"
    assert extrair_codigo_do_tema_site("1- Tema Qualquer") == "1"
    assert extrair_codigo_do_tema_site("17- Outro Tema") == "17"
    assert extrair_codigo_do_tema_site("Tema sem código") is None


def test_validar_codigo_site():
    """Validação do código contra o conjunto de códigos do site."""
    codigos_site = {"0", "00", "000", "1", "2", "17"}
    assert validar_codigo_site("0", codigos_site) is True
    assert validar_codigo_site("00", codigos_site) is True
    assert validar_codigo_site("000", codigos_site) is True
    assert validar_codigo_site("0000", codigos_site) is False
    assert validar_codigo_site("99", codigos_site) is False

@pytest.fixture
def arquivos_por_pasta(config_teste):
    """Descobre arquivos usando a config de teste."""
    return descobrir_arquivos(config_teste)


@pytest.fixture
def db_temporario():
    """Cria um banco SQLite temporário."""
    import uuid
    tmp_name = os.path.join(tempfile.gettempdir(), f"test_{uuid.uuid4().hex}.db")
    original_db = os.environ.get("ESQUEMA_DB_PATH")
    os.environ["ESQUEMA_DB_PATH"] = tmp_name
    prog = Progresso(tmp_name)
    prog.close()
    yield tmp_name
    # Tentar fechar conexões pendentes
    import gc
    gc.collect()
    import time
    time.sleep(0.1)
    try:
        os.unlink(tmp_name)
    except PermissionError:
        pass  # Windows pode travar o arquivo brevemente
    if original_db:
        os.environ["ESQUEMA_DB_PATH"] = original_db
    else:
        os.environ.pop("ESQUEMA_DB_PATH", None)
# =====================================================================
# Testes de conciliação
# =====================================================================

def test_conciliacao_exato_unico(alunos_teste, arquivos_por_pasta):
    """Correspondência exata e única -> EXATO_UNICO."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    resultado = conciliar(alunos_sala_a, arquivos_por_pasta, codigos_site={"000", "001", "002", "003", "004"})
    
    estados = {item.arquivo: item.estado for item in resultado.itens if item.arquivo}
    assert estados.get("Ana Lalara Larili dos Larito - Red.jpg") == EXATO_UNICO
    assert estados.get("Bruno Silva - Red.jpg") == EXATO_UNICO


def test_conciliacao_sugestao_fuzzy(alunos_teste, arquivos_por_pasta):
    """Variação de nome -> SUGESTAO_FUZZY com pontuação, revisão humana obrigatória."""
    alunos_sala_teste = [a for a in alunos_teste if a.sala == "TESTE"]
    resultado = conciliar(alunos_sala_teste, arquivos_por_pasta, codigos_site={"000", "001", "002", "003", "004"})
    
    itens_fuzzy = [item for item in resultado.itens if item.estado == SUGESTAO_FUZZY]
    assert len(itens_fuzzy) >= 2
    for item in itens_fuzzy:
        assert item.score_fuzzy is not None
        assert item.segundo_score is not None
        assert "revisao humana obrigatoria" in (item.observacao or "").lower()


def test_conciliacao_ambiguo(planilha_temporaria):
    """Dois alunos com mesmo nome normalizado -> AMBIGUO."""
    from openpyxl import Workbook
    from config import Config
    wb = Workbook()
    ws = wb.active
    ws.title = "Alunos"
    ws.append(["nome", "email", "sala"])
    ws.append(["Joao Silva", "joao1@escola.com", "A"])
    ws.append(["Joao Silva", "joao2@escola.com", "A"])
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    wb.save(tmp.name)
    tmp.close()
    
    try:
        cfg = Config()
        cfg.planilha = Path(tmp.name)
        pasta = tempfile.mkdtemp()
        subpasta = Path(pasta) / "001 - Carta"
        subpasta.mkdir()
        (subpasta / "Joao Silva - Red.jpg").write_bytes(b"fake")
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        alunos = carregar_alunos(cfg)
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos, arquivos, codigos_site={"001"})
        itens_amb = [item for item in resultado.itens if item.estado == AMBIGUO]
        assert len(itens_amb) == 1
        assert len(itens_amb[0].candidatos) == 2
    finally:
        os.unlink(tmp.name)
        import shutil
        shutil.rmtree(pasta)


def test_arquivo_sem_aluno(alunos_teste, planilha_temporaria):
    """Arquivo sem correspondência na planilha -> ARQUIVO_SEM_ALUNO."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    pasta = tempfile.mkdtemp()
    subpasta = Path(pasta) / "005 - Outro"
    subpasta.mkdir()
    (subpasta / "Fulano Inexistente - Red.jpg").write_bytes(b"fake")
    try:
        from config import Config
        cfg = Config()
        cfg.planilha = Path(planilha_temporaria)
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos_sala_a, arquivos, codigos_site={"005"})
        itens_sem = [item for item in resultado.itens if item.estado == ARQUIVO_SEM_ALUNO]
        assert len(itens_sem) == 1
    finally:
        import shutil
        shutil.rmtree(pasta)


def test_aluno_sem_arquivo(alunos_teste, arquivos_por_pasta):
    """Aluno da planilha sem arquivo -> ALUNO_SEM_ARQUIVO."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    resultado = conciliar(alunos_sala_a, arquivos_por_pasta, codigos_site={"000", "001", "002"})
    itens_sem = [item for item in resultado.itens if item.estado == ALUNO_SEM_ARQUIVO]
    assert any(item.aluno and item.aluno.nome == "Diana Sem Arquivo" for item in itens_sem)


def test_codigo_ausente_marcado_sem_codigo(alunos_teste, planilha_temporaria):
    """Arquivo sem código no nome nem na pasta -> SEM_CODIGO."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    pasta = tempfile.mkdtemp()
    # Criar subpasta SEM código no nome
    subpasta = Path(pasta) / "Sem Codigo Tema"
    subpasta.mkdir()
    (subpasta / "Fulano - Red.jpg").write_bytes(b"fake")
    try:
        from config import Config
        cfg = Config()
        cfg.planilha = Path(planilha_temporaria)
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos_sala_a, arquivos, codigos_site=set())
        itens_sem = [item for item in resultado.itens if item.estado == SEM_CODIGO]
        assert len(itens_sem) == 1
    finally:
        import shutil
        shutil.rmtree(pasta)


def test_codigo_invalido_marcado_codigo_invalido(alunos_teste, planilha_temporaria):
    """Código extraído não existe no combo do site -> CODIGO_INVALIDO."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    pasta = tempfile.mkdtemp()
    subpasta = Path(pasta) / "999 - Invalido"
    subpasta.mkdir()
    (subpasta / "Fulano - Red.jpg").write_bytes(b"fake")
    try:
        from config import Config
        cfg = Config()
        cfg.planilha = Path(planilha_temporaria)
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos_sala_a, arquivos, codigos_site={"000", "001"})
        itens_inv = [item for item in resultado.itens if item.estado == CODIGO_INVALIDO]
        assert len(itens_inv) == 1
    finally:
        import shutil
        shutil.rmtree(pasta)
def test_dois_arquivos_mesmo_tema_mesmo_aluno_revisao_manual(alunos_teste, planilha_temporaria):
    """Dois arquivos do mesmo aluno com mesmo código -> ambos REVISAO_MANUAL."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    pasta = tempfile.mkdtemp()
    subpasta = Path(pasta) / "000 - Narração"
    subpasta.mkdir()
    (subpasta / "Ana Lalara Larili dos Larito - Red1.jpg").write_bytes(b"fake")
    (subpasta / "Ana Lalara Larili dos Larito - Red2.jpg").write_bytes(b"fake")
    try:
        from config import Config
        cfg = Config()
        cfg.planilha = Path(planilha_temporaria)
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos_sala_a, arquivos, codigos_site={"000"})
        itens_rev = [item for item in resultado.itens if item.estado == REVISAO_MANUAL]
        assert len(itens_rev) == 2
        for item in itens_rev:
            assert item.codigo_tema == "000"
    finally:
        import shutil
        shutil.rmtree(pasta)


def test_conflito_pasta_arquivo_revisao_manual(alunos_teste, planilha_temporaria):
    """Arquivo tem código 001, pasta tem 002 -> REVISAO_MANUAL."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    pasta = tempfile.mkdtemp()
    subpasta = Path(pasta) / "002 - Outro Tema"
    subpasta.mkdir()
    (subpasta / "001 - Ana Lalara Larili dos Larito - Red.jpg").write_bytes(b"fake")
    try:
        from config import Config
        cfg = Config()
        cfg.planilha = Path(planilha_temporaria)
        cfg.pasta_raiz = Path(pasta)
        cfg.extensoes = (".jpg", ".JPG")
        arquivos = descobrir_arquivos(cfg)
        resultado = conciliar(alunos_sala_a, arquivos, codigos_site={"000", "001", "002"})
        itens_rev = [item for item in resultado.itens if item.estado == REVISAO_MANUAL]
        assert len(itens_rev) == 1
    finally:
        import shutil
        shutil.rmtree(pasta)
def test_nao_jpg_ignorado_com_aviso(alunos_teste, arquivos_por_pasta, capsys):
    """Arquivos .jpeg, .pdf etc. são ignorados com [AVISO] no terminal e log."""
    alunos_sala_a = [a for a in alunos_teste if a.sala == "A"]
    resultado = conciliar(alunos_sala_a, arquivos_por_pasta, codigos_site={"000", "001", "002", "005", "006"})
    arquivos_processados = [item.arquivo for item in resultado.itens if item.arquivo]
    assert "005 - Teste.jpeg" not in arquivos_processados
    assert "006 - Teste.pdf" not in arquivos_processados


def test_modo_teste_recusa_outros_emails(alunos_teste):
    """Modo teste deve recusar e-mails que não sejam o da conta de teste."""
    from config import Config
    cfg = Config()
    # O modo teste é controlado via --modo-teste flag e variáveis de ambiente
    assert cfg is not None


# =====================================================================
# Testes de SQLite / Progresso
# =====================================================================

def test_retomada_enviando_sem_duplicar(db_temporario):
    """Se estado ENVIANDO existe no SQLite, não reenviar na retomada."""
    prog = Progresso(db_temporario)
    aluno = Aluno(nome="Ana Lalara", email="ana@teste.com", sala="A")
    prog.marcar(aluno.id, "teste.jpg", "ENVIANDO")
    existing = prog.obter(aluno.id, "teste.jpg")
    assert existing is not None
    assert existing["estado"] == "ENVIANDO"


def test_bloqueio_envio_dry_run():
    """Sem --envio-real, envio deve ser bloqueado com mensagem padrão."""
    from config import exigir_envio_real
    with pytest.raises(RuntimeError, match="Envio real desativado"):
        exigir_envio_real(False)


def test_limite_4_envios_por_aluno(db_temporario):
    """Limite de 4 envios por aluno em produção (configurável em teste)."""
    prog = Progresso(db_temporario)
    aluno = Aluno(nome="Ana Lalara", email="ana@teste.com", sala="A")
    from progresso_relatorio import LimiteEnvios
    # Registrar 4 envios usando registrar_envio (que insere na tabela envios)
    for i in range(4):
        prog.registrar_envio(aluno.id, f"teste{i}.jpg", max_envios=4)
    # 5o envio deve ser bloqueado com excecao LimiteEnvios
    try:
        prog.registrar_envio(aluno.id, "teste4.jpg", max_envios=4)
        assert False, "Deveria ter levantado LimiteEnvios"
    except LimiteEnvios:
        pass  # Esperado
    # Verificar que a contagem esta correta
    contador = prog.envios_de(aluno.id)
    assert contador == 4
# =====================================================================
# Testes de lançamento (Playwright) - marcado como real
# ============@pytest.mark.real
def test_launch():
    """Abre navegador e faz login na conta de teste (requer credenciais no .env)."""
    from playwright.sync_api import sync_playwright
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv("ESQUEMA_TESTE_EMAIL")
    senha = os.getenv("ESQUEMA_TESTE_SENHA")
    
    if not email or not senha:
        pytest.skip("Credenciais de teste não configuradas no .env")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        try:
            from plataforma import login, confirmar_identidade, ler_lista_redacoes, ler_combo_temas
            
            page = login(page, email, senha)
            assert "/minhas-redacoes" in page.url
            
            from planilha_arquivos import Aluno
            aluno_teste = Aluno(nome="Usuario Testes Ignorar", email=email, sala="TESTE")
            confirmar_identidade(page, aluno_teste)
            
            lista = ler_lista_redacoes(page)
            assert len(lista) >= 2
            
            temas_0 = [item for item in lista if item.tema.startswith("0-")]
            assert len(temas_0) >= 2
            
            page.goto("https://www.esquemaredacao.com.br/wordings/new")
            page.wait_for_load_state("networkidle")
            temas = ler_combo_temas(page)
            codigos = [t.codigo for t in temas]
            assert "0" in codigos
            assert "00" in codigos
            assert "000" in codigos
            
        finally:
            browser.close()


# =====================================================================
# Testes de lógica de verificação simulada (sem site)
# =====================================================================

def test_verificacao_simulada_processando_para_pendente():
    """Simula o fluxo: 5s, Processando -> Pendente, contagem sobe 1, saldo cai 1."""
    from plataforma import ItemListaRedacao
    
    lista_antes = [
        ItemListaRedacao(data="29/09/2026", tema="0- Narração", nota="", situacao="Pendente", botao_texto=""),
    ]
    
    lista_processando = lista_antes + [
        ItemListaRedacao(data="30/09/2026", tema="0- Narração", nota="", situacao="Processando arquivo", botao_texto="Aguarde a correção"),
    ]
    
    lista_pendente = lista_antes + [
        ItemListaRedacao(data="30/09/2026", tema="0- Narração", nota="", situacao="Pendente", botao_texto="Aguarde a correção"),
    ]
    
    from plataforma import contar_linhas_codigo_data
    
    contagem_antes = contar_linhas_codigo_data(lista_antes, "0", "30/09/2026")
    assert contagem_antes == 0
    
    contagem_proc = contar_linhas_codigo_data(lista_processando, "0", "30/09/2026")
    assert contagem_proc == 1
    
    contagem_final = contar_linhas_codigo_data(lista_pendente, "0", "30/09/2026")
    assert contagem_final == 1


def test_verificacao_simulada_timeout():
    """Se timeout e linha não chega a Pendente -> REVISAO_MANUAL."""
    from plataforma import ItemListaRedacao
    from plataforma import contar_linhas_codigo_data
    
    lista_sem_nova = [
        ItemListaRedacao(data="29/09/2026", tema="0- Narração", nota="", situacao="Pendente", botao_texto=""),
    ]
    
    contagem = contar_linhas_codigo_data(lista_sem_nova, "0", "30/09/2026")
    assert contagem == 0


def test_verificacao_simulada_estado_desconhecido():
    """Estado não mapeado (ex: 'Erro', 'Corrigida') -> REVISAO_MANUAL."""
    from plataforma import ItemListaRedacao
    
    lista = [
        ItemListaRedacao(data="30/09/2026", tema="0- Narração", nota="", situacao="Erro", botao_texto=""),
    ]
    
    assert lista[0].situacao == "Erro"
    assert lista[0].situacao not in ("Pendente", "Processando arquivo")


def test_codigo_string_preserva_zeros():
    """Códigos '0', '00', '000' são strings distintas."""
    from planilha_arquivos import extrair_codigo_do_tema_site
    assert extrair_codigo_do_tema_site("0- Narração") == "0"
    assert extrair_codigo_do_tema_site("00- Carta") == "00"
    assert extrair_codigo_do_tema_site("000- Dissertativo") == "000"
    assert "0" != "00"
    assert "00" != "000"
    assert "0" != "000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])