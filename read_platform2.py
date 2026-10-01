import json
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_content.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_part.txt', 'w', encoding='utf-8') as f:
    f.write(''.join(lines[80:300]))
print("Done")