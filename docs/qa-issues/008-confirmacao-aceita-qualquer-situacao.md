# 008 — Confirmação marcava ENVIADO com a linha nova em qualquer situação

- **Tipo:** bug de envio (fail-closed)
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/site/confirmacao.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A regra é: sucesso só com a linha nova "Pendente" (ou "Processando" no fim do prazo). O código aceitava qualquer situação que não tivesse "erro" no texto. Uma linha nova "Recusada" ou "Falha no upload" virava ENVIADO, e ENVIADO nunca é reenviado nem aparece em "O que precisa de você".

## Reprodução

Lista falsa com a linha nova em "Recusada", "Falha no upload", "Arquivo inválido": `aguardar_confirmacao` devolvia True.

## Correção

Situação nova desconhecida (fora de Pendente, Processando, Corrigida, erro) espera e, se não mudar no prazo, vira ConfirmacaoInconclusiva (REVISAO_MANUAL). A linha antiga que vira "Corrigida" durante a espera continua não atrapalhando (T48).
