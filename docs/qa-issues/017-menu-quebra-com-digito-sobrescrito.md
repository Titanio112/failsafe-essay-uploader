# 017 — Menu fechava com "²" ou "³" digitado

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/ferramentas/menu.py`, `revisao_interativa.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

`isdigit()` aceita "²" (AltGr+2), mas `int()` não. A pergunta da opção ficava fora do try do menu, então o menu fechava com traceback.

## Reprodução

Menu 3 (ensaio), "Quantas redações?" -> "²": ValueError.

## Correção

`isdecimal()` no lugar de `isdigit()`; as perguntas da opção ficam dentro do try do menu.
