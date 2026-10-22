# 001 — Código repetido no combo (0000) nunca era detectado

- **Tipo:** bug lógico (risco de enviar para o tema errado)
- **Status:** resolvido na T27 (branch `f4-producao`)
- **Encontrado em:** 22/10/2026, ao implementar a análise remota

## Descrição

O combo de temas do site tem o código `0000` duas vezes (Simulado SOMOS 01 e
02). A regra do projeto diz: código repetido no combo -> revisão manual.

1. `main.py` lia `dados/temas_site.csv` num **set**: o segundo `0000` sumia, e a
   conciliação (que conta repetidos) nunca marcava `SIMULADO`.
2. Na trava antes do clique (`envio_item.py`), o código só era conferido com
   `in`; `selecionar_tema_por_codigo` escolhia a **primeira** opção `0000` e a
   conferência da opção marcada ("0000" == "0000") passava. Uma redação
   `0000` iria para o Simulado 01 mesmo sendo do 02.

## Local

- `main.py`, `ler_codigos_site_csv`
- `modulos/envio_item.py`, passo 3 (código no combo)

## Reprodução

`dados/temas_site.csv` tem 2 linhas `0000`; pasta `0000 - Simulado/Aluno.JPG`
com aluno exato -> antes: `EXATO_UNICO` (entrava na fila); agora: `SIMULADO`
(fora da fila) e, se chegasse ao site, `ERRO` sem clique.

## Correção

- `ler_codigos_site_csv` devolve lista (mantém repetidos).
- `envio_item`: código que aparece mais de uma vez no combo -> `ERRO`
  "repetido no combo (revisao manual)", sem selecionar e sem clicar.
- Testes: `tests/test_t27.py` (`test_main_le_codigos_com_repetidos`,
  `test_conciliacao_marca_codigo_repetido_como_simulado`,
  `test_envio_item_nao_clica_com_codigo_repetido_no_combo`).

## GitHub

Repositório sem remoto: `gh issue create` não é possível. Registro só local.
