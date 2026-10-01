import pathlib

part2 = """
### Duplicidade (antes de anexar)

1. Login do aluno → `/minhas-redacoes` ler lista de redações.
2. Se tema (código) já consta na lista → `[JA_ENVIADO] Tema <cód> do aluno <nome> já enviado em <data>. Pulado.` → estado `JA_ENVIADO`.
3. Lista sem dados suficientes (tema/data) → `REVISAO_MANUAL`, não envia.
4. Dois arquivos do mesmo aluno com mesmo código → `REVISAO_MANUAL`.

### Fluxo de envio (Fase 3)

1. Login → confirmar identidade (nome no navbar).
2. Abrir `/wordings/new` → selecionar tema pelo **código exato** → selecionar ENEM.
3. Anexar JPG → aguardar \"upload aceito\" (botão \"Enviar resposta\" habilita, ~10 s).
4. `ENVIANDO` no SQLite (transação confirmada).
5. Clique **único** em \"Enviar resposta\" (sem retry).
6. Poll em `/minhas-redacoes` a cada 10 s (reload) por 120 s.
7. Confirmação inequívoca → `ENVIADO` + `registrar_envio()` + confirmar queda de saldo.
8. Timeout/ambíguo → `REVISAO_MANUAL` (nunca reenviar sozinho).

### Estados

```
PENDENTE
EXATO_UNICO
SUGESTAO_FUZZY
AMBIGUO
ARQUIVO_SEM_ALUNO
ALUNO_SEM_ARQUIVO
ARQUIVO_INVALIDO
SEM_CODIGO
CODIGO_INVALIDO
SIMULADO
LOGIN_FALHOU
IDENTIDADE_DIVERGENTE
ENVIANDO
ENVIADO
JA_ENVIADO              # duplicidade detectada antes de enviar
PULADO                  # outros saltos (ex.: limite atingido)
ERRO_SITE
REVISAO_MANUAL
```

### Identidade local

Chave: `email_normalizado + codigo_tema + SHA-256(arquivo)`

### Trava de envio

- Dry-run padrão → `[BLOQUEADO] Envio real desativado.`
- Produção: `--envio-real` + resumo + `ENVIAR SALA <sala>`.
- Teste: `--modo-teste --envio-real` + `ENVIAR TESTE`.
- Análise: `--analise-remota` + `ANALISAR SALA <sala>`.
- Senhas só via env (`ESQUEMA_SENHA_PADRAO`, `ESQUEMA_TESTE_SENHA`) ou `getpass`.

### Créditos

- Ler saldo em `/minhas-redacoes` antes e depois de cada envio.
- Não iniciar se saldo < envios planejados.
- Queda de saldo é sinal EXTRA, nunca a única prova de sucesso.

## Fases

1. **Análise remota** (`--analise-remota`): só leitura. Para cada aluno da sala com arquivos: contexto limpo, login, ler `/minhas-redacoes`, ler combo temas, logout. Pausa 5–10 s entre alunos. Parar após 3 falhas de login consecutivas. Gerar `relatorios/analise_<data>.csv` (aluno, e-mail mascarado, sala, código, arquivo, situação, data_envio_se_ja_enviado). Resumo no terminal: quantos já enviaram, quantos faltam, quantos exigem revisão.
2. **Envio em lote** só liberado se análise feita no mesmo dia.

## Hipóteses a confirmar (pendências)

1. Conta de teste sem escola/turma abre \"Enviar redação\" e vê os temas?
2. Créditos suficientes na conta de teste?
3. `/minhas-redacoes` expõe: tema (código/nome), data, status? Que campos exatamente?
4. Mensagem exata de \"upload aceito\".
5. Formato de data/fuso na lista de redações.
6. Diagnóstico de login anterior usou credencial de aluno real (Sala B). Regra: testes só na conta de teste.

## Progresso

- [x] Config, planilha, conciliação, SQLite, dry-run, testes essenciais (8/8 passing).
- [x] Diagnóstico de login funcional (Playwright) — usou credencial de aluno real (Sala B); **regra: testes só na conta de teste**.
- [x] **Fase 2 parcial**: navegação pós-login mapeada (`/minhas-redacoes`, `/wordings/new`). `/meus-pedidos` é compras de créditos, não redações.
- [x] Estrutura de pastas criada com `.gitkeep`; `config.example.ini` atualizado; `dados/temas_site.csv` vazio (referência).
- [ ] `planilha_arquivos.py`: extração de código do tema (arquivo/pasta), validação contra combo do site, prompt interativo (máx 3 tentativas).
- [ ] `plataforma.py`: ler `/minhas-redacoes` para duplicidade; ler combo temas; fluxo completo com `ENVIANDO` antes do clique; créditos antes/depois.
- [ ] `main.py`: CLI com `--analise-remota`, `--modo-teste`, `--envio-real`, seleção de sala, orquestração + confirmações `ANALISAR SALA <sala>`, `ENVIAR TESTE`, `ENVIAR SALA <sala>`.
- [ ] Testes T1–T4 na conta de teste (logs em `logs/<execucao>/`).
- [ ] Novos testes unitários com input simulado (ver AGENTS.md).
- [ ] `.gitignore` atualizado para novas pastas.
"""

existing = pathlib.Path("PROJECT_MEMORY.md").read_text(encoding="utf-8")
pathlib.Path("PROJECT_MEMORY.md").write_text(existing + part2, encoding="utf-8")
print("Parte 2 anexada")