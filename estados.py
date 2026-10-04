"""Constantes de estado para conciliação de arquivos.

Estados de cada arquivo conciliado:

- ``EXATO_UNICO``: correspondência normalizada exata e única com um aluno.
- ``SUGESTAO_FUZZY``: melhor candidato aproximado acima do limiar e com
  margem para o segundo. NUNCA entra na fila real sem revisão humana.
- ``AMBIGUO``: correspondência exata com mais de um aluno, ou fuzzy com
  margem insuficiente / mais de um candidato no limiar.
- ``ARQUIVO_SEM_ALUNO``: nenhum candidato acima do limiar.
- ``ALUNO_SEM_ARQUIVO``: aluno da sala sem nenhum arquivo associado.
- ``SEM_CODIGO``: arquivo sem código no nome nem na pasta.
- ``CODIGO_INVALIDO``: código extraído não existe no combo do site.
- ``REVISAO_MANUAL``: casos que exigem revisão humana (duplicatas, conflitos, etc.)
- ``SIMULADO``: estado usado em testes simulados.
"""

EXATO_UNICO = "EXATO_UNICO"
SUGESTAO_FUZZY = "SUGESTAO_FUZZY"
AMBIGUO = "AMBIGUO"
ARQUIVO_SEM_ALUNO = "ARQUIVO_SEM_ALUNO"
ALUNO_SEM_ARQUIVO = "ALUNO_SEM_ARQUIVO"
SEM_CODIGO = "SEM_CODIGO"
CODIGO_INVALIDO = "CODIGO_INVALIDO"
REVISAO_MANUAL = "REVISAO_MANUAL"
SIMULADO = "SIMULADO"

ESTADOS_CONCILIACAO = (
    EXATO_UNICO,
    SUGESTAO_FUZZY,
    AMBIGUO,
    ARQUIVO_SEM_ALUNO,
    ALUNO_SEM_ARQUIVO,
    SEM_CODIGO,
    CODIGO_INVALIDO,
    REVISAO_MANUAL,
    SIMULADO,
)

MARCADOR_PESSOA = " - Red"