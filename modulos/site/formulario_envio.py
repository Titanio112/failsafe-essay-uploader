"""Abertura de formulário, seleção de tema/critério, anexo e upload."""

from __future__ import annotations
from dataclasses import dataclass

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from modulos.site.login import DOMINIO_ESPERADO, verificar_dominio_autorizado


@dataclass
class TemaCombo:
    """Uma opção do combo 'Informe o tema da redação'."""
    codigo: str
    texto_completo: str


def abrir_formulario_envio(page: Page) -> None:
    """Abre o formulário de envio de redação."""
    page.goto(f"https://{DOMINIO_ESPERADO}/wordings/new", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)


def ler_combo_temas(page: Page) -> list[tuple[str, str]]:
    """Lê as opções do combo 'Informe o tema da redação'.
    
    Retorna lista de (codigo, texto_completo)."""
    # Aguardar combo carregar - seletor real do site
    page.wait_for_selector("select[name='wording[wording_proposal_id]']", timeout=10000)
    
    combo = page.locator("select[name='wording[wording_proposal_id]']").first
    opcoes = combo.locator("option").all()
    
    resultado = []
    for opcao in opcoes:
        texto = opcao.inner_text().strip()
        if texto and not texto.lower().startswith("selecione"):
            import re
            match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", texto)
            if match:
                codigo = match.group(1)
                resultado.append((codigo, texto))
    
    return resultado


def selecionar_tema_por_codigo(page: Page, codigo: str, codigos_site: list[str] = None) -> bool:
    """Seleciona o tema no combo pelo código exato (string).
    
    Se codigos_site for fornecido, valida que o código existe e é único.
    Retorna True se conseguiu selecionar pelo texto da opção; False se não.
    Sem fallback por value: o value do combo é o id da proposta, não o código.
    
    Levanta RuntimeError se código duplicado ou inexistente no combo."""
    # Validar códigos do site se fornecidos
    if codigos_site is not None:
        count = codigos_site.count(codigo)
        if count == 0:
            raise RuntimeError(f"Código {codigo} não existe no combo do site (REVISAO_MANUAL)")
        if count > 1:
            raise RuntimeError(f"Código {codigo} aparece {count}x no combo do site (SIMULADO/REVISAO_MANUAL)")
    
    # Primeiro obter o texto completo do tema para usar como label
    try:
        temas = ler_combo_temas(page)
        for tema in temas:
            # tema pode ser tupla (codigo, texto) ou objeto TemaCombo com .codigo/.texto_completo
            if hasattr(tema, 'codigo'):
                cod = tema.codigo
                texto_completo = tema.texto_completo
            else:
                cod, texto_completo = tema
            if cod == codigo:
                # Selecionar por label (texto visível)
                combo = page.get_by_label("Informe o tema da redação")
                combo.select_option(label=texto_completo)
                return True
    except Exception:
        pass

    return False


def selecionar_criterio(page: Page) -> None:
    """Seleciona o critério ENEM no formulário."""
    # Critério é um select: select[name="wording[folder_id]"]
    # value="1" = ENEM, value="2" = FUVEST, value="3" = UNICAMP
    try:
        page.select_option("select[name='wording[folder_id]']", value="1", timeout=3000)
    except PWTimeoutError:
        pass  # Critério pode já estar selecionado ou ser padrão


def anexar_arquivo(page: Page, caminho_arquivo: str) -> None:
    """Anexa o arquivo JPG no input file."""
    input_file = page.locator("input[type='file'][name=\"wording[pages_attributes][0][file]\"]").first
    input_file.set_input_files(caminho_arquivo)


def aguardar_upload_aceito(page: Page, timeout_segundos: int = 30) -> bool:
    """Aguarda o upload ser aceito — sinal real: .progress .bar visível, width=100%, texto 'Arquivo carregado'.

    Retorna True se upload aceito, False se timeout."""
    from playwright.sync_api import TimeoutError as PWTimeoutError
    import time

    progress_bar = page.locator(".progress .bar").first

    try:
        # 1. Aguardar elemento ficar visível
        progress_bar.wait_for(state="visible", timeout=timeout_segundos * 1000)
    except PWTimeoutError:
        return False

    # 2. Ler style e text_content
    style = progress_bar.get_attribute("style") or ""
    texto = progress_bar.text_content() or ""

    # 3. Confirmar sinal: visível + width:100% no style + "Arquivo carregado" no texto
    if not progress_bar.is_visible():
        return False

    style_lower = style.lower()
    width_ok = "width: 100%" in style_lower or "width:100%" in style_lower
    texto_ok = "arquivo carregado" in texto.lower()

    if width_ok and texto_ok:
        return True

    # 4. If not complete yet, poll for up to timeout
    start = time.time()
    while time.time() - start < timeout_segundos:
        style = progress_bar.get_attribute("style") or ""
        texto = progress_bar.text_content() or ""

        style_lower = style.lower()
        width_ok = "width: 100%" in style_lower or "width:100%" in style_lower
        texto_ok = "arquivo carregado" in texto.lower()

        if width_ok and texto_ok:
            return True
        
        time.sleep(1)

    return False
