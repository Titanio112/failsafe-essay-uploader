with open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\progresso_relatorio.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'def obter' in line or 'def marcar' in line or 'def envios_de' in line or 'def registrar_envio' in line:
        print(f"{i}: {line.strip()}")

# Print the obter function
for i, line in enumerate(lines):
    if 'def obter' in line:
        print(f"\nobter function (lines {i}-{i+15}):")
        for j in range(i, min(i+20, len(lines))):
            print(f"  {lines[j].rstrip()}")
        break