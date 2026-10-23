# PENDENCIAS.md — pontos em aberto (só o que ainda vale)

Atualizado em 22/10/2026 (depois da T50). O arquivo antigo de decisões
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
5. **Conferência da página da lista (T48)** nunca rodou no site real: HTTP
   < 400, caminho `/minhas-redacoes` e texto "Você tem N crédito(s)". Só
   testada com a fixture `tests/fixtures/minhas_redacoes.html`, que tem o
   texto do saldo ("Você tem 18 crédito(s)"). Se o primeiro ensaio der
   "Pagina sem o saldo de creditos" ou "Pagina inesperada", observar o
   HTML antes de mexer.

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

