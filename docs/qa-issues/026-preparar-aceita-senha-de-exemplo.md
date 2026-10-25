# 026 — --preparar marcava "Senhas ✔" com o .env de exemplo

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/ferramentas/primeiro_uso.py`, `modulos/base/config.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

O `.env` copiado do `.env.example` tem `<definir-no-.env>`. O guia marcava ✔ só porque o arquivo existia, e o script tentava login com o texto de exemplo como senha.

## Reprodução

`--preparar` num clone novo: "Senhas ✔" sem nada preenchido.

## Correção

✔ só com as 3 variáveis preenchidas e sem o valor de exemplo; valor começando com "<" conta como ausente (o script pergunta a senha).
