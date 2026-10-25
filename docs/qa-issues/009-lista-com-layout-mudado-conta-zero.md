# 009 — Lista do site com layout mudado contava 0 e liberava o envio

- **Tipo:** bug de envio (fail-closed)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/site/lista_redacoes.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

Dois furos na leitura de /minhas-redacoes: (1) com o cabeçalho mudado, uma outra tabela sem `<th>` na página (ou um `<table></table>` vazio) era lida no lugar da lista; (2) data com hora, em outro formato ou tema sem o código no começo faziam toda linha deixar de casar. Nos dois casos a contagem do tema hoje dava 0, e uma redação já mandada à mão podia ir de novo.

## Reprodução

HTML com a lista Data|Tema|Situação|Nota mais uma tabela sem `<th>`: lida, 0 do tema. Linha com data "24/10/2026 14:05": lida, 0 do tema.

## Correção

Tabela com outro cabeçalho e nenhuma com o esperado = lista ilegível. Antes do clique, toda linha tem de ter a data dd/mm/aaaa e o tema começando pelo código; senão, lista ilegível (não envia).
