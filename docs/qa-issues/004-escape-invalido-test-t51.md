# 004 — Escape inválido `"\C"` em test_t51

- **Tipo:** bug de teste (aviso hoje, erro numa versão futura do Python)
- **Status:** resolvido em 24/10/2026
- **Local:** `tests/test_t51.py`, linhas 31 e 55 (`\C` e `\A`)
- **Encontrado em:** 24/10/2026, no aviso do pytest ao rodar a suíte

## Descrição

O link OSC 8 termina com `ESC \`. Na string esperada estava
`f"...\033\Cecília em branco.JPG..."`: o `\C` não é um escape válido.
O teste passava por sorte, porque o Python mantém `\C` como barra + C, mas emite
`SyntaxWarning: "\C" is an invalid escape sequence`. Numa versão futura, isso vira
erro e o teste quebra.

## Reprodução

```
python -W error::SyntaxWarning -m pytest tests/test_t51.py -q
```

## Correção

`\033\\Cecília ...` (barra escapada), que é o mesmo texto, agora sem aviso.
