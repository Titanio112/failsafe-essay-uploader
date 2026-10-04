"""Playwright: login, identidade, diagnóstico, upload, envio e logout.

Fase 1: somente a trava de envio está ativa. As rotinas web serão
implementadas na Fase 2 (diagnóstico) e Fase 3 (envio), após autorização.

Referência (scripts antigos, somente leitura, não alterar):
- Login Rails/devise: POST /auth/users/sign_in com authenticity_token
  obtido do form GET; cookies de sessão via requests.Session.
- Após login há seleção de escola (main.py antigo).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config import Config, exigir_envio_real
from planilha_arquivos import Aluno

# Re-exportar de novos módulos
from excecoes import (
    CaptchaOuBloqueio,
    LoginFalhou,
    IdentidadeDivergente,
    UploadNaoConfirmado,
    ConfirmacaoInconclusiva,
)
from login import (
    DOMINIO_ESPERADO,
    verificar_dominio_autorizado,
    login,
    confirmar_identidade,
)
from lista_redacoes import (
    ItemListaRedacao,
    ler_saldo_creditos,
    ler_lista_redacoes,
    verificar_duplicidade,
    contar_linhas_codigo_data,
    ler_lista_redacoes_html,
    detectar_ja_enviado,
)
from formulario_envio import (
    abrir_formulario_envio,
    ler_combo_temas,
    selecionar_tema_por_codigo,
    selecionar_criterio,
    anexar_arquivo,
    aguardar_upload_aceito,
)
from confirmacao import (
    clicar_enviar,
    aguardar_confirmacao,
    logout,
)

# Estruturas locais que os testes esperam
@dataclass
class TemaCombo:
    """Uma opção do combo 'Informe o tema da redação'."""
    codigo: str
    texto_completo: str

# Fim das re-exportações - funções movidas para módulos separados
