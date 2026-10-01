import json
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma.py', 'rb') as f:
    c = f.read()
text = c.decode('utf-8', errors='replace')
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\plataforma_content.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Done")