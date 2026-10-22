# Automação de redações — Esquema Redação

Envia os JPGs das redações dos alunos para a plataforma
www.esquemaredacao.com.br, entrando na conta de cada aluno.

> **Hoje o envio para alunos reais está BLOQUEADO** (decisão de 22/10/2026).
> Só a conta de teste envia (modo teste e ensaio). Para liberar: `PRODUCAO_BLOQUEADA = False` em
> `modulos/base/config.py`, só com ordem do Antônio.

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
| Redações | `Redações plataforma/` | Uma subpasta por tema; dentro, um `.jpg`/`.jpeg` por aluno, com o nome do aluno (sem subpastas) |
| Senhas | `.env` | `ESQUEMA_EMAIL_TESTE`, `ESQUEMA_SENHA_TESTE`, `ESQUEMA_SENHA_PADRAO` |

Folha sem redação: ponha "em branco" no nome do arquivo; ela nunca é enviada.

A lista pode ser salva pelo Excel (aceita "E-mail" no cabeçalho). Arquivos
como "Ana 2.jpg" ou "Ana (2).jpg" (página 2? cópia?) e a mesma foto com dois
nomes não vão sozinhos: aparecem para você decidir.

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
5. Teste com as redações reais na conta de teste: `python main.py --ensaio 3`
   (veja abaixo).
6. Envio para os alunos: hoje BLOQUEADO.

## Testar com redações reais (ensaio)

O jeito de testar as fotos, os temas e as aprovações **de verdade** sem
tocar em nenhum aluno. Pega a fila real já conferida (lista de alunos,
`Redações plataforma/`, aprovações de `dados/`), escolhe N redações (uma
pasta de cada vez) e manda **todas para a conta de teste**. Nenhuma conta de
aluno é aberta. Funciona mesmo com o envio para alunos bloqueado.

```
python main.py --ensaio 3                 mostra quais 3 iriam (não envia)
python main.py --ensaio 3 --envio-real    envia para a conta de teste (digite ENVIAR TESTE)
```
- Sem número, são 3. Cada redação gasta 1 crédito da conta de teste.
- O que já foi no ensaio não volta na próxima vez.
- Precisa de `dados/temas_site.csv` (rode `--analise-remota` antes, se faltar).
- Não combina com `--modo-teste`, `--revisar` nem `--analise-remota`.
- Se o `ESQUEMA_EMAIL_TESTE` for o e-mail de um aluno da lista, recusa.

## Testar na conta de teste com as pastas de teste

O modo teste faz **exatamente o mesmo caminho** do envio real (temas das
pastas, tema genérico, revisão de nomes, contagem do dia), mas o único
"aluno" é a conta de teste e as redações ficam em `testes/redacoes_teste/`.
As aprovações de teste ficam em `testes/` e nunca se misturam com as reais.

```
testes/redacoes_teste/
├── 0 - Narração/                           pasta com código: vai direto
├── Efeitos da aporofobia/                  tema que não existe: g (000)
├── Discriminação no trabalho/              2º no 000 no mesmo dia + nome curto + folha em branco
└── Impactos da invisibilidade da filiação/ Enter no tema 100 + nome com erro
```

```
python main.py --modo-teste                 confere, sem enviar
python main.py --modo-teste --revisar       g, g, Enter e os nomes
python main.py --modo-teste                 a fila deve ter 4 redações
python main.py --modo-teste --envio-real    digite ENVIAR TESTE
```
Cada redação enviada gasta 1 crédito da conta de teste. Pode criar mais
subpastas para testar outros casos: os arquivos devem ter o nome da conta
de teste (`Usuario Testes Ignorar`) ou algo parecido, para a revisão perguntar.

## Outros comandos

| Comando | Para quê |
|---|---|
| `python main.py --ensaio [N]` | Redações reais conferidas -> conta de teste (veja acima) |
| `python main.py --analise-remota` | Lê a lista de temas do site e atualiza `dados/temas_site.csv` (digite `ANALISAR`) |
| `python main.py --analise-remota --conta-aluno EMAIL` | Lê os temas na conta desse aluno (só leitura; entra na conta do aluno). `--conta-aluno` sozinho é recusado |
| `python main.py --envio-real --limite-alunos N` | Produção: só os N primeiros alunos do lote (só vale no `--envio-real` de produção) |
| `python main.py --envio-real --limite-redacoes N` | Produção: só as N primeiras redações do lote (idem; no ensaio use `--ensaio N`) |
| `python main.py --desfazer-renomeacao relatorios/renomeacoes_<data>.csv` | Volta os nomes de uma revisão |
| `python main.py --pasta "outra pasta"` | Usa outra pasta de redações (recusado com `--modo-teste`, que usa sempre `testes/redacoes_teste/`) |
| `python -m pytest -m "not real" -q` | Testes offline (sem site) |

Cada execução fica registrada em `logs/automacao.log`. O script pode ser
rodado de qualquer pasta (`python caminho\main.py`).

## Mudar o visual do terminal

Todo o visual (cores, símbolos ✔ ⚠ ✘, largura, linhas dos títulos, barras de
%) fica em **`modulos/base/tela.py`**, na parte de cima do arquivo. Mude lá e
a saída inteira muda junto. Sem cores: defina a variável `NO_COLOR=1`.

## Segurança

- Sem `--envio-real` nada é enviado. Com ele, só depois de digitar a confirmação.
- Uma redação já enviada nunca é reenviada; resultado incerto vira
  "revisão manual", nunca um segundo clique.
- Senhas só no `.env` (nunca no git, nunca no log).
- Um envio por vez: uma segunda janela com `--envio-real` sai sem enviar.
- CAPTCHA ou site estranho para tudo. Entre 23:55 e 00:05 (Brasília) não envia.
- A mesma foto nunca é enviada duas vezes, mesmo com outro nome.

## Para quem mexe no código

```
main.py                 linha de comando (só orquestra)
modulos/base/           configuração, estados, erros, banco de progresso
modulos/dados/          lista de alunos, arquivos, conciliação, aprovações
modulos/site/           login, lista de redações, formulário, confirmação
modulos/envio/          filas e fluxos de envio (teste, ensaio e produção)
modulos/ferramentas/    revisão no terminal e primeiro uso
tests/                  testes offline (pytest)
dados/                  lista de alunos, temas do site, aprovações
relatorios/             banco de progresso e relatórios (fora do git)
logs/                   automacao.log (fora do git)
docs/                   tarefas, pendências, bugs (qa-issues) e histórico
```
Regras e fatos do site: `AGENTS.md`. Estado: `PROJECT_MEMORY.md`.
