# 010 — Pasta aprovada sem o nome do tema deixava o "0" do Excel passar

- **Tipo:** bug de dado
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/dados/sugestao_temas.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

A proteção da T43 (o Excel transforma "000" em "0", e 0 é outro tema do site) só funcionava com a coluna `tema` preenchida. Com ela vazia (pasta sem tema parecido, código digitado à mão) o "0" passava e as redações iam para Narração em vez do genérico.

## Reprodução

`3B - Tema novo;0;;sim;` em `pastas_aprovadas.csv`: conciliação marcava EXATO_UNICO no tema 0.

## Correção

Decisão do Antônio (25/10, opção a): linha aprovada sem o nome do tema é ignorada com aviso ("preencha a coluna tema ou aprove pelo menu 2"). A revisão do menu 2 já grava o nome.
