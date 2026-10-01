import pathlib
base = pathlib.Path('.')
dirs = ['redacoes_pendentes','testes/redacoes_teste','dados','logs','relatorios','diagnosticos']
for d in dirs:
    p = base.joinpath(d)
    g = p.joinpath('.gitkeep')
    print(f'{d}: exists={p.exists()}, gitkeep={g.exists()}')