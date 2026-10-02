import sys
sys.path.insert(0, r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes')

with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\write_phase2_final.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\fase2_mapeamento.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File copied successfully")