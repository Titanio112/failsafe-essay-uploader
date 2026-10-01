import json
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_content.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_part6.txt', 'w', encoding='utf-8') as f:
    f.write(''.join(lines[550:750]))
print("Done")