"""Abertura de formulário, seleção de tema/critério, anexo e upload."""

from __future__ import annotations

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config import Config
from excecoes import CaptchaOuBloqueio, UploadNaoConfirmado


def verificar_dominio_autorizado(page: Page) -> None:
    from login import DOMINIO_ESPERADO
    dominio_atual = page.url.split("/")[2] if len(page.url.split("/")) > 2 else ""
    if DOMINIO_ESPERADO not in dominio_atual:
        raise CaptchaOuBloqueio(f"Domínio inesperado: {dominio_atual}. Esperado: {DOMINIO_ESPERADO}")


def abrir_formulario_envio(page: Page) -> None:
    """Abre o formulário de envio de redação."""
    page.goto(f"https://{DOMINIO_ESPERADO}/wordings/new", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)


def ler_combo_temas(page: Page) -> list[tuple[str, str]]:
    """Lê as opções do combo 'Informe o tema da redação'.
    
    Retorna lista de (codigo, texto_completo)."""
    # Aguardar combo carregar
    page.wait_for_selector("select[name='redacao[tema_id]'], select#tema_id, select[name='tema']", timeout=10000)
    
    combo = page.locator("select[name='redacao[tema_id]'], select#tema_id, select[name='tema']").first
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
    Retorna True se conseguiu selecionar.
    
    Levanta RuntimeError se código duplicado ou inexistente no combo."""
    # Validar códigos do site se fornecidos
    if codigos_site is not None:
        count = codigos_site.count(codigo)
        if count == 0:
            raise RuntimeError(f"Código {codigo} não existe no combo do site (REVISAO_MANUAL)")
        if count > 1:
            raise RuntimeError(f"Código {codigo} aparece {count}x no combo do site (SIMULADO/REVISAO_MANUAL)")
    
    # Import aqui para permitir mock nos testes
    import plataforma
    
    # Primeiro obter o texto completo do tema para usar como label
    try:
        temas = plataforma.ler_combo_temas(page)
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
    
    # Fallback: tentar por value direto no select
    try:
        combo = page.locator("select[name='redacao[tema_id]'], select#tema_id, select[name='tema']").first
        combo.select_option(value=codigo)
        return True
    except Exception:
        pass
    
    return False


def selecionar_criterio(page: Page) -> None:
    """Seleciona o critério ENEM no formulário."""
    # Procurar radio/select para ENEM
    try:
        page.check("input[value='enem'], input[name='redacao[criterio]'][value='enem']", timeout=3000)
    except PWTimeoutError:
        try:
            page.select_option("select[name='redacao[criterio]']", value="enem", timeout=3000)
        except PWTimeoutError:
            pass  # Critério pode já estar selecionado ou ser padrão


def anexar_arquivo(page: Page, caminho_arquivo: str) -> None:
    """Anexa o arquivo JPG no input file."""
    input_file = page.locator("input[type='file'][name='redacao[arquivo]'], input[type='file'][accept*='image']").first
    input_file.set_input_files(caminho_arquivo)


def aguardar_upload_aceito(page: Page, timeout_segundos: int = 30) -> bool:
    """Aguarda o upload ser aceito (botão 'Enviar resposta' habilita).
    
    Retorna True se upload aceito, False se timeout."""
    import time
    inicio = time.time()
    
    while time.time() - inicio < timeout_segundos:
        try:
            # Verificar se botão de enviar está habilitado
            btn_enviar = page.locator("button:has-text('Enviar resposta'), input[type='submit'][value*='Enviar']").first
            if btn_enviar.is_enabled():
                return True
            
            # Verificar mensagem de sucesso
            sucesso = page.locator(".upload-sucesso, .alert-success, [data-testid=upload-ok]").first
            if sucesso.is_visible():
                return True
        except Exception:
            pass
        
        time.sleep(1)
    
    return False