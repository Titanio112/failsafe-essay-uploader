# 030 — Marcar pastas já enviadas e liberar a limpeza só depois de conferir no site

- **Tipo:** sugestão de melhoria (ideia para o futuro)
- **Status:** feito em 25/10/2026 (T60; testes em `tests/test_t60.py`)
- **Local:** `Redações plataforma/`, menu 5 (conferir no site), menu 11 (arquivo morto)
- **Registrado em:** 25/10/2026, ideia do Antônio

## Descrição

Hoje não dá para saber, olhando a pasta, se as redações dela já foram para a
plataforma. A ideia: depois do envio, marcar a pasta de um jeito visível
(ex.: `ENVIADA - 53 - Impactos da evasão escolar`). Quem abre a pasta vê na
hora o que já foi e pode ser limpo.

Para ficar seguro, a limpeza só é liberada depois de o script **conferir no
site** que cada redação daquela pasta está mesmo lá (menu 5). Sem essa
conferência, nada sai do lugar.

## Cuidados (para decidir antes de fazer)

1. **O caderno usa o nome da pasta.** `relatorios/progresso.db` identifica a
   redação por pasta/arquivo. Renomear a pasta sem cuidado faria o script
   achar que as redações são novas. A marca precisa ir junto no caderno
   (ou o caderno passar a usar a foto, sha256: ver a 028).
2. **Nada é apagado.** A regra do projeto é mover para o arquivo morto
   (menu 11), com log, e não apagar. "Limpar" seria: conferir no site ->
   marcar como enviada -> oferecer mover para o arquivo morto.
3. **Pasta pela metade.** Se só parte das redações da pasta estiver no site,
   a pasta não é marcada; o script mostra quais faltam.

## Ideia de fluxo

1. Enviar (menu 6) ou enviar as que faltam (menu 7).
2. Conferir no site (menu 5): pastas com TODAS as redações no site ganham
   a marca "enviada" (com log).
3. Arquivo morto (menu 11) passa a sugerir primeiro as pastas marcadas.

Relacionada: 028 (pastas que entram, mudam e saem com o tempo) e o item 2 da
conversa de 25/10 (renomear a pasta para o nome do tema do site ao aprovar).

## Como ficou (T60)

- No fim da conferência no site (menu 5), as pastas em que **todas** as fotos
  foram conferidas e estão "no site" são listadas; com `s`, viram
  `ENVIADA - <nome>` (log em `relatorios/pastas_enviadas_<data>.csv`).
  Conferência que parou não marca nada.
- Cuidado 1 resolvido sem mexer no caderno: pastas `ENVIADA - ...` ficam fora
  de tudo (envio, revisão, conferência), então não há como reenviar.
- Cuidado 2: nada é apagado. O arquivo morto (menu 11) mostra primeiro as
  marcadas ("✔ conferida no site") e `e` arquiva só elas.
- Cuidado 3: pasta com qualquer foto faltando, em parte, outro tema,
  cancelada, sem conferir ou sem aluno nunca é marcada.
- Prova numa cópia: pasta marcada saiu do dry-run (4 -> 3 pastas, 126 -> 96
  prontas) e apareceu em 1º no arquivo morto.
