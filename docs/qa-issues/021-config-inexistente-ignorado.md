# 021 — --config com caminho errado era ignorado sem aviso

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/base/config.py`, `main.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

Um `--config` que não existe caía calado no `config.ini` padrão (outra pasta de redações, outra lista, outro modo de navegador).

## Reprodução

`python main.py --config confg.ini` (erro de digitação) rodava com o config padrão.

## Correção

Arquivo pedido que não existe = erro claro e saída 2.
