"""Sinal entre a conferência (main) e o menu, sem passar por código de saída (issue #52)."""

# True quando a última conferência deixou temas ou nomes para a Revisão resolver
revisao_pendente = False

# True quando a conferência manual mudou o alunos.csv: a conferência no site precisa ser refeita (issue #56)
cadastro_mudou = False
