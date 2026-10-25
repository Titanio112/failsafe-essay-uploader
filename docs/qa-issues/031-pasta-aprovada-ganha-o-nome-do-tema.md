# 031 — Pasta aprovada ganha o nome do tema do site

- **Tipo:** melhoria (pedido do Antônio, item 2 da conversa de 25/10)
- **Status:** feito em 25/10/2026 (T59; testes em `tests/test_t59.py`)
- **Local:** `modulos/ferramentas/revisao_interativa.py`
- **Pedido em:** 25/10/2026

## Descrição

As pastas chegam com nomes da escola ("3-B - impactos da evasao"). Antes,
a revisão (menu 2) só anotava o tema aprovado em
`dados/pastas_aprovadas.csv` e a pasta continuava com o nome de origem, com
o tema "escondido" num CSV.

## O que mudou

- Ao confirmar o tema, a pasta é **renomeada** para `<código> - <tema do
  site>`, ex.: `53 - Impactos da evasão escolar para o Brasil`. O código fica
  no próprio nome e o CSV não é mais preciso para ela.
- A troca vai para o mesmo log das renomeações de arquivo
  (`relatorios/renomeacoes_<data>.csv`, linha com a coluna `pasta` vazia) e
  o desfazer (menu 10) volta primeiro os arquivos e depois a pasta.
- A parte 2 da revisão (nomes) já usa o nome novo da pasta.

## Travas (nunca renomeia)

- Pasta com alguma redação no caderno (enviada, pulada, em revisão): o
  caderno identifica a redação por pasta/arquivo, e renomear abriria
  caminho para reenvio. A aprovação vai para o CSV, como antes.
- Pasta com foto aberta (o Windows recusa) ou nome novo que já existe: idem.
- Desfazer não volta uma pasta que já tem redação no caderno pelo nome novo.

## Prova

Cópia do projeto, pasta de teste "impactos da evasão escolar para o Brasil":
revisão renomeou para "53 - Impactos da evasão escolar para o Brasil", o
dry-run passou de 5 para 6 prontas, e o desfazer voltou o nome antigo.
