# 028 — Pastas e redações que entram, mudam e saem com o tempo

- **Tipo:** sugestão de melhoria (ideia para o futuro)
- **Status:** aberta; nada implementado ainda
- **Local:** `Redações plataforma/`, `dados/pastas_aprovadas.csv`, `dados/nomes_aprovados.csv`, `relatorios/progresso.db`
- **Registrado em:** 25/10/2026, ideia do Antônio

## Descrição

O uso real vai ter rotatividade: chegam lotes novos de redações, pastas
de tema são trocadas, crescem ou são apagadas depois do envio. Hoje o
script guarda informação presa ao **nome** da pasta e do arquivo:

- `pastas_aprovadas.csv` liga o nome da pasta a um tema. A pasta apagada
  deixa uma linha velha; uma pasta nova com o mesmo nome herda a aprovação
  antiga (talvez de outro tema).
- O caderno (`progresso.db`) identifica a redação por pasta/arquivo. Uma
  redação nova com o mesmo nome de uma já enviada é pulada (seguro, mas
  confunde; ver T57).
- `nomes_aprovados.csv` acumula nomes de alunos que já saíram da lista.
- O arquivo morto (menu 11) tira as pastas antigas, mas as aprovações e o
  caderno continuam apontando para elas.

## Ideias de solução (para decidir depois)

1. **Lote com data:** cada leva de redações numa pasta com a data
   (ex.: `2026-11-03 - 000 - Aporofobia`), para nunca repetir nome.
2. **Limpeza das aprovações:** ao arquivar uma pasta, marcar ou mover a
   linha dela em `pastas_aprovadas.csv` (nada apagado, com log).
3. **Aprovação presa ao conteúdo:** guardar junto da aprovação a data e a
   quantidade de fotos; pasta que mudou muito pede nova confirmação.
4. **Relatório de sobras:** mostrar na conferência as linhas de aprovação e
   os nomes aprovados que não aparecem mais em nenhuma pasta.
5. **Caderno pelo conteúdo:** usar o sha256 da foto (já gravado desde a T44)
   como identidade principal, em vez do nome do arquivo.

Nada disso muda as regras de segurança: na dúvida, não envia.
