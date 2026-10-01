import pathlib

content = pathlib.Path("planilha_arquivos.py").read_text(encoding="utf-8")

old = '''def extrair_codigo_tema(nome_arquivo: str, pasta: str = "") -> str | None:
    """
    Extrai o código do tema do nome do arquivo (sem extensão) OU do nome da pasta.
    Padrão: número no início seguido de separador (espaço, _, ., -).
    Retorna o código como string (preserva zeros à esquerda) ou None se não encontrado.
    """
    import re
    padrao = re.compile(r"^\s*(\d+)(?=[\s_.-]|$)")

    # Primeiro tenta no nome do arquivo (sem extensão)
    stem = Path(nome_arquivo).stem
    match = padrao.match(stem)
    if match:
        return match.group(1)

    # Depois tenta no nome da pasta
    if pasta:
        match = padrao.match(pasta)
        if match:
            return match.group(1)

    return None'''

new = '''def extrair_codigo_tema(nome_arquivo: str, pasta: str = "") -> str | None:
    """
    Extrai o código do tema do nome do arquivo (sem extensão) OU do nome da pasta.
    Padrão: número no início seguido de separador (espaço, _, ., -).
    Retorna o código como string (preserva zeros à esquerda) ou None se não encontrado.
    """
    import re
    padrao = re.compile(r"^\s*(\d+)(?=[\s_.-]|$)")

    # Primeiro tenta no nome do arquivo (sem extensão)
    stem = Path(nome_arquivo).stem
    match = padrao.match(stem)
    if match:
        return match.group(1)

    # Depois tenta no nome da pasta
    if pasta:
        match = padrao.match(pasta)
        if match:
            return match.group(1)

    return None


def extrair_codigo_do_tema_site(texto_tema: str) -> str | None:
    """
    Extrai o código do tema a partir do texto do combo do site.
    Exemplos: "0- Narração" → "0", "00- CARTA" → "00", "000- DISSERTATIVO" → "000"
    Padrão: número no início seguido de " - " ou espaço ou fim.
    """
    import re
    padrao = re.compile(r"^\s*(\d+)(?=\s*-|\s|$)")
    match = padrao.match(texto_tema)
    if match:
        return match.group(1)
    return None'''

content = content.replace(old, new)
pathlib.Path("planilha_arquivos.py").write_text(content, encoding="utf-8")
print("planilha_arquivos.py updated")