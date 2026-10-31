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
python main.py --preparar --escola "Minha Escola" --turma "3A"
```

> **Escolas e turmas (M3, 29/10):** cada turma é `Redações plataforma/<Escola>/<Turma>/`, e todo
> comando (menos o `--modo-teste`) precisa de `--escola` e `--turma`; `python main.py` pergunta.
> Neste guia, `dados/...` e `relatorios/...` de uma turma ficam dentro da pasta dela. Detalhes e como
> passar os dados de hoje para uma turma: README, "Escolas e turmas".

O `--preparar` cria o que falta e mostra o que ainda precisa ser feito:

| O quê | Onde | Como |
|---|---|---|
| Lista de alunos | `<Escola>/<Turma>/alunos.csv` | Uma linha por aluno: `Nome;Email;Senha` (e-mail e senha da plataforma; nome igual ao que o site mostra no menu) |
| Redações | `<Escola>/<Turma>/temas/` | Uma subpasta por tema; dentro, um `.jpg`/`.jpeg` por aluno, com o nome do aluno (sem subpastas) |
| Conta de teste | `.env` | `ESQUEMA_EMAIL_TESTE`, `ESQUEMA_SENHA_TESTE` (aluno usa a senha do `alunos.csv`; não há senha padrão) |

Folha sem redação: ponha "em branco" no nome do arquivo; ela nunca é enviada.

A lista pode ser salva pelo Excel (aceita "E-mail" no cabeçalho). Arquivos
como "Ana 2.jpg" ou "Ana (2).jpg" (página 2? cópia?) e a mesma foto com dois
nomes não vão sozinhos: aparecem para você decidir.

## Menu (jeito mais fácil)

`python main.py` sem nada, num terminal, abre um menu (T47):

```
Preparar                    1) Conferir as redações         não envia nada
                            2) Revisar temas e nomes
Testar (nada vai p/ alunos)  3) Ensaio com redações reais
                            4) Modo teste
                            5) Conferir no site            lê as contas, não envia
Enviar                      6) Enviar para os alunos        (hoje: bloqueado)
                            7) Enviar as que faltam no site (hoje: bloqueado)
                            8) Resolver revisões manuais    chegou no site? sim/não
Ferramentas                 9) Atualizar os temas do site
                           10) Desfazer uma renomeação
                           11) Arquivo morto                guarda as pastas já enviadas
                           12) Primeiro uso / o que falta
                           13) Configurações                navegador aparece ou não (s/n)
                            0) Sair
