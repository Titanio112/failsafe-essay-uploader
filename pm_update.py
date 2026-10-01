import pathlib

part1 = """# PROJECT_MEMORY.md — Automação de redações

## Objetivo do MVP

MVP Python + Playwright para conciliar alunos/arquivos e enviar redações na plataforma Esquema Redação.
- **Modo teste** (pronto agora): conta dedicada `ESQUEMA_TESTE_EMAIL` + pasta `testes/redacoes_teste/` (5 JPGs "arquivo de testes, ignorar, não corrigir" numerados 1–5).
- **Produção** (bloqueada até autorização): planilha de alunos + `redacoes_pendentes/<tema>/`.
- Envio real **somente** com flags + confirmação textual explícita.

## Fatos confirmados

### Dados locais (estrutura nova)

```
redacoes_pendentes/           # raiz dos arquivos reais
├── <CODIGO> - Nome do Tema/  # subpasta cujo nome CONTÉM o código do tema
│   ├── Aluno Um.jpg
│   └── Aluno Dois.jpg
testes/redacoes_teste/        # 5 JPGs de teste (ignorado em produção)
dados/temas.csv               # codigo,nome_no_site (lista real virá depois)
logs/                         # execucao.log, console_navegador.log, resultado.csv, erros/
relatorios/                   # conciliação, fila, retrospectiva
diagnosticos/                 # HTML/snapshots de diagnóstico
```

- Só `.jpg`/`.jpeg` são processados; outros → `[AVISO]` no log (nome + motivo).
- Código do tema = prefixo numérico no **nome do arquivo** OU no **nome da pasta**.
- Conflito pasta × arquivo → `REVISAO_MANUAL`.
- Sem código → pergunta no terminal (máx. 3 tentativas, opção pular).
- Padrão do código configurável em `config.ini` → `padrao_codigo` (regex, default `^(\\d{3,})[-_\\s]`).

### Planilha de alunos

- 69 alunos (30 Sala A, 39 Sala B). Colunas: `nome`, `email`, `sala`.
- E-mail padrão: `<nome_normalizado>@esquema.com`.
- Senha padrão única para todos (produção): `ESQUEMA_SENHA_PADRAO` (env/getpass).
- Conta de teste: `ESQUEMA_TESTE_EMAIL` / `ESQUEMA_TESTE_SENHA` (só no `.env`).

### Plataforma (descoberto na Fase 2)

- Base: `https://www.esquemaredacao.com.br`
- Login: `/auth/users/sign_in` — campos `user[email]`, `user[password]`, botão `commit=Entrar`.
- Pós-login → `/minhas-redacoes` (8 créditos visíveis).
- "Enviar redação" → `/wordings/new`
  - Combo "Informe o tema da redação" (opções incluem `000- DISSERTATIVO ARGUMENTATIVO`, etc.)
  - Combo "Selecione um critério de avaliação" (default `ENEM`)
  - Input `type=file` escondido sob botão "Choose File"
  - Botão "Enviar resposta" (habilita após upload aceito)
- Lista de enviados: `/meus-pedidos` — tabela com colunas **Data, Pacote, Valor, Situação**.
  - Campos expostos ainda não mapeados completamente (Fase 2).
  - Necessário confirmar se mostra: tema (código), data, nome do arquivo, status, ID/href.
"""

pathlib.Path("PROJECT_MEMORY.md").write_text(part1, encoding="utf-8")
print("Parte 1 escrita")