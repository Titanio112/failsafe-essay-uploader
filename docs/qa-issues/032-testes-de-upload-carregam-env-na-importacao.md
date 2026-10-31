# 032 — Dois testes de upload carregam o `.env` só por serem importados

- **Tipo:** bug de teste (segurança)
- **Status:** aberto (29/10/2026). Não mexido na M3, por decisão do Antônio.
- **Local:** `tests/test_upload_aceito_t18.py` e `tests/test_upload_sinal.py` (linhas 28-29)
- **Encontrado em:** 29/10/2026, no diagnóstico da M1 (incidente do `.env`)

## Descrição

Os dois arquivos chamam `load_dotenv()` no nível do módulo. O pytest importa
todo arquivo de teste na coleta, então **qualquer** `pytest` rodado na pasta
do projeto (até `--collect-only` e a suíte `-m "not real"`, em que esses
testes nem rodam) carrega o `.env` real na memória do processo. O
`test_upload_aceito_t18.py` ainda copia e-mail e senha de teste para
variáveis globais do módulo.

Enquanto isso não for corrigido, a suíte offline só roda numa cópia do
projeto sem `.env` (regra do item 0 da M3).

## Reprodução

```
# na pasta do projeto, com um .env presente
python -m pytest --collect-only -q tests/test_upload_sinal.py
# a importação já executou load_dotenv(): o .env está no ambiente do processo
```

## Correção proposta

Carregar o `.env` só dentro dos testes `real` (fixture que chama
`load_dotenv()` quando o teste roda) e ler e-mail/senha na hora, nunca na
importação. Depois, um teste estático que barre `load_dotenv()` fora de
função em `tests/`.
