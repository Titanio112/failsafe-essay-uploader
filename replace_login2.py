with open('login.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'def confirmar_identidade(page: Page, aluno: Aluno) -> bool:\n    """Confirma se o aluno logado corresponde ao esperado.\n    \n    Retorna True se confirmado, levanta IdentidadeDivergente se n\u00e3o."""\n    page.goto(f"https://{DOMINIO_ESPERADO}/minhas-redacoes", wait_until="domcontentloaded")\n    page.wait_for_load_state("networkidle")\n    verificar_dominio_autorizado(page)\n\n    # Tentar ler nome/e-mail da p\u00e1gina\n    # Seletor pode variar - usar fallback\n    try:\n        nome_logado = page.locator(".usuario-nome, .user-name, [data-testid=user-name]").first.inner_text(timeout=5000)\n    except PWTimeoutError:\n        nome_logado = ""\n\n    if aluno.nome.lower() not in nome_logado.lower() and aluno.email.lower() not in nome_logado.lower():\n        raise IdentidadeDivergente(f"Identidade n\u00e3o confere. Esperado: {aluno.nome} ({aluno.email}). Encontrado: {nome_logado}")\n    \n    return True'

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
    # Try to find with raw comparison
    start = content.find('def confirmar_identidade(page: Page, aluno: Aluno) -> bool:')
    if start >= 0:
        end = content.find('\ndef ', start + 1)
        if end == -1:
            end = len(content)
        actual = content[start:end]
        print('ACTUAL:', repr(actual))
        print('EXPECTED:', repr(old))
        print('MATCH:', actual == old)