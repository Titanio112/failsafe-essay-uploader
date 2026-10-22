# Automação de redações — Esquema Redação

Envia os JPGs das redações dos alunos para a plataforma
www.esquemaredacao.com.br, entrando na conta de cada aluno.

> **Hoje o envio para alunos reais está BLOQUEADO** (decisão de 22/10/2026).
> Só a conta de teste envia. Para liberar: `PRODUCAO_BLOQUEADA = False` em
> `modulos/config.py`, só com ordem do Antônio.

## Primeira vez

```
pip install -r requirements.txt
python -m playwright install chromium
python main.py --preparar
```

O `--preparar` cria o que falta e mostra o que ainda precisa ser feito:

| O quê | Onde | Como |
|---|---|---|
| Lista de alunos | `dados/dados_alunos.csv` | Uma linha por aluno: `Nome;Email` (o e-mail da plataforma) |
| Redações | `Redações plataforma/` | Uma subpasta por tema; dentro, um JPG por aluno, com o nome do aluno |
| Senhas | `.env` | `ESQUEMA_EMAIL_TESTE`, `ESQUEMA_SENHA_TESTE`, `ESQUEMA_SENHA_PADRAO` |

Folha sem redação: ponha "em branco" no nome do arquivo; ela nunca é enviada.

## Uso de cada semana

1. Coloque as redações em `Redações plataforma/<tema>/`.
2. Confira sem enviar nada (dry-run):
   ```
   python main.py
   ```
3. Revise no terminal o tema de cada pasta e os nomes que não batem:
   ```
   python main.py --revisar
   ```
   - Tema: Enter confirma o provável, um número escolhe, `g` = tema genérico
     (000, quando o tema não existe no site), uma palavra procura.
   - Nomes: Enter confirma, número escolhe, texto procura outro aluno. O
     arquivo é renomeado para o nome exato do aluno (dá para desfazer com o
     comando que aparece no fim).
4. Rode o dry-run de novo e confira a fila.
5. Envio (hoje só na conta de teste):
   ```
   python main.py --modo-teste --envio-real
   ```
   Digite `ENVIAR TESTE` para confirmar.

## Outros comandos

| Comando | Para quê |
|---|---|
| `python main.py --analise-remota` | Lê a lista de temas do site e atualiza `dados/temas_site.csv` (digite `ANALISAR`) |
| `python main.py --desfazer-renomeacao relatorios/renomeacoes_<data>.csv` | Volta os nomes de uma revisão |
| `python main.py --pasta "outra pasta"` | Usa outra pasta de redações |
| `python -m pytest -q` | Testes (offline, sem site) |

## Segurança

- Sem `--envio-real` nada é enviado. Com ele, só depois de digitar a confirmação.
- Uma redação já enviada nunca é reenviada; resultado incerto vira
  "revisão manual", nunca um segundo clique.
- Senhas só no `.env` (nunca no git, nunca no log).

## Para quem mexe no código

`AGENTS.md` (regras e fatos do site), `PROJECT_MEMORY.md` (estado),
`docs/TAREFAS_ATUAIS.md` (o que está aberto), `docs/historico/` (histórico).
