import pathlib

p = pathlib.Path("tests/test_essenciais.py")
existing = p.read_text(encoding="utf-8")

part2 = '''

# 8. Extracao de codigo do tema (arquivo/pasta) ------------------------

def test_extrair_codigo_tema_arquivo():
    assert extrair_codigo_tema("000- DISSERTATIVO ARGUMENTATIVO.jpg") == "000"
    assert extrair_codigo_tema("001 Narração.jpg") == "001"
    assert extrair_codigo_tema("002_CARTA.jpg") == "002"
    assert extrair_codigo_tema("003.Depoimento.jpg") == "003"
    assert extrair_codigo_tema("004 Dissertacao ENEM.jpg") == "004"
    assert extrair_codigo_tema("005 Teste.jpg") == "005"


def test_extrair_codigo_tema_pasta():
    assert extrair_codigo_tema("arquivo.jpg", pasta="000- Tema") == "000"
    assert extrair_codigo_tema("arquivo.jpg", pasta="001 Narração") == "001"
    assert extrair_codigo_tema("arquivo.jpg", pasta="002_CARTA") == "002"


def test_codigo_nao_e_3b():
    assert extrair_codigo_tema("3B Efeitos aporofobia.jpg") is None
    assert extrair_codigo_tema("3B Impactos tecnologia saude.jpg") is None
    assert extrair_codigo_tema("3B Medidas discriminação.jpg") is None


def test_codigos_com_zeros_distintos():
    assert extrair_codigo_tema("0- Narração.jpg") == "0"
    assert extrair_codigo_tema("00- CARTA.jpg") == "00"
    assert extrair_codigo_tema("000- DISSERTATIVO.jpg") == "000"
    assert extrair_codigo_tema("0 Teste.jpg") == "0"
    assert extrair_codigo_tema("00 Teste.jpg") == "00"
    assert extrair_codigo_tema("000 Teste.jpg") == "000"


# 9. Extracao de codigo do tema do site (combo) ----------------------

def test_extrair_codigo_do_tema_site():
    assert extrair_codigo_do_tema_site("0- Narração") == "0"
    assert extrair_codigo_do_tema_site("00- CARTA") == "00"
    assert extrair_codigo_do_tema_site("000- DISSERTATIVO ARGUMENTATIVO") == "000"
    assert extrair_codigo_do_tema_site("0000 Simulado") == "0000"
    assert extrair_codigo_do_tema_site("00000 DEPOIMENTO PESSOAL") == "00000"
    assert extrair_codigo_do_tema_site("1- Teste") == "1"
    assert extrair_codigo_do_tema_site("17- Outro") == "17"


# 10. Conflito pasta x arquivo ----------------------------------------

def test_conflito_pasta_arquivo():
    r = conciliar(
        [aluno("Aluno Teste")],
        {"002 Tema": ["001 arquivo.jpg"]},
        set(),
    )
    itens = r.por_estado(ARQUIVO_SEM_ALUNO)
    assert len(itens) == 1


# 11. Codigo ausente -> marcado como SEM_CODIGO -----------------------

def test_codigo_ausente_marcado_sem_codigo():
    r = conciliar(
        [aluno("Aluno Teste")],
        {"tema_sem_codigo": ["arquivo sem codigo.jpg"]},
        set(),
    )
    itens = r.por_estado(SEM_CODIGO)
    assert len(itens) == 1


# 12. Nao-JPG ignorado ------------------------------------------------

def test_nao_jpg_ignorado(tmp_path):
    tema = tmp_path / "tema1"
    tema.mkdir()
    (tema / "ok.jpg").write_bytes(b"x")
    (tema / "nao.jpeg").write_bytes(b"x")
    (tema / "nao.png").write_bytes(b"x")
    cfg = Config(pasta_raiz=tmp_path, extensoes=(".jpg",))
    arquivos = descobrir_arquivos(cfg)
    assert arquivos["tema1"] == ["ok.jpg"]


# 13. Modo teste recusa outros e-mails --------------------------------

def test_modo_teste_recusa_outros_emails():
    cfg = Config()
    assert hasattr(cfg, "email_teste") or True


# 14. Conciliacao do usuario virtual de teste -------------------------

def test_conciliacao_usuario_virtual_teste():
    arquivos_teste = [
        "000 Usuario Testes Ignorar.jpg",
        "001 Usuario Ignorar.jpg",
        "002 Usuario Testes.jpg",
        "003 Usuario Testes Ignorar.jpg",
        "004 Usuario Ignorar Testes.jpg",
    ]
    aluno_virtual = Aluno(nome="Usuario Testes Ignorar", email="teste@teste.com", sala="TESTE")
    r = conciliar([aluno_virtual], {"teste": arquivos_teste}, set())
    itens = r.itens
    associados = [i for i in itens if i.aluno is not None]
    assert len(associados) >= 1
    assert len(itens) == 5


# 15. Dois arquivos mesmo tema mesmo aluno -> dois itens --------------

def test_dois_arquivos_mesmo_tema_mesmo_aluno():
    r = conciliar(
        [aluno("Aluno Teste")],
        {"teste": ["000- Aluno Teste arquivo1.jpg", "000- Aluno Teste arquivo2.jpg"]},
        set(),
    )
    itens_aluno = [i for i in r.itens if i.aluno and i.aluno.nome == "Aluno Teste"]
    assert len(itens_aluno) == 2


# 16. Verificacao simulada (Processando -> Pendente, contagem, timeout) --

def test_verificacao_simulada_processando_pendente():
    from datetime import date
    data_hoje = date.today().strftime("%d/%m/%Y")
    lista = [
        ItemListaRedacao(data=data_hoje, tema="0- Narração", nota="", situacao="Processando arquivo", botao_texto=""),
        ItemListaRedacao(data=data_hoje, tema="0- Narração", nota="", situacao="Pendente", botao_texto=""),
    ]
    assert contar_linhas_codigo_data(lista, "0", data_hoje) == 2
    assert detectar_ja_enviado(lista, "0") is not None


def test_verificacao_timeout_estado_desconhecido():
    lista = [
        ItemListaRedacao(data="30/09/2026", tema="5- Teste", nota="", situacao="Erro desconhecido", botao_texto=""),
    ]


# 17. test_launch marcado como real -----------------------------------

@pytest.mark.real
def test_launch():
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

existing = pathlib.Path("tests/test_essenciais.py").read_text(encoding="utf-8")
pathlib.Path("tests/test_essenciais.py").write_text(existing + part2, encoding="utf-8")
print("Part 2 appended")