with open('login.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''def confirmar_identidade(page: Page, aluno: Aluno) -> bool:
    """Confirma se o aluno logado corresponde ao esperado.
    
    Retorna True se confirmado, levanta IdentidadeDivergente se não."""
    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    verificar_dominio_autorizado(page)

    # Tentar ler nome/e-mail da página
    # Seletor pode variar - usar fallback
    try:
        nome_logado = page.locator(".usuario-nome, .user-name, [data-testid=user-name]").first.inner_text(timeout=5000)
    except PWTimeoutError:
        nome_logado = ""

    if aluno.nome.lower() not in nome_logado.lower() and aluno.email.lower() not in nome_logado.lower():
        raise IdentidadeDivergente(f"Identidade não confere. Esperado: {aluno.nome} ({aluno.email}). Encontrado: {nome_logado}")
    
    return True'''

new = '''def confirmar_identidade(page: Page, aluno: Aluno, modo_teste: bool = False) -> bool:
    """Confirma se o aluno logado corresponde ao esperado.

    Retorna True se confirmado, levanta IdentidadeDivergente se não.
    Fail-closed: se elemento não existir ou texto vier vazio, NÃO aceita vazio."""
    from planilha_arquivos import mascarar_email
    from normalizacao import normalizar_nome

    # Esperar elemento do menu do usuário (topo da página) - até 10s
    # Seletor que funcionava na Etapa E: texto exato do nome
    nome_locator = page.locator(f"text={aluno.nome}").first
    encontrado = False
    texto_visivel = ""
    qtd_casados = 0

    try:
        nome_locator.wait_for(state="visible", timeout=10000)
        encontrado = True
        qtd_casados = nome_locator.count()
        texto_visivel = (nome_locator.text_content() or "").strip()
    except PWTimeoutError:
        # Fallback: tentar seletor genérico do menu
        fallback_locator = page.locator("a[href='#'] >> text=Testes").first
        try:
            fallback_locator.wait_for(state="visible", timeout=5000)
            encontrado = True
            qtd_casados = fallback_locator.count()
            texto_visivel = (fallback_locator.text_content() or "").strip()
        except PWTimeoutError:
            pass

    if not encontrado or not texto_visivel:
        # Diagnóstico seguro (sem e-mail, sem senha)
        url_sem_query = page.url.split("?")[0]
        diagnostico = (
            f"URL: {url_sem_query} | "
            f"elemento_encontrado: {encontrado} | "
            f"qtd_casados: {qtd_casados} | "
            f"texto_menu: '{texto_visivel}'"
        )
        email_mascarado = mascarar_email(aluno.email)
        raise IdentidadeDivergente(
            f"Identidade não confere. Esperado: {aluno.nome} ({email_mascarado}). "
            f"Encontrado: VAZIO. Diagnóstico: {diagnostico}"
        )

    # Comparação normalizada (acentos, maiúsculas, pontuação)
    nome_normalizado = normalizar_nome(texto_visivel)
    esperado_normalizado = normalizar_nome(aluno.nome)

    if nome_normalizado != esperado_normalizado:
        url_sem_query = page.url.split("?")[0]
        diagnostico = (
            f"URL: {url_sem_query} | "
            f"elemento_encontrado: {encontrado} | "
            f"qtd_casados: {qtd_casados} | "
            f"texto_menu: '{texto_visivel}'"
        )
        email_mascarado = mascarar_email(aluno.email)
        raise IdentidadeDivergente(
            f"Identidade não confere. Esperado: {aluno.nome} ({email_mascarado}). "
            f"Encontrado (normalizado): '{nome_normalizado}' != '{esperado_normalizado}'. "
            f"Diagnóstico: {diagnostico}"
        )

    # Em modo teste, salvar snapshot HTML se identidade falhou (aqui passou)
    if modo_teste:
        try:
            from datetime import datetime
            from pathlib import Path
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            diag_dir = Path("diagnosticos")
            diag_dir.mkdir(exist_ok=True)
            (diag_dir / f"identidade_{ts}.html").write_text(page.content(), encoding="utf-8")
        except Exception:
            pass  # snapshot é best-effort, não quebrar o fluxo

    return True'''

if old in content:
    content = content.replace(old, new)
    with open('login.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('REPLACED OK')
else:
    print('OLD NOT FOUND')
    print('Searching for function...')
    idx = content.find('def confirmar_identidade')
    if idx >= 0:
        print('Found at', idx)
        print(repr(content[idx:idx+200]))