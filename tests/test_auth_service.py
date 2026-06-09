"""Tests for services/auth_service.py — APIClient mocked."""

from unittest.mock import MagicMock, patch

import pytest

from services.auth_service import AuthService


@pytest.fixture
def service():
    with patch("services.auth_service.APIClient") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        svc = AuthService()
        yield svc, mock_client


class TestSignUp:

    def test_success_returns_user_dict(self, service):
        svc, mock_client = service
        mock_client.register.return_value = {"id": 1, "username": "alice"}
        result = svc.sign_up("alice", "pass123")
        assert result["username"] == "alice"

    def test_passes_num_years_and_credits(self, service):
        svc, mock_client = service
        mock_client.register.return_value = {"id": 1}
        svc.sign_up("alice", "pass", num_years=4, credit_requirements=[30, 30, 30, 30])
        mock_client.register.assert_called_once_with("alice", "pass", 4, [30, 30, 30, 30])

    def test_propagates_value_error_from_client(self, service):
        svc, mock_client = service
        mock_client.register.side_effect = ValueError("username taken")
        with pytest.raises(ValueError, match="username taken"):
            svc.sign_up("alice", "pass")

    def test_wraps_unexpected_exceptions_as_value_error(self, service):
        svc, mock_client = service
        mock_client.register.side_effect = RuntimeError("network down")
        with pytest.raises(ValueError, match="Registration failed"):
            svc.sign_up("alice", "pass")


class TestLogin:

    def test_returns_user_dict_with_id_username_token(self, service):
        svc, mock_client = service
        mock_client.login.return_value = "tok123"
        mock_client.get_profile.return_value = {"username": "alice"}
        mock_client.user_id = 7
        result = svc.login("alice", "pass")
        assert result == {"id": 7, "username": "alice", "token": "tok123"}

    def test_calls_client_login_then_get_profile(self, service):
        svc, mock_client = service
        mock_client.login.return_value = "tok"
        mock_client.get_profile.return_value = {"username": "alice"}
        mock_client.user_id = 1
        svc.login("alice", "pass")
        mock_client.login.assert_called_once_with("alice", "pass")
        mock_client.get_profile.assert_called_once()

    def test_propagates_value_error_from_client(self, service):
        svc, mock_client = service
        mock_client.login.side_effect = ValueError("bad credentials")
        with pytest.raises(ValueError, match="bad credentials"):
            svc.login("alice", "wrong")

    def test_wraps_unexpected_exceptions_as_value_error(self, service):
        svc, mock_client = service
        mock_client.login.side_effect = ConnectionError("timeout")
        with pytest.raises(ValueError, match="Login failed"):
            svc.login("alice", "pass")
