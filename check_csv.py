import csv
from collections import Counter

rows = list(csv.reader(open(r'D:\%USERNAME%\Documents\VS-CODE\Ambientes\esquema\automacao-redacoes\dados\temas_site.csv', encoding='utf-8-sig')))
print('Total lines:', len(rows))
codes = [r[0] for r in rows[1:]]
dup = Counter(codes)
dups = {k:v for k,v in dup.items() if v>1}
print('Duplicados:', dups)
print('Codigos unicos:', len(set(codes)))
nums = [int(c) for c in codes if c.isdigit()]
print('Max codigo numerico:', max(nums) if nums else 'N/A')
missing = set(range(1,102)) - set(nums)
print('Faltando 1-101:', sorted(missing) if missing else 'Nenhum')