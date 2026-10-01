import json
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_content.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_part5.txt', 'w', encoding='utf-8') as f:
    f.write(''.join(lines[450:650]))
print("Done")