```
Cada opção chama o mesmo comando com flags (abaixo), com as mesmas travas e
confirmações digitadas. Todos os comandos com flags continuam valendo.
Onde o terminal disser "rode `python main.py`", é este menu.

## Uso de cada semana

1. Coloque as redações em `Redações plataforma/<tema>/`.
2. Confira sem enviar nada: menu opção **1** (a conferência termina com
   "Só conferência: nada foi enviado.").
3. Revise no terminal o tema de cada pasta e os nomes que não batem
   (menu opção **2**, ou):
   ```
   python main.py --revisar
   ```
   - Tema: Enter confirma o provável, um número escolhe, `g` = tema genérico
     (000, quando o tema não existe no site), uma palavra procura, `v` abre
     a pasta para ver as fotos (T57). Turma no começo do nome ("3B", "3-B",
     "3 B") é ignorada. Ao confirmar, a pasta ganha o nome do tema do site,
     ex.: `3-B - evasao` -> `53 - Impactos da evasão escolar para o Brasil`
     (T59; dá para desfazer). Pasta com redação já enviada não é renomeada:
     a aprovação fica em `dados/pastas_aprovadas.csv`.
   - Nomes: Enter confirma, número escolhe, texto procura outro aluno. O
     arquivo é renomeado para o nome exato do aluno (dá para desfazer com o
     comando que aparece no fim).
4. Confira de novo (opção 1) e veja a fila ("Prontas para enviar").
5. Teste com as redações reais na conta de teste: `python main.py --ensaio 3`
   (veja abaixo).
6. Envio para os alunos: hoje BLOQUEADO (veja como vai funcionar abaixo).
7. Se sobrar alguma redação em "Conferir no site", responda com
   `python main.py --resolver` (menu opção **8**).

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
As fotos de teste não vêm no repositório (estão no `.gitignore`): num
clone novo, coloque nessas pastas JPGs seus com o nome da conta de teste.
Cada redação enviada gasta 1 crédito da conta de teste. Pode criar mais
subpastas para testar outros casos: os arquivos devem ter o nome da conta
de teste (`Usuario Testes Ignorar`) ou algo parecido, para a revisão perguntar.

## Como funciona o envio para muitos alunos (produção)

Hoje bloqueado; quando o Antônio liberar, é `python main.py --envio-real`
(menu opção **6**).

1. **Uma confirmação só.** O terminal mostra o lote inteiro (aluno por
   aluno, tema e arquivo) e uma parte "Como funciona". Você digita `ENVIAR`
   uma vez para o lote todo. Qualquer outro texto cancela sem enviar nada.
2. **Antes de abrir o navegador:** confere se não está perto da meia-noite
   (23:55 a 00:05 não envia) e guarda uma cópia de segurança do caderno
   (`relatorios/progresso.db`). Sem a cópia, nada é enviado.
3. **Depois vai sozinho, aluno por aluno:** para cada aluno abre um
   navegador limpo (nada de um aluno passa para o outro), faz login, confere
   que o site abriu a conta da pessoa certa e envia as redações dela uma por
   uma. Entre uma redação e outra (e entre alunos) espera um tempo aleatório
   de 8 a 15 s. No fim de cada aluno, sai da conta.
   Durante o envio aparece o **progresso ao vivo** (T51):
   `▶ 23 de 61 redações  ████░░░░░░  38%  ·  passou 12 min  ·  faltam ~19 min`.
   O navegador aparece na tela (para acompanhar); para deixar rodando sem a
   janela: menu **13) Configurações** (fica salvo no `config.ini`) ou
   `--sem-janela` numa execução só.
4. **Pulos automáticos (sem erro):** a redação daquele tema que já está no
   site hoje ("já estava no site") e a mesma foto que já foi enviada, mesmo
   com outro nome.
5. **Para só aquele aluno:** erro antes do clique em "Enviar resposta"
   (tema não conferido, upload não aceito, lista ilegível, login recusado...).
   Nada foi enviado; ele tenta de novo na próxima execução.
6. **Para tudo:** dúvida depois do clique (não apareceu a linha nova na
   lista), CAPTCHA ou site estranho, 2 logins seguidos falhando (senha
   padrão errada? conta bloqueada?) ou chegou perto da meia-noite.
7. **No fim:** o resumo (Enviadas / Já estavam no site / Não enviadas /
   Conferir no site), a lista **"O que precisa de você"** (conferir no site,
   não enviadas com o motivo e o que fazer, e as que nem foram tentadas), o
   relatório `relatorios/envio_<data>.csv` e o log `logs/automacao.log`.
8. **As duvidosas** ("Conferir no site"): olhe o site na conta do aluno e
   responda em `python main.py --resolver` (abaixo).

Rodar de novo é seguro: o que está como enviada, já estava no site ou
conferir no site nunca é reenviado; só as "não enviadas" e as que não foram
tentadas vão de novo.

## Abrir o arquivo direto do terminal

Na conferência, na revisão, no "O que precisa de você" e no `--resolver`
(e, desde a T53, em todo caminho de relatório mostrado na tela),
os nomes de arquivo são **links**: **Ctrl+clique** abre a foto. No terminal
do VS Code a foto abre numa aba do próprio VS Code (o nome da pasta ali não
é link); nos outros terminais a pasta também abre no Explorador. Fora de um
terminal (relatório, log) sai só o texto.

T52: o primeiro jeito (T51) não abria nada: o Windows lê o "ç" codificado
no link como dois caracteres ("RedaÃ§Ãµes") e não acha a pasta. Se mesmo
assim o clique não abrir, na revisão (`--revisar`) e no `--resolver` a
tecla **`v`** abre a foto no visualizador do Windows, sem depender do
terminal.

## Conferir no site (só leitura)

`python main.py --conferir-site` (menu opção **5**): entra na conta de cada
aluno que tem redação conferida na pasta (nome exato + tema aprovado), lê
Minhas redações e diz, foto por foto, se aquele tema **já está no site em
qualquer data** ("no site", com as datas), "em parte" (tema repetido, ex.:
genérico 000, com menos linhas no site do que fotos) ou "não está no site".
Não anexa, não envia e não mexe no caderno. Pede `CONFERIR` (digitado por
você), usa a senha padrão, mostra o progresso por aluno, para em CAPTCHA ou
em 2 contas seguidas sem abrir, e grava `relatorios/conferencia_site_<data>.csv`.
Serve para saber o que já foi mandado à mão antes do script (o envio só
pula o que está no site **hoje**).

T53: se um tema "não está no site", mas o site tem redações **a mais** de
outro tema (ex.: a filiação mandada como 000), a foto aparece como
**"talvez no site com outro tema"** e nunca vai no envio. Desde a T56,
havendo qualquer sobra, **todas** as que "faltariam" daquele aluno ficam
como "outro tema?" (na dúvida, não envia). Na 1ª conferência
real (23/10) foram 28 assim (tema 100 mandado como 000). No fim, as que
certamente faltam podem ser enviadas na hora: o script pergunta "Montar o
envio só destas?" e segue o envio normal (lote na tela, `ENVIAR`, todas as
travas). Hoje a produção está bloqueada, então ele só avisa. Se não falta
nenhuma, ele diz "Não falta enviar nenhuma" (por isso não pergunta nada).
Saiu sem querer? Menu **7) Enviar as que faltam no site**
(`--enviar-faltantes`) usa o relatório da conferência de **hoje**, sem
abrir as contas de novo (relatório de outro dia não vale: alguém pode ter
mandado à mão depois).

Na tela, cada foto é uma linha curta: `✔ no site  tema 000  30/09/2026
pasta`, `⚠ outro tema?  tema 100  como 000?  pasta`, `• falta ...`. O nome
da pasta abre a foto (Ctrl+clique).

**Pastas com tudo no site (T60).** No fim, se uma pasta tem **todas** as
fotos conferidas e "no site", o script lista e pergunta (s/n) se marca:
a pasta vira `ENVIADA - <nome>` (log em `relatorios/pastas_enviadas_<data>.csv`).
Pasta com alguma foto faltando, "em parte", "outro tema?", cancelada, sem
conferir ou que não é de aluno nunca é marcada; conferência que parou não
marca nada. Pastas `ENVIADA - ...` ficam fora de tudo (envio, revisão,
conferência): não há como serem reenviadas. Para desmarcar, tire o
`ENVIADA - ` do nome.

## Arquivo morto (T57)

Menu **11** (`python main.py --arquivar`): mostra as pastas de tema e move
as escolhidas (`t` = todas, ou números: `1,3`) para
`Arquivo morto/<data_hora>/`, na raiz do projeto. Nada é apagado; para
trazer de volta, mova a pasta de novo. Cada movimento fica em
`relatorios/arquivamento_<data>.csv`. Não roda durante um envio.
As pastas `ENVIADA - ...` (conferidas no site, T60) aparecem primeiro, com
"✔ conferida no site", e `e` arquiva só elas.
Use para tirar as redações já enviadas (as antigas, mandadas à mão) antes de
colocar as novas. **Dica:** dê nomes de pasta novos às redações novas: o
caderno lembra "pasta/arquivo"; uma foto nova com o nome de uma já enviada é
pulada (com o aviso "a FOTO E OUTRA ... use um nome de pasta novo").

## Primeiro envio de verdade (quando liberado)

Menu **6** pergunta "Quantos alunos desta vez?" e "Quantas redações no
máximo?" (Enter = todos). Para o primeiro envio: `1` e `1`.

## Resolver as revisões manuais

"Conferir no site" (revisão manual) = o script clicou em Enviar mas não
conseguiu ver a redação na lista. Ele nunca reenvia sozinho (poderia
duplicar). Abra o site **na conta do aluno**, em Minhas redações, e rode:

```
python main.py --resolver        (ou menu opção 8)
```
Para cada uma: `s` = chegou (vira enviada e nunca mais vai), `n` = não
chegou (vai de novo na próxima execução), Enter = deixa para depois, `q` =
sai. A data do registro não muda (a contagem do dia continua certa) e cada
resposta fica em `relatorios/resolucoes_<data>.csv`.

## Cópia de segurança do caderno

Antes de cada envio (modo teste, ensaio ou produção) o caderno
`relatorios/progresso.db` é copiado para
`relatorios/copias/progresso_<data_hora>.db` (ficam as 30 mais recentes).
Se a cópia falhar, nada é enviado.

Para voltar uma cópia: feche o script, renomeie o `relatorios/progresso.db`
e copie a cópia escolhida para esse nome.

> **CUIDADO:** voltar uma cópia antiga faz o script **esquecer os envios
> feitos depois dela**. Os do mesmo dia o site ainda segura (contagem do
> dia), mas os de dias anteriores podem ir **de novo**. Só volte uma cópia
> se o `progresso.db` atual sumiu ou estragou, e confira no site antes de
> enviar.

## Outros comandos

| Comando | Para quê |
|---|---|
| `python main.py --ensaio [N]` | Redações reais conferidas -> conta de teste (veja acima) |
| `python main.py --resolver` | Responde, uma a uma, as redações em "conferir no site" (veja acima) |
| `... --envio-real --sem-janela` | Envia sem mostrar o navegador (padrão: mostra; fixo: menu 13, Configurações) |
| `python main.py --conferir-site` | Só lê: o tema de cada foto já está no site? (`CONFERIR`) |
| `python main.py --analise-remota` | Lê a lista de temas do site e atualiza `dados/temas_site.csv` (digite `ANALISAR`) |
| `python main.py --analise-remota --conta-aluno EMAIL` | Lê os temas na conta desse aluno (só leitura; entra na conta do aluno). `--conta-aluno` sozinho é recusado |
| `python main.py --envio-real --limite-alunos N` | Produção: só os N primeiros alunos do lote (só vale no `--envio-real` de produção) |
| `python main.py --envio-real --limite-redacoes N` | Produção: só as N primeiras redações do lote (idem; no ensaio use `--ensaio N`) |
| `python main.py --desfazer-renomeacao relatorios/renomeacoes_<data>.csv` | Volta os nomes (arquivos e pastas) de uma revisão |
| `python main.py --escola "E" --turma "T"` | Escolhe a turma (obrigatório, menos no `--modo-teste`); `--pasta` saiu |
| `python main.py --vincular-antigos --escola "E" --turma "T"` | Registros do caderno de antes das turmas, dos alunos desta turma, passam a ser dela (cópia antes) |
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
- Cópia do caderno antes de cada envio; sem cópia, não envia.
- 2 logins seguidos falhando param o envio (senha padrão errada?).
- A lista do site só vale se for a página certa (com o saldo de créditos);
  senão, nada é enviado para aquele aluno.
- CAPTCHA ou site estranho para tudo. Entre 23:55 e 00:05 (Brasília) não envia.
- A mesma foto nunca é enviada duas vezes, mesmo com outro nome.

## Para quem mexe no código

```
main.py                 linha de comando (só orquestra)
modulos/base/           configuração, estados, erros, banco de progresso
modulos/dados/          lista de alunos, arquivos, conciliação, aprovações
modulos/site/           login, lista de redações, formulário, confirmação
modulos/envio/          filas e fluxos de envio (teste, ensaio e produção)
modulos/ferramentas/    menu, revisão no terminal, resolver e primeiro uso
tests/                  testes offline (pytest)
dados/                  temas do site (uma lista para todas as turmas), referências do projeto
relatorios/             banco de progresso e relatórios (fora do git)
logs/                   automacao.log (fora do git)
docs/                   este guia e os bugs (qa-issues)
```
