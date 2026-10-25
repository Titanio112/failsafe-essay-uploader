# 013 — A mesma foto podia ir para outro aluno em outro dia

- **Tipo:** bug de dado (segurança)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/base/progresso_relatorio.py`, `modulos/envio/fila_producao.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

No mesmo lote a mesma foto (sha256) em dois alunos já era barrada, mas no caderno a busca era só pelo próprio aluno. Foto já enviada para a Ana, copiada com o nome da Bia numa execução seguinte, entrava no lote da Bia.

## Reprodução

Caderno com a foto ENVIADA para outro aluno; a mesma foto com o nome da Ana: entrava no lote.

## Correção

Foto já registrada (enviada, pulada ou em revisão) para OUTRO aluno fica fora do lote com o motivo. O ensaio (chave `ensaio/...`, fotos reais na conta de teste) não conta. Nos dados reais: 0 casos.
