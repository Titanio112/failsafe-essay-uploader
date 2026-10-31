"""Exceções da plataforma."""

class CaptchaOuBloqueio(RuntimeError):
    """CAPTCHA, 2FA ou bloqueio detectado — parar lote imediatamente."""


class LoginFalhou(RuntimeError):
    """Credenciais inválidas ou página de login não carregou."""


class IdentidadeDivergente(RuntimeError):
    """Nome/e-mail logado não confere com o aluno esperado."""


class ConfirmacaoInconclusiva(RuntimeError):
    """Não foi possível confirmar envio na lista remota em 120 s."""


class BotaoEnviarAusente(RuntimeError):
    """O botão "Enviar resposta" não está na página: nada foi clicado (T48)."""
