"""Testes offline do critério de sucesso do login (sem navegador real)."""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from playwright.sync_api import Page

from modulos.site.login import login
from modulos.base.excecoes import LoginFalhou
import modulos.site.login as login_module


class MockLocator:
    """Mock para page.locator()."""
    def __init__(self, should_find=True, text_content=""):
        self._should_find = should_find
        self._text_content = text_content
        self.called = False

    def wait_for(self, timeout=5000):
        self.called = True
        if not self._should_find:
            from playwright.sync_api import TimeoutError as PWTimeoutError
            raise PWTimeoutError("Timeout")

    @property
    def first(self):
        return self


def test_login_sucesso_destino_raiz_com_saldo():
    """Destino '/' com saldo visível → sucesso."""
    mock_page = MagicMock(spec=Page)
    # Use PropertyMock for URL since it's a property
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/")
    
    # Mock para saldo visível
    mock_saldo = MockLocator(should_find=True)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        login(mock_page, MagicMock(), "test@test.com", "senha")
    
    # Deve ter navegado para /minhas-redacoes
    assert mock_page.goto.call_count == 2
    # Segunda chamada deve ser para /minhas-redacoes
    args, _ = mock_page.goto.call_args
    assert "/minhas-redacoes" in args[0]
    # Não deve ter levantado exceção


def test_login_sucesso_destino_minhas_redacoes():
    """Destino '/minhas-redacoes' → sucesso."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/minhas-redacoes")
    
    mock_saldo = MockLocator(should_find=True)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        login(mock_page, MagicMock(), "test@test.com", "senha")
    
    assert "sign_in" not in mock_page.url


def test_login_sucesso_destino_alunos_x_com_saldo():
    """Destino '/alunos/x' com saldo → sucesso (página válida pós-login)."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/alunos/123")
    
    mock_saldo = MockLocator(should_find=True)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        login(mock_page, MagicMock(), "test@test.com", "senha")
    
    assert "sign_in" not in mock_page.url


def test_login_falha_permanece_sign_in_com_erro():
    """Continua em sign_in com mensagem de erro → LoginFalhou."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/auth/users/sign_in")
    
    mock_saldo = MockLocator(should_find=False)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        with pytest.raises(LoginFalhou) as exc:
            login(mock_page, MagicMock(), "test@test.com", "senha")
    
    assert "Permaneceu na página de login" in str(exc.value)
    assert "sign_in" in str(exc.value)


def test_login_falha_minhas_redacoes_redireciona_para_sign_in():
    """/minhas-redacoes redireciona para sign_in → LoginFalhou."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/auth/users/sign_in")
    
    mock_saldo = MockLocator(should_find=False)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        with pytest.raises(LoginFalhou) as exc:
            login(mock_page, MagicMock(), "test@test.com", "senha")
    
    assert "Permaneceu na página de login" in str(exc.value)


def test_login_falha_sem_saldo_sem_menu_usuario():
    """URL não é sign_in, mas sem saldo e sem menu do usuário → LoginFalhou."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/minhas-redacoes")
    
    mock_saldo = MockLocator(should_find=False)
    mock_usuario = MockLocator(should_find=False)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        with pytest.raises(LoginFalhou) as exc:
            login(mock_page, MagicMock(), "test@test.com", "senha")
    
    assert "Login incerto" in str(exc.value)
    assert "sem saldo visível e sem menu do usuário" in str(exc.value)


def test_login_sucesso_apenas_menu_usuario_sem_saldo():
    """Sem saldo, mas com menu do usuário → sucesso."""
    mock_page = MagicMock(spec=Page)
    type(mock_page).url = PropertyMock(return_value="https://www.esquemaredacao.com.br/minhas-redacoes")
    
    mock_saldo = MockLocator(should_find=False)
    mock_usuario = MockLocator(should_find=True)
    mock_page.locator.side_effect = [mock_saldo, mock_usuario]
    
    with patch.object(login_module, 'verificar_dominio_autorizado'):
        login(mock_page, MagicMock(), "test@test.com", "senha")
    
    # Não deve ter levantado exceção


if __name__ == "__main__":
    pytest.main([__file__, "-v"])