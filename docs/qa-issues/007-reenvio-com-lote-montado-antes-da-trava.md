# 007 — Redação já enviada por outra janela era enviada de novo

- **Tipo:** bug de envio (segurança)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/envio/envio_item.py`, `modulos/envio/fluxo_envio_producao.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

O lote é montado e a palavra ENVIAR é pedida ANTES de pegar a trava de "um envio por vez". Com duas janelas paradas no "Digite ENVIAR", a segunda pegava a trava depois que a primeira terminava e usava o lote velho. Dentro da trava o envio não relia o caderno: com site 1 e caderno 1, a conta da T48 (total = caderno + 1) dava 2 e a redação era enviada pela segunda vez.

## Reprodução

Caderno temporário com o item já ENVIADO hoje, site com 1 linha do tema hoje: `enviar_item` clicava em Enviar de novo (1 clique).

## Correção

No começo de `enviar_item` (já dentro da trava) o caderno é relido: item (ou a mesma foto) em ENVIADO/JA_ENVIADO vira JA_ENVIADO sem clique e sem regravar; em REVISAO_MANUAL/ENVIANDO para tudo.
