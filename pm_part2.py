import pathlib

part2 = """
## Regras operacionais

### Modos de execução

| Flag | Conta | Pasta | Confirmação | Limite envios |
|------|-------|-------|-------------|---------------|
| (nenhuma) | — | — | dry-run | — |
| `--modo-teste` | `ESQUEMA_TESTE_EMAIL` | `testes/redacoes_teste/` | `ENVIAR TESTE` | `max_envios_teste` (default 5) |
| `--envio-real` (produção) | Aluno da planilha | `redacoes_pendentes/` | `ENVIAR SALA <sala>` | `max_envios_por_aluno` (4) |

- Modo teste **nunca** lê `redacoes_pendentes/` nem usa credenciais de aluno real.
- Produção **nunca** lê `testes/redacoes_teste/` nem loga na conta de teste.

### Duplicidade (antes de anexar)

1. Abrir `/meus-pedidos` do aluno logado.
2. Se tema (código) já consta na lista → `[DUPLICADA] Tema <cód> do aluno <nome> já enviado em <data>. Pulado.` → `PULADO`.
3. Se lista não expõe tema/data suficiente → `REVISAO_MANUAL`, não envia.
4. Registrar exatamente quais campos a lista mostra.

### Fluxo de envio (Fase 3)

1. Login → confirmar identidade (nome no navbar).
2. Abrir `/wordings/new` → selecionar tema pelo **código** → selecionar `ENEM`.
3. Anexar JPG → aguardar botão "Enviar resposta" habilitar (~10 s = upload aceito).
4. `ENVIANDO` no SQLite (transação confirmada).
5. Clique **único** em "Enviar resposta" (sem retry).
6. Poll `/meus-pedidos` a cada 10 s (reload) por 120 s.
7. Novo item único confirmado → `ENVIADO` + `registrar_envio()`.
8. Múltiplos itens novos / timeout → `REVISAO_MANUAL` (nunca reenviar sozinho).

### Estados (atualizados)

```
PENDENTE
EXATO_UNICO
SUGESTAO_FUZZY
AMBIGUO
ARQUIVO_SEM_ALUNO
ALUNO_SEM_ARQUIVO
ARQUIVO_INVALIDO
SIMULADO
LOGIN_FALHOU
IDENTIDADE_DIVERGENTE
ENVIANDO
ENVIADO
JA_ENVIADO
PULADO              # duplicidade detectada antes de enviar
ERRO_SITE
REVISAO_MANUAL
```

### Identidade local

Chave: `email_normalizado + codigo_tema + SHA-256(arquivo)`

### Trava de envio

- Dry-run padrão → `[BLOQUEADO] Envio real desativado.`
- Produção: `--envio-real` + resumo + `ENVIAR SALA <sala>`.
- Teste: `--modo-teste --envio-real` + `ENVIAR TESTE`.
- Senhas só via env (`ESQUEMA_SENHA_PADRAO`, `ESQUEMA_TESTE_SENHA`) ou `getpass`.

## Hipóteses a confirmar (pendências)

1. Conta de teste sem escola/turma consegue acessar "Enviar redação" e ver os temas?
2. Conta de teste tem créditos suficientes para 5 envios?
3. Lista remota (`/meus-pedidos`) expõe: tema (código/nome), data, nome do arquivo, status, ID/href único?
4. Lista real de códigos de temas (virá depois; `dados/temas.csv` tem exemplos fictícios).
5. Formato exato dos 5 nomes de arquivo de teste (prefixo numérico?).
6. Mensagem exata de "upload aceito" (hoje inferida pelo botão habilitar).
7. Formato de data/fuso na lista remota.

## Progresso

- [x] Config, planilha, conciliação, SQLite, dry-run, testes essenciais (8/8 passing).
- [x] Diagnóstico de login funcional (Playwright) — credenciais reais de aluno testadas.
- [x] **Fase 2 parcial**: navegação pós-login mapeada (`/minhas-redacoes`, `/wordings/new`, `/meus-pedidos`).
- [x] Estrutura de pastas criada com `.gitkeep`; `dados/temas.csv` com exemplos; `config.example.ini` atualizado.
- [ ] `planilha_arquivos.py`: extração de código do tema (arquivo/pasta), validação contra `temas.csv`, prompt interativo.
- [ ] `plataforma.py`: detecção de duplicidade em `/meus-pedidos`, fluxo completo de envio com `ENVIANDO` antes do clique.
- [ ] `main.py`: CLI com `--modo-teste`, `--envio-real`, seleção de sala, orquestração.
- [ ] Testes T1–T4 na conta de teste (logs em `logs/<execucao>/`).
- [ ] `.gitignore` atualizado para novas pastas.
"""

existing = pathlib.Path("PROJECT_MEMORY.md").read_text(encoding="utf-8")
pathlib.Path("PROJECT_MEMORY.md").write_text(existing + part2, encoding="utf-8")
print("Parte 2 anexada")