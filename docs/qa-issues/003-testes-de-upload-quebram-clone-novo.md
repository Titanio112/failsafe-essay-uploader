# 003 — Testes de upload quebram a coleta num clone novo

- **Tipo:** bug de teste
- **Status:** resolvido em 24/10/2026 (commit "test: testes de upload pulam quando faltam os JPGs locais")
- **Local:** `tests/test_upload_aceito_t18.py`, `tests/test_upload_sinal.py`
- **Encontrado em:** 24/10/2026, ao rodar os testes numa cópia nova para publicar no GitHub

## Descrição

Os dois arquivos faziam `assert JPGS` no nível do módulo. Os JPGs de teste
(`testes/redacoes_teste/0 - Narração/`) ficam fora do git, então num clone
novo a **coleta inteira** do pytest parava com 2 erros, e até
`pytest -m "not real"` falhava. `tests/test_imports_reais.py` também caía,
porque roda `--collect-only -m real` e exige que os dois testes apareçam.

## Reprodução

```
git clone <repo> && cd <repo>
python -m pytest -m "not real" -q
# ERROR collecting tests/test_upload_aceito_t18.py ... Nenhum JPG encontrado
```

## Correção

`pytestmark = pytest.mark.skipif(not JPGS, ...)` e `ARQUIVO_TESTE = JPGS[0] if JPGS else None`.
Os testes continuam sendo coletados (o `test_imports_reais` passa) e são
pulados quando faltam as fotos locais. Resultado: `415 passed, 4 deselected`.
