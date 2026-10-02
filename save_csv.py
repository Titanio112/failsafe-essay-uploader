import csv
from pathlib import Path
from datetime import datetime
from test_steps import temas

dados_dir = Path("dados")
dados_dir.mkdir(exist_ok=True)
csv_path = Path("dados/temas_site.csv")

with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "texto", "data_leitura", "conta_mascarada"])
    for t in temas:
        w.writerow([t.codigo, t.texto_completo, datetime.now().strftime("%Y-%m-%d"), "usr***@test.com"[:3] + "***"])

print(f"Saved {len(temas)} themes to {csv_path}")