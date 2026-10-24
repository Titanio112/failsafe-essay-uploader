# 005 — Dados sensíveis no histórico do git antes de publicar

- **Tipo:** bug de dado / segurança
- **Status:** resolvido em 24/10/2026, antes da publicação (nada foi público antes da limpeza)
- **Local:** histórico do git (docs, scripts de diagnóstico apagados, logs, metadados)
- **Encontrado em:** 24/10/2026, na auditoria do histórico para o repositório público

## Descrição

O `.gitignore` protegia os dados no dia a dia, mas commits antigos tinham:
credenciais da conta de teste e a senha padrão em documentos, 7 scripts de
diagnóstico com login fixo, um relatório com nomes de alunos, nomes reais
usados como exemplo nos testes, caminhos locais com o usuário do Windows e o
e-mail pessoal como autor dos commits.

## Reprodução

Auditoria de todos os blobs do histórico, comparando com os valores do `.env`
e com a lista de alunos local (os valores só em memória, nunca impressos).

## Correção

Histórico reescrito com `git-filter-repo` numa cópia separada: os arquivos de
rascunho e os logs saíram de todos os commits; as senhas viraram `********`; o
e-mail de teste virou `teste@example.com`; os sobrenomes de alunos viraram
fictícios; o usuário do Windows virou `%USERNAME%`; o autor virou o e-mail
noreply do GitHub. A mesma auditoria rodada de novo: nada encontrado. Testes:
`415 passed, 4 deselected`.

**Prevenção:** rodar a auditoria antes de cada push. Credenciais só no `.env`.
