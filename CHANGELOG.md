# Changelog

Mudanças que importam para quem usa o script. Cada tarefa tem um número
(T1, T2...). Os bugs ficam em [`docs/qa-issues/`](docs/qa-issues) e nas
[issues do GitHub](https://github.com/Titanio112/failsafe-essay-uploader/issues).
O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado
- `CHANGELOG.md`, modelos de issue e de pull request, etiquetas e milestones no GitHub.

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
