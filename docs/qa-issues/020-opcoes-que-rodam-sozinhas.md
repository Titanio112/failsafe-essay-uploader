# 020 — Opções que rodam sozinhas aceitavam outras caladas

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `main.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

Pela regra T46, opção fora de lugar é recusada. Mas `--preparar` rodava antes de qualquer checagem, `--arquivar` ignorava `--conferir-site`/`--resolver`/`--enviar-faltantes`, e `--resolver` aceitava `--ensaio` e `--modo-teste` (com `--modo-teste`, o `v` podia abrir a foto da pasta errada).

## Reprodução

`python main.py --arquivar --conferir-site` arquivava e saía com 0, sem conferir.

## Correção

Uma checagem única antes de tudo: as ações exclusivas não combinam entre si nem com envio/ensaio/revisão (saída 2).
