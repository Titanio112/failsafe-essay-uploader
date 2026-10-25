# 016 — Arquivo morto deixava a pasta pela metade com uma foto aberta

- **Tipo:** bug de ferramenta
- **Status:** resolvido em 25/10/2026 (T58; testes em `tests/test_t58.py`)
- **Local:** `modulos/ferramentas/arquivo_morto.py`
- **Encontrado em:** 24/10/2026, na auditoria do código (5 frentes, cada achado conferido por 2 verificadores)

## Descrição

`shutil.move` tenta renomear; se falha (no Windows, qualquer foto aberta na pasta), copia tudo e apaga a origem. O apagar parava na foto aberta: a pasta de trabalho ficava sem parte das fotos, o arquivo morto com todas, o log sem linha e a tela dizia "Não movi".

## Reprodução

Pasta com 3 fotos e b.jpg aberta: origem ficou com 2, arquivo morto com 3, log vazio.

## Correção

No mesmo disco só renomeia: falhou, nada muda e a tela diz para fechar a foto. Em outro disco copia, confere a cópia e só então tira a origem; se a origem não sair toda, avisa e registra no log.
