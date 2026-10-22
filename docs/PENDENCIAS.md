# PENDENCIAS.md — pontos em aberto (só o que ainda vale)

Atualizado em 22/10/2026 (depois da T46). O arquivo antigo de decisões
(01–06/10) está em `docs/historico/DECISOES_PENDENTES.md`, só como histórico.
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
4. **Critério ENEM conferido (T44)** nunca rodou no site real (só fixture
   `wordings_new.html`). O primeiro ensaio/envio de teste confirma; se der
   "Criterio ENEM nao conferido", observar o HTML antes de mexer.

## Decisões do Antônio

5. **`--analise-remota --conta-aluno EMAIL`** entra na conta de um aluno de
   verdade (só leitura do combo de temas), mesmo com `PRODUCAO_BLOQUEADA =
   True`. A regra de 22/10 diz que IA nenhuma faz login em conta de aluno; o
   script só faz isso quando o Antônio roda e digita `ANALISAR`. Decidir:
   manter assim, ou bloquear também enquanto a produção estiver bloqueada.
6. **T25 — 1º envio real de produção** (1 aluno, 1 redação): suspenso
   enquanto `PRODUCAO_BLOQUEADA = True` (T30). Antes: rodar o ensaio
   (`python main.py --ensaio 3 --envio-real`) e revisar a branch
   `revisao-autonoma` (T42–T46).
