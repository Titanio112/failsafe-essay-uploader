# ─── Navegação formulário ────────────────────────────────────

def abrir_formulario_envio(page: Page) -> Page:
    """Vai para /wordings/new (Enviar redação)."""
    page.click('a:has-text("Enviar redação")')
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)
    if "wordings/new" not in page.url:
        raise RuntimeError(f"URL inesperada ao abrir formulário: {page.url}")
    return page


def ler_combo_temas(page: Page) -> list[TemaCombo]:
    """Lê as opções do combo 'Informe o tema da redação'."""
    combo = page.get_by_label("Informe o tema da redação")
    combo.click()
    page.wait_for_timeout(300)
    
    temas = []
    options = page.get_by_role("option").all()
    for opt in options:
        texto = opt.text_content() or ""
        if texto.strip():
            from planilha_arquivos import extrair_codigo_do_tema_site
            codigo = extrair_codigo_do_tema_site(texto)
            if codigo:
                temas.append(TemaCombo(codigo=codigo, texto_completo=texto.strip()))
    return temas


def selecionar_tema_por_codigo(page: Page, codigo: str) -> bool:
    """Seleciona a opção do combo cujo código seja exatamente igual."""
    temas = ler_combo_temas(page)
    for tema in temas:
        if tema.codigo == codigo:
            page.get_by_role("option", name=tema.texto_completo).click()
            page.wait_for_timeout(300)
            return True
    return False


def selecionar_criterio(page: Page, criterio: str = "ENEM") -> None:
    """Seleciona o critério de avaliação."""
    combo = page.get_by_label("Selecione um critério de avaliação")
    combo.click()
    page.get_by_role("option", name=criterio).click()
    page.wait_for_timeout(300)


# ─── Upload ──────────────────────────────────────────────────

def anexar_arquivo(page: Page, arquivo: Path) -> None:
    """Anexa o arquivo JPG no input de arquivo."""
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(arquivo))
    page.wait_for_timeout(1000)


def aguardar_upload_aceito(page: Page, timeout_segundos: int = 120) -> bool:
    """
    Aguarda o botão 'Enviar resposta' ficar habilitado (upload aceito).
    """
    import time
    inicio = time.monotonic()
    while time.monotonic() - inicio < timeout_segundos:
        try:
            btn = page.get_by_role("button", name="Enviar resposta")
            if btn.is_enabled():
                return True
        except PWTimeoutError:
            pass
        page.wait_for_timeout(2000)
    return False


def clicar_enviar(page: Page) -> None:
    """Clica no botão final 'Enviar resposta' uma única vez."""
    btn = page.get_by_role("button", name="Enviar resposta")
    btn.click()
    page.wait_for_load_state("networkidle")


# ─── Verificação pós-envio ───────────────────────────────────

def aguardar_confirmacao(
    page: Page,
    codigo: str,
    data_hoje: str,
    contagem_antes: int,
    saldo_antes: int,
    timeout_segundos: int = 120,
    poll_segundos: int = 5,
) -> tuple[bool, str]:
    """
    Polling em /minhas-redacoes até confirmar envio ou timeout.
    Retorna (sucesso, detalhe).
    """
    import time
    inicio = time.monotonic()
    tentativa = 0
    
    while time.monotonic() - inicio < timeout_segundos:
        tentativa += 1
        page.wait_for_timeout(poll_segundos * 1000)
        page.reload()
        page.wait_for_load_state("networkidle")
        
        lista = ler_lista_redacoes(page)
        contagem_depois = contar_linhas_codigo_data(lista, codigo, data_hoje)
        saldo_depois = ler_saldo_creditos(page)
        
        # Log da tentativa
        detalhe = f"Tentativa {tentativa}: contagem={contagem_depois} (antes={contagem_antes}), saldo={saldo_depois} (antes={saldo_antes})"
        print(detalhe)
        
        if contagem_depois == contagem_antes + 1:
            # Verifica se a nova linha está "Pendente"
            for item in lista:
                import re
                match = re.match(r"^\s*(\d+)(?=\s*-|\s|$)", item.tema)
                if match and match.group(1) == codigo and item.data == data_hoje:
                    if item.situacao == "Pendente":
                        if saldo_depois == saldo_antes - 1:
                            return True, f"{detalhe} → ENVIADO (Pendente, saldo -1)"
                        else:
                            return False, f"{detalhe} → REVISAO_MANUAL (saldo não caiu 1)"
                    elif item.situacao == "Processando arquivo":
                        # Ainda processando, continua o polling
                        continue
                    else:
                        return False, f"{detalhe} → REVISAO_MANUAL (estado='{item.situacao}')"
        
        elif contagem_depois > contagem_antes + 1:
            return False, f"{detalhe} → REVISAO_MANUAL (contagem subiu mais que 1)"
    
    return False, f"Timeout {timeout_segundos}s: contagem não subiu ou linha não chegou a Pendente"


# ─── API legada ──────────────────────────────────────────────

def enviar_redacao(
    cfg: Config,
    aluno: Aluno,
    arquivo: Path,
    *,
    envio_real: bool = False,
) -> None:
    """API legada mantida para compatibilidade com testes."""
    exigir_envio_real(envio_real)
    raise NotImplementedError(
        "Use as funções de Fase 3 via main.py com Progresso e autorização completa."
    )


def login_permissao(page: Page, email: str, password: str) -> Page:
    """API legada mantida para compatibilidade com scripts de diagnóstico."""
    return login(page, email, password)