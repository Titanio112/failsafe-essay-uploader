"""Exceções da plataforma."""

class CaptchaOuBloqueio(RuntimeError):
    """CAPTCHA, 2FA ou bloqueio detectado — parar lote imediatamente."""


class LoginFalhou(RuntimeError):
    """Credenciais inválidas ou página de login não carregou."""


class IdentidadeDivergente(RuntimeError):
    """Nome/e-mail logado não confere com o aluno esperado."""


class UploadNaoConfirmado(RuntimeError):
    """Mensagem de upload aceito não apareceu no tempo esperado."""


class ConfirmacaoInconclusiva(RuntimeError):
    """Não foi possível confirmar envio na lista remota em 120 s."""