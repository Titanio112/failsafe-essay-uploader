"""Leitura de lista de redações, saldo e verificação de duplicidade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from planilha_arquivos import normalizar_nome
from excecoes import CaptchaOuBloqueio
from login import DOMINIO_ESPERADO


@dataclass
class ItemListaRedacao:
    codigo: str = ""
    tema: str = ""
    data: str = ""
    situacao: str = ""
    nota: str = ""
    botao_texto: str = ""


def verificar_dominio_autorizado(page: Page) -> None:
    dominio_atual = page.url.split("/")[2] if len(page.url.split("/")) > 2 else ""
    if DOMINIO_ESPERADO not in dominio_atual:
        raise CaptchaOuBloqueio(f"Domínio inesperado: {dominio_atual}. Esperado: {DOMINIO_ESPERADO}")


def ler_saldo_creditos(page: Page) -> int | None:
    """Lê o saldo de créditos da conta logada.
    
    Retorna o número de créditos como int, ou None se não conseguir ler.
    Não retorna 0 para não mascarar erros de leitura."""
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Tentar encontrar saldo na página - padrão observado: "Você tem 999 crédito(s)"
    import re
    try:
        # Procurar no texto completo da página
        full_text = page.locator("body").inner_text(timeout=5000)
        # Padrão: "Você tem 999 crédito(s)" ou "999 crédito(s)"
        match = re.search(r"Você\s+tem\s+(\d+)\s+crédito", full_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r"(\d+)\s+crédito\(s\)", full_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Fallback: qualquer número seguido de "crédito"
        match = re.search(r"(\d+)\s+crédito", full_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except PWTimeoutError:
        pass
    
    return None  # Não conseguiu ler - fail closed


def ler_lista_redacoes(page: Page) -> list[ItemListaRedacao]:
    """Lê a lista de redações do aluno em /minhas-redacoes."""
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    itens = []
    try:
        linhas = page.locator("table tbody tr, .redacao-item, [data-testid=redacao-row]").all()
        for linha in linhas:
            try:
                # Extrair células
                celulas = linha.locator("td, .cell").all()
                if len(celulas) >= 3:
                    tema_texto = celulas[1].inner_text()
                    data_texto = celulas[2].inner_text()
                    situacao_texto = celulas[3].inner_text() if len(celulas) > 3 else ""
                    nota_texto = celulas[4].inner_text() if len(celulas) > 4 else ""
                    botao_texto = celulas[5].inner_text() if len(celulas) > 5 else ""

                    # Extrair código do tema
                    import re
                    match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", tema_texto)
                    codigo = match.group(1) if match else ""

                    itens.append(ItemListaRedacao(
                        codigo=codigo,
                        tema=tema_texto.strip(),
                        data=data_texto.strip(),
                        situacao=situacao_texto.strip(),
                        nota=nota_texto.strip(),
                        botao_texto=botao_texto.strip()
                    ))
            except Exception:
                continue
    except PWTimeoutError:
        pass

    return itens


def contar_linhas_codigo_data(lista: list[ItemListaRedacao], codigo: str, data: str) -> int:
    """Conta quantas linhas na lista têm o código e data especificados.
    
    Verifica tanto o campo codigo quanto extrai do campo tema."""
    import re
    count = 0
    for item in lista:
        if item.data != data:
            continue
        # Verificar campo codigo
        if item.codigo == codigo:
            count += 1
            continue
        # Extrair código do tema se não estiver no campo codigo
        match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
        if match and match.group(1) == codigo:
            count += 1
    return count


def ler_lista_redacoes_html(html: str) -> list[ItemListaRedacao]:
    """Parseia HTML da página /minhas-redacoes e retorna lista de itens."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    itens = []
    # Procurar tabela
    tabela = soup.find('table')
    if not tabela:
        return itens
    
    tbody = tabela.find('tbody')
    if not tbody:
        return itens
    
    linhas = tbody.find_all('tr')
    for linha in linhas:
        celulas = linha.find_all('td')
        if len(celulas) < 3:
            continue
        
        data = celulas[0].get_text(strip=True)
        tema = celulas[1].get_text(strip=True)
        
        # A estrutura pode variar
        # Caso 1: data, tema, (vazia), situacao, nota, botao
        # Caso 2: data, tema, nota, situacao, botao
        # Caso 3: data, tema, situacao
        
        situacao = ""
        nota = ""
        botao_texto = ""
        
        if len(celulas) >= 4 and celulas[2].get_text(strip=True) == "":
            # Caso 1: 3ª célula vazia
            situacao = celulas[3].get_text(strip=True) if len(celulas) > 3 else ""
            nota = celulas[4].get_text(strip=True) if len(celulas) > 4 else ""
            botao_texto = celulas[5].get_text(strip=True) if len(celulas) > 5 else ""
        elif len(celulas) >= 4:
            # Caso 2: 3ª célula tem nota
            nota = celulas[2].get_text(strip=True)
            situacao = celulas[3].get_text(strip=True)
            botao_texto = celulas[4].get_text(strip=True) if len(celulas) > 4 else ""
        else:
            # Caso 3: apenas 3 células
            situacao = celulas[2].get_text(strip=True) if len(celulas) > 2 else ""
        
        # Extrair código
        import re
        match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", tema)
        codigo = match.group(1) if match else ""
        
        itens.append(ItemListaRedacao(
            codigo=codigo,
            tema=tema,
            data=data,
            situacao=situacao,
            nota=nota,
            botao_texto=botao_texto
        ))
    
    return itens


def verificar_duplicidade(lista_redacoes: list[ItemListaRedacao], codigo_tema: str, data_hoje: str | None = None) -> tuple[str, Optional[str]]:
    """Verifica se já existe redação com esse código na lista.
    
    Retorna: (estado, data_envio) onde estado pode ser:
    - "JA_ENVIADO": já enviado HOJE (com data)
    - "OK": não encontrado hoje, pode prosseguir
    - "REVISAO_MANUAL": lista ilegível/sem dados
    """
    from datetime import datetime
    if data_hoje is None:
        data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    if not lista_redacoes:
        return "REVISAO_MANUAL", None
    
    # Verificar se a lista tem dados válidos (pelo menos um item com tema e data)
    tem_dados_validos = any(item.tema.strip() and item.data.strip() for item in lista_redacoes)
    if not tem_dados_validos:
        return "REVISAO_MANUAL", None
    
    for item in lista_redacoes:
        # Extrair código do tema
        import re
        match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
        item_codigo = match.group(1) if match else item.codigo
        
        if item_codigo == codigo_tema:
            # Verificar se a data é de HOJE
            item_data = item.data.strip()
            if item_data == data_hoje:
                if item.situacao.lower() == "cancelada":
                    return "OK", None
                return "JA_ENVIADO", item.data
            # Mesmo código mas data diferente - NÃO é duplicata
            continue
    
    return "OK", None


def detectar_ja_enviado(lista_redacoes: list[ItemListaRedacao], codigo: str, data_hoje: str | None = None) -> tuple[bool, str]:
    """Verifica se já foi enviado HOJE - retorna (True, data) ou (False, '')."""
    from datetime import datetime
    if data_hoje is None:
        data_hoje = datetime.now().strftime("%d/%m/%Y")
    estado, data = verificar_duplicidade(lista_redacoes, codigo, data_hoje)
    if estado == "JA_ENVIADO":
        return True, data or ""
    return False, ""