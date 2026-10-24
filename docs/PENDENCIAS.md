# PENDENCIAS.md — pontos em aberto (só o que ainda vale)

Atualizado em 22/10/2026 (depois da T50).
Regra: ponto aberto aqui não se resolve no chute; observar no site ou o
Antônio decide.

## Site (não observado ainda)

1. **Lista de uma conta sem nenhuma redação.** HTML nunca observado. Hoje:
   página sem tabela = lista vazia = pode enviar (decisão D1 (a), 21/10). Se
   vier uma linha-aviso com `<td>`, o envio é bloqueado (fail-closed) até
   observar e ajustar.
2. **Outros valores de Situação** além de "Processando arquivo" e
   "Pendente" (e "Cancelada", que a contagem já descarta). Na confirmação, sem linha nova Pendente/Processando no prazo →
   `REVISAO_MANUAL`.
3. **Paginação da lista `/minhas-redacoes`.** Nunca observada. Desde a T44,
   página com paginação → fail-closed (não envia). Se aparecer, observar o
   HTML e decidir como ler as outras páginas.
4. ~~Critério ENEM conferido (T44)~~ e 5. ~~página da lista (T48)~~:
   conferidos no site real no ensaio de 23/10 02:17 (3 enviadas, Pendente) ✔.

## Decisões do Antônio

6. **`--analise-remota --conta-aluno EMAIL`** entra na conta de um aluno de
   verdade (só leitura do combo de temas), mesmo com `PRODUCAO_BLOQUEADA =
   True`. A regra de 22/10 diz que IA nenhuma faz login em conta de aluno; o
   script só faz isso quando o Antônio roda e digita `ANALISAR`. Decidir:
   manter assim, ou bloquear também enquanto a produção estiver bloqueada.
7. **T25 — 1º envio real de produção** (1 aluno, 1 redação): suspenso
   enquanto `PRODUCAO_BLOQUEADA = True` (T30). Antes: rodar o ensaio
   (`python main.py --ensaio 3 --envio-real`) e revisar a branch
   `revisao-autonoma` (T42–T50).

## T52 (23/10)

- Ctrl+clique com o link novo: conferir no terminal do VS Code (e no Windows
  Terminal) se a foto abre. Se não abrir, usar `v` na revisão/resolver.
- `--conferir-site` rodou no site real em 23/10 (36 alunos, 0 falhas) ✔.
  Falta ver o "talvez com outro tema" (T53) numa conferência real.
- Redações antigas da pasta já foram enviadas à mão (data incerta): antes de
  liberar a produção, tirar da pasta ou conferir com `--conferir-site`.
- Ideia não feita: marcar no caderno, a partir da conferência, as que já
  estão no site (hoje é só relatório; pede decisão do Antônio).
- Ideia para depois (Antônio, 23/10): nos créditos do menu, o nome dele
  como link clicável (GitHub). Não fazer agora.

## T55 (23/10)

- Ensaio no site real ✔ (23/10 02:17, 3 enviadas e confirmadas): critério ENEM,
  página da lista e progresso ao vivo conferidos.
- `v` (ver a foto): testar no menu 4 -> r (a pasta de teste tem um "nome parecido").

## T57 (23/10)

- **Decisão do Antônio (vai conferir):** a filiação foi mandada à mão como
  tema 000, mas a pasta está aprovada como 100 (o tema existe no site).
  Nas próximas, qual vale? Muda o que a correção recebe.
- O caderno identifica a redação por pasta/arquivo: redação nova com o mesmo
  nome de pasta e arquivo de uma já enviada é pulada (seguro, com aviso).
  Usar nomes de pasta novos a cada lote (ex.: com a data).
- `v` nos temas e nos nomes: testar de novo no menu 4 -> r.

