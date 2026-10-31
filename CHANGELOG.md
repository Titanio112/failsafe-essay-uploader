# Changelog

Mudanças que importam para quem usa o script. Cada tarefa tem um número
(T1, T2...). Os bugs ficam em [`docs/qa-issues/`](docs/qa-issues) e nas
[issues do GitHub](https://github.com/Titanio112/failsafe-essay-uploader/issues).
O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado
- **Gerenciar escolas e turmas (#35):** menu 13 Configurações ganhou adicionar escola, adicionar turma, renomear escola e renomear turma (a pasta, o arquivo morto e o caderno acompanham; cópia do caderno antes; recusa durante um envio).
- Toda turma nasce com a pasta-guia `Renomeie_Para_O_Tema_E_Coloque_As_Redacoes_Aqui` em `temas/` (ignorada até ser renomeada). Um único `LEIA-ME.md` por escola, em vez de um por pasta.
- **Primeiro uso guiado (#34):** sem nenhuma turma, `python main.py` pergunta "É a primeira vez?" e monta escolas e turmas passo a passo (ou cria só uma escola de exemplo), com `LEIA-ME.md` em cada pasta, links clicáveis e resumo final.
- `CHANGELOG.md`, modelos de issue e de pull request, etiquetas e milestones no GitHub.
- **M3 — várias escolas e turmas:** cada turma é `Redações plataforma/<Escola>/<Turma>/`
  (`alunos.csv`, `temas/`, `dados/`, `relatorios/`, `logs/`). `python main.py` escolhe
  escola e turma antes do menu (opção 14 troca); comandos diretos com `--escola` e `--turma`.
  `--preparar --escola X --turma Y` cria a turma. Exemplo inventado em `exemplos/`.
- **M3:** `--vincular-antigos` liga os registros do caderno de antes das turmas aos alunos
  da turma (pergunta s/n, cópia do caderno antes).

### Mudado
- **M3:** sem turma só o `--modo-teste` roda; `--pasta` saiu; com turma, `pasta_raiz`/`planilha`
  em `[dados]` do `config.ini` são recusados.
- **M3, senhas:** cada aluno entra com a senha da coluna `Senha` do `alunos.csv` (texto exato).
  Sem senha, o aluno não faz login. `ESQUEMA_SENHA_PADRAO` não existe mais.
- **M3, identidade:** o nome do menu do usuário tem de ser igual ao do `alunos.csv` (sem os
  seletores reserva e sem aceitar nome abreviado). Homônimos na turma vão para revisão manual.
- **M3, caderno:** continua um só (`relatorios/progresso.db`), com a coluna `turma`; as travas
  (mesma foto, contagem do dia, já enviado) valem entre turmas e para os registros antigos.
  `--resolver`, desfazer e "enviar as que faltam" só usam o que é da turma.
- **M3, arquivo morto:** só pastas `ENVIADA - ...`, para `Arquivo morto/<Escola>/<Turma>/<data_hora>/`,
  sem nunca sobrescrever.
- **M3, repositório:** `.gitignore` cobre `alunos.csv` em qualquer lugar (menos `exemplos/`),
  cópias e backups; a auditoria pública aceita só a lista inventada de `exemplos/`.

## [2026.10.25] — 25/10/2026

### Adicionado
- **T60 (issue 030):** no fim da conferência no site (menu 5), a pasta com
  todas as fotos no site pode ser marcada `ENVIADA - <nome>`. O script passa
  a ignorá-la, e o arquivo morto (menu 11) a oferece primeiro (`e`).
- **T59 (issue 031):** ao aprovar o tema na revisão (menu 2), a pasta ganha o
  nome do tema do site (`53 - Impactos da evasão...`), com log e desfazer.
- **T58 (issue 025):** `python -m modulos.ferramentas.auditoria_publica`
  confere, antes do push, que não vai dado de aluno, senha nem anotação de IA.

### Corrigido
- **T58, envio (fail-closed):** uma redação já enviada por outra janela não
  é enviada de novo (007); uma situação nova desconhecida não conta como
  sucesso (008); uma lista com layout mudado bloqueia o envio (009).
- **T58, dados:** pasta aprovada sem o nome do tema (010), página 2 depois
  de " - Red" (011), aprovação "parecido" com aluno novo igual (012), mesma
  foto para outro aluno (013), CSV com vírgula (014) e foto solta na raiz (015).
- **T58, ferramentas:** arquivo morto pela metade (016), menu com "²" (017),
  "Cancelada" na conferência (018), desfazer com arquivo aberto (019), opções
  que rodam sozinhas (020), `--config` inexistente (021) e link de pasta no
  VS Code (022).
- **T58, repositório público:** `.gitignore` sem depender de maiúsculas (023),
  `temas_site.csv` sem e-mail (024), `.env` de exemplo não conta como senha
  (026) e documentação atualizada (027).
- **029:** turma no começo do nome da pasta ("3-B", "3 B", "2º ano") ou data
  nunca vira código do tema.

## [2026.10.24] — 24/10/2026

### Mudado
- Projeto publicado no GitHub (portfólio): histórico limpo de dados sensíveis
  (005), README bilíngue e manual em `docs/GUIA_DE_USO.md`.
- Anotações de trabalho das IAs fora do repositório (006).

## [2026.10.23] — até 23/10/2026 (T1–T57)

Desenvolvimento antes da publicação; o detalhe está no histórico de commits.

- Dry-run, conciliação aluno/foto e tema por código da pasta.
- Envio fail-closed: `ENVIANDO` antes do clique, clique único, confirmação
  na lista, trava de um envio por vez, cópia do caderno antes de enviar.
- Modo teste, ensaio com redações reais na conta de teste, revisão no
  terminal, resolver revisões, conferência no site, arquivo morto e menu.
- Envio para alunos reais **bloqueado** (`PRODUCAO_BLOQUEADA = True`) até a
  liberação pelo mantenedor.
