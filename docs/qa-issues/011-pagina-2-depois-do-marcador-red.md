# 011 — "Ana Souza - Red 2.jpg" sozinha ia direto para a fila

- **Tipo:** bug de dado
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/normalizacao.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A regra da T48 manda para revisão o arquivo que só é identificado tirando o número final ("Ana Souza 2.jpg": página 2? cópia?). Mas `extrair_pessoa` cortava tudo depois de " - Red", e o número sumia antes da checagem.

## Reprodução

"Ana Souza - Red 2.jpg", "Ana Souza - Redação (2).jpg" e "Ana Souza - Red - Copia.jpg" sozinhas na pasta viravam EXATO_UNICO.

## Correção

Número ou "cópia" depois do marcador volta para o fim do nome; a conciliação manda para REVISAO_MANUAL, como "Ana Souza 2". Nas 130 fotos reais nenhuma usa o marcador.
