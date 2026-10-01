import pathlib

part1 = """# PROJECT_MEMORY.md — Automação de redações

## Objetivo do MVP

MVP Python + Playwright para conciliar alunos/arquivos e enviar redações na plataforma Esquema Redação.
- **Modo teste**: conta dedicada `ESQUEMA_TESTE_EMAIL` + pasta `testes/redacoes_teste/` (5 JPGs "arquivo de testes, ignorar, não corrigir").
- **Produção** (bloqueada até autorização): planilha de alunos + `redacoes_pendentes/`.
- Envio real **somente** com flags + confirmação textual explícita.

## Fatos confirmados

### Dados locais (estrutura)

```
redacoes_pendentes/           # raiz dos arquivos reais (sem subpasta por tema; código vem do arquivo)
testes/redacoes_teste/        # 5 JPGs de teste (ignorado em produção)
dados/temas_site.csv          # referencia: codigo,texto,data_leitura,conta_mascarada (preenchido a cada login)
logs/                         # execucao.log, console_navegador.log, resultado.csv, erros/
relatorios/                   # conciliação, fila, retrospectiva, analise_<data>.csv
diagnosticos/                 # HTML/snapshots de diagnóstico
```

- Só `.jpg` (caixa alta ou baixa) são processados; outros → `[AVISO]` no log (nome + motivo).
- Código do tema = número no **início** do nome do arquivo (sem extensão) OU no nome da pasta. Padrão: `^\\s*(\\d+)(?=[\\s_.-]|$)` — número seguido de separador; "3B ..." NÃO é código. Preservar zeros à esquerda (ex.: "000").
- Conflito pasta × arquivo → `REVISAO_MANUAL`.
- Sem código → pergunta no terminal (máx. 3 tentativas, opção pular) → `SEM_CODIGO` se pular.
- Validação: extrair opções do combo "Informe o tema da redação" no site, pegar o código do prefixo de cada opção; se o código não existir no combo → `CODIGO_INVALIDO`.
- Gravar `dados/temas_site.csv` (codigo,texto,data_leitura,conta_mascarada) só como referência; fonte de verdade é o combo da conta logada.

### Planilha de alunos

- 69 alunos (30 Sala A, 39 Sala B). Colunas: `nome`, `email`, `sala`.
- E-mails vêm **sempre da planilha** (não há padrão fixo).
- Senha padrão única para todos (produção): `ESQUEMA_SENHA_PADRAO` (env/getpass).
- Conta de teste: `ESQUEMA_TESTE_EMAIL` / `ESQUEMA_TESTE_SENHA` (só no `.env`).

### Plataforma (descoberto na Fase 2)

- Base: `https://www.esquemaredacao.com.br`
- Login: `/auth/users/sign_in` — campos `user[email]`, `user[password]`, botão `commit=Entrar`.
- Pós-login → `/minhas-redacoes` (saldo de créditos visível, ex.: 8).
- \"Enviar redação\" → `/wordings/new`
  - Combo \"Informe o tema da redação\" (opções incluem `000- DISSERTATIVO ARGUMENTATIVO`, etc.)
  - Combo \"Selecione um critério de avaliação\" (default `ENEM`)
  - Input `type=file` escondido sob botão \"Choose File\"
  - Botão \"Enviar resposta\" (habilita após upload aceito)
- Lista de redações enviadas: **`/minhas-redacoes`** (não `/meus-pedidos`, que mostra compras de créditos).
  - Campos expostos ainda não mapeados completamente (HIPÓTESE até envio manual de teste).
  - Necessário confirmar: tema (código/nome), data, status.

## Regras operacionais

### Modos de execução

| Flag | Conta | Pasta | Confirmação | Limite envios |
|------|-------|-------|-------------|---------------|
| (nenhuma) | — | — | dry-run | — |
| `--analise-remota` | Aluno da planilha | `redacoes_pendentes/` | `ANALISAR SALA <sala>` | — |
| `--modo-teste --envio-real` | `ESQUEMA_TESTE_EMAIL` | `testes/redacoes_teste/` | `ENVIAR TESTE` | `max_envios_teste` (default 5) |
| `--envio-real` (produção) | Aluno da planilha | `redacoes_pendentes/` | `ENVIAR SALA <sala>` | `max_envios_por_aluno` (4) |

- Modo teste **nunca** lê `redacoes_pendentes/` nem usa credenciais de aluno real.
- Produção **nunca** lê `testes/redacoes_teste/` nem loga na conta de teste.
"""

pathlib.Path("PROJECT_MEMORY.md").write_text(part1, encoding="utf-8")
print("Parte 1 escrita")