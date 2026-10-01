# Criar um script para ler o arquivo
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\planilha_arquivos.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(''.join(lines[224:260]))