with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\progresso_relatorio.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Print envios_de function
for i, line in enumerate(lines):
    if 'def envios_de' in line:
        print(f"envios_de function (lines {i}-{i+15}):")
        for j in range(i, min(i+20, len(lines))):
            print(f"  {lines[j].rstrip()}")
        break

# Print marcar function to see what estado values are valid
for i, line in enumerate(lines):
    if 'def marcar' in line:
        print(f"\nmarcar function (lines {i}-{i+30}):")
        for j in range(i, min(i+35, len(lines))):
            print(f"  {lines[j].rstrip()}")
        break