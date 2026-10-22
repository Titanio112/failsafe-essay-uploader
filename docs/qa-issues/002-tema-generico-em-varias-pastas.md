# 002 — Tema genérico (000) em várias pastas trava os envios do aluno

- **Tipo:** lógico (conciliação + duplicidade)
- **Status:** aberto, aguardando decisão do Antônio
- **Local:** `modulos/planilha_arquivos.py` (`conciliar`, contagem aluno+código),
  `modulos/fila_producao.py` (um arquivo por aluno+código),
  `modulos/envio_item.py` (duplicidade "mesmo dia + mesmo tema"),
  `modulos/confirmacao.py` (confirmação procura código + data de hoje)

## Descrição

Na T32 as pastas cujo tema não existe na plataforma passam a usar o tema
genérico `000- DISSERTATIVO ARGUMENTATIVO`. Hoje as regras supõem que cada
código aparece no máximo uma vez por aluno:

1. Na conciliação, o mesmo aluno com o mesmo código em duas pastas vira
   `REVISAO_MANUAL` nas duas, e nada desse aluno no tema 000 entra na fila.
2. Mesmo liberando a conciliação, no envio a segunda redação 000 do mesmo dia
   seria vista como "já enviada" (mesmo dia + mesmo tema) e marcada
   `JA_ENVIADO` sem ter sido enviada.
3. A confirmação poderia achar a linha da primeira redação 000 do dia.

## Reprodução

```
conciliar([ANA], {"3B - Aporofobia": ["ANA....JPG"], "3B - Discriminacao": ["ANA....JPG"]},
          codigos_site=["000"], codigos_pasta={"3B - Aporofobia": "000", "3B - Discriminacao": "000"})
-> as duas: REVISAO_MANUAL
```

## Opções (decisão do Antônio)

- **A (recomendada):** uma redação por aluno e por tema **por dia**; as outras
  do mesmo tema ficam "para amanhã" (estado novo, nunca marcadas como enviadas).
  A regra "mesmo dia + mesmo tema = já enviado" continua valendo.
- **B:** enviar todas no mesmo dia; a duplicidade passa a contar as linhas
  do tema no dia (antes/depois). Mais rápido, mais frágil.
