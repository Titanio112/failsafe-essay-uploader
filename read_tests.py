# Ler o arquivo de testes
with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\tests\test_essenciais.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Encontrar a fixture pasta_arquivos_temporaria
for i, line in enumerate(lines):
    if 'pasta_arquivos_temporaria' in line and 'def ' in line:
        print(f"Linha {i}: {line.strip()}")
        # Imprimi as próximas 30 linhas
        for j in range(i, min(i+35, len(lines))):
            print(f"{j}: {lines[j].rstrip()}")
        break