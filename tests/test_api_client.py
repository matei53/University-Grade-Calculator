"""Tests for client/api_client.py — all HTTP calls mocked via requests."""

from unittest.mock import MagicMock, patch

import pytest

from client.api_client import APIClient
from models.session import Session


@pytest.fixture(autouse=True)
def clean_session():
    Session.logout()
    yield
    Session.logout()


@pytest.fixture
def client():
    return APIClient()


def _ok(payload):
    """Build a mock 200 response returning payload."""
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = payload
    r.text = str(payload)
    return r


def _err(status, detail):
    """Build a mock error response."""
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {"detail": detail}
    r.text = detail
    return r


# -----------------------------------------------------------------------
# Headers
# -----------------------------------------------------------------------


class TestGetHeaders:

    def test_content_type_always_present(self, client):
        assert client._get_headers()["Content-Type"] == "application/json"

    def test_no_authorization_without_token(self, client):
        assert "Authorization" not in client._get_headers()

    def test_bearer_token_included_when_set(self, client):
        client.token = "mytoken"
        assert client._get_headers()["Authorization"] == "Bearer mytoken"

    def test_token_restored_from_logged_in_session(self, client):
        Session.login({"id": 1, "username": "alice", "token": "session_tok"})
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer session_tok"


# -----------------------------------------------------------------------
# ensure_token
# -----------------------------------------------------------------------


class TestEnsureToken:

    def test_returns_false_when_no_token(self, client):
        assert client.ensure_token() is False

    def test_returns_true_when_token_set(self, client):
        client.token = "tok"
        assert client.ensure_token() is True

    def test_restores_token_from_session(self, client):
        Session.login({"id": 1, "username": "u", "token": "from_session"})
        assert client.ensure_token() is True


# -----------------------------------------------------------------------
# register
# -----------------------------------------------------------------------


class TestRegister:

    def test_success_returns_user_dict(self, client):
        expected = {"id": 1, "username": "alice"}
        with patch("requests.post", return_value=_ok(expected)):
            result = client.register("alice", "pass")
        assert result == expected

    def test_raises_value_error_on_400(self, client):
        with patch("requests.post", return_value=_err(400, "username taken")):
            with pytest.raises(ValueError, match="Registration error"):
                client.register("alice", "pass")

    def test_credit_requirements_included_in_payload(self, client):
        with patch("requests.post", return_value=_ok({"id": 1})) as mock_post:
            client.register("alice", "pass", num_years=2, credit_requirements=[30, 30])
        payload = mock_post.call_args.kwargs["json"]
        assert payload["credit_requirements"] == [30, 30]

    def test_credit_requirements_omitted_when_none(self, client):
        with patch("requests.post", return_value=_ok({"id": 1})) as mock_post:
            client.register("alice", "pass")
        payload = mock_post.call_args.kwargs["json"]
        assert "credit_requirements" not in payload


# -----------------------------------------------------------------------
# login
# -----------------------------------------------------------------------


class TestLogin:

    def test_stores_token_on_success(self, client):
        with patch("requests.post", return_value=_ok({"access_token": "tok123"})), patch(
            "requests.get", return_value=_ok({"id": 1})
        ):
            client.login("alice", "pass")
        assert client.token == "tok123"

    def test_returns_token_string(self, client):
        with patch("requests.post", return_value=_ok({"access_token": "tok123"})), patch(
            "requests.get", return_value=_ok({"id": 1})
        ):
            result = client.login("alice", "pass")
        assert result == "tok123"

    def test_raises_value_error_on_401(self, client):
        with patch("requests.post", return_value=_err(401, "bad credentials")):
            with pytest.raises(ValueError, match="Login error"):
                client.login("alice", "wrong")

    def test_login_succeeds_even_if_profile_fetch_fails(self, client):
        with patch("requests.post", return_value=_ok({"access_token": "tok"})), patch(
            "requests.get", side_effect=Exception("unreachable")
        ):
            result = client.login("alice", "pass")
        assert result == "tok"


# -----------------------------------------------------------------------
# verify_token
# -----------------------------------------------------------------------


