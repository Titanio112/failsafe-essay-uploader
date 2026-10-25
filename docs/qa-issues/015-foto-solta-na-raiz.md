# 015 — Foto solta na raiz da pasta das redações sumia sem aviso

- **Tipo:** melhoria (aviso)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/planilha_arquivos.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

Só as subpastas de tema eram lidas. Um JPG arrastado para a raiz não aparecia em lugar nenhum (subpasta e extensão errada já avisavam).

## Reprodução

"Fulano Teste.jpg" na raiz: nenhum aviso.

## Correção

Aviso "Arquivo fora de pasta de tema ignorado" para cada foto da raiz (o LEIA-ME fica de fora).
