# 014 — Aprovações sumiam sem aviso com o CSV salvo com vírgula

- **Tipo:** bug de dado
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/arquivos_csv.py`, `nomes_aprovados.py`, `sugestao_temas.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

Os arquivos de aprovação são lidos com `;`. Salvos com vírgula (Excel em inglês), nenhuma aprovação valia e nada avisava. Pior: a revisão (`aprovar_pasta`) regravava o arquivo e trocava as aprovações antigas por linhas vazias.

## Reprodução

`pastas_aprovadas.csv` com vírgula: `{}` e 0 avisos; depois de `aprovar_pasta`, linhas `;;;;`.

## Correção

Cabeçalho sem as colunas esperadas = aviso claro ("salve como CSV separado por ponto e vírgula") e o arquivo não é regravado.