class TestVerifyToken:

    def test_returns_true_on_200(self, client):
        with patch("requests.post", return_value=_ok({})):
            assert client.verify_token("tok") is True

    def test_returns_false_on_non_200(self, client):
        with patch("requests.post", return_value=_err(401, "expired")):
            assert client.verify_token("bad") is False

    def test_returns_false_on_network_exception(self, client):
        with patch("requests.post", side_effect=Exception("timeout")):
            assert client.verify_token("tok") is False


# -----------------------------------------------------------------------
# Profile endpoints
# -----------------------------------------------------------------------


class TestProfileEndpoints:

    def test_get_profile_returns_dict(self, client):
        profile = {"id": 1, "username": "alice"}
        with patch("requests.get", return_value=_ok(profile)):
            assert client.get_profile() == profile

    def test_get_profile_raises_on_error(self, client):
        with patch("requests.get", return_value=_err(401, "unauthorized")):
            with pytest.raises(ValueError, match="Get profile error"):
                client.get_profile()

    def test_update_profile_sends_only_provided_fields(self, client):
        with patch("requests.put", return_value=_ok({})) as mock_put:
            client.update_profile(university_id=5)
        payload = mock_put.call_args.kwargs["json"]
        assert payload == {"university_id": 5}
        assert "major_id" not in payload

    def test_update_profile_raises_on_error(self, client):
        with patch("requests.put", return_value=_err(400, "bad request")):
            with pytest.raises(ValueError, match="Update profile error"):
                client.update_profile(university_id=1)


# -----------------------------------------------------------------------
# Universities / Majors
# -----------------------------------------------------------------------


class TestUniversitiesMajors:

    def test_get_universities_returns_list(self, client):
        unis = [{"id": 1, "name": "MIT"}, {"id": 2, "name": "Stanford"}]
        with patch("requests.get", return_value=_ok(unis)):
            assert client.get_universities() == unis

    def test_get_universities_raises_on_error(self, client):
        with patch("requests.get", return_value=_err(500, "server error")):
            with pytest.raises(ValueError, match="Get universities error"):
                client.get_universities()

    def test_get_majors_returns_list(self, client):
        majors = [{"id": 1, "name": "CS"}]
        with patch("requests.get", return_value=_ok(majors)):
            assert client.get_majors() == majors

    def test_get_majors_raises_on_error(self, client):
        with patch("requests.get", return_value=_err(500, "server error")):
            with pytest.raises(ValueError, match="Get majors error"):
                client.get_majors()


# -----------------------------------------------------------------------
# Academic data endpoints
# -----------------------------------------------------------------------


class TestAcademicEndpoints:

    def test_get_academic_years_returns_list(self, client):
        years = [{"id": 1, "order_index": 1, "subjects": []}]
        with patch("requests.get", return_value=_ok(years)):
            assert client.get_academic_years() == years

    def test_get_academic_years_raises_on_error(self, client):
        with patch("requests.get", return_value=_err(401, "unauthorized")):
            with pytest.raises(ValueError, match="Get academic years error"):
                client.get_academic_years()

    def test_add_subject_returns_created_subject(self, client):
        subject = {"id": 10, "name": "Math"}
        with patch("requests.post", return_value=_ok(subject)):
            result = client.add_subject("Math", 6, 1, 1)
        assert result == subject

    def test_add_subject_raises_on_error(self, client):
        with patch("requests.post", return_value=_err(400, "bad data")):
            with pytest.raises(ValueError, match="Add subject error"):
                client.add_subject("Math", 6, 1, 1)

    def test_add_assessment_returns_result(self, client):
        assessment = {"id": 5, "name": "Exam"}
        with patch("requests.post", return_value=_ok(assessment)):
            result = client.add_assessment(1, "Exam", 100.0, 8.0)
        assert result == assessment

    def test_add_assessment_raises_on_error(self, client):
        with patch("requests.post", return_value=_err(400, "bad data")):
            with pytest.raises(ValueError, match="Add assessment error"):
                client.add_assessment(1, "Exam", 100.0, 8.0)
