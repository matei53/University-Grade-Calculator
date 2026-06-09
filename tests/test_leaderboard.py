"""Tests for leaderboard methods in client/api_client.py — all HTTP calls mocked."""

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
    c = APIClient()
    c.token = "test_token"
    return c


def _ok(payload):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = payload
    r.text = str(payload)
    return r


def _err(status, detail):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = {"detail": detail}
    r.text = detail
    return r


def _leaderboard_payload(**overrides):
    base = {
        "podium": [],
        "entries": [],
        "total": 0,
        "page": 1,
        "page_size": 2,
        "total_pages": 0,
        "current_user_visible": True,
        "filter_university": None,
        "filter_major": None,
        "filter_year_level": None,
        "current_user_year_level": 1,
        "available_year_levels": [],
    }
    base.update(overrides)
    return base


class TestGetLeaderboard:

    def test_success_returns_dict(self, client):
        payload = _leaderboard_payload()
        with patch("requests.get", return_value=_ok(payload)):
            result = client.get_leaderboard()
        assert result == payload

    def test_raises_on_non_200(self, client):
        with patch("requests.get", return_value=_err(401, "unauthorized")):
            with pytest.raises(ValueError, match="Leaderboard error"):
                client.get_leaderboard()

    def test_default_params_sent(self, client):
        with patch("requests.get", return_value=_ok(_leaderboard_payload())) as mock_get:
            client.get_leaderboard()
        params = mock_get.call_args.kwargs["params"]
        assert params["page"] == 1
        assert params["page_size"] == 2
        assert "year_level" not in params
        assert "search" not in params

    def test_year_level_included_when_provided(self, client):
        with patch("requests.get", return_value=_ok(_leaderboard_payload())) as mock_get:
            client.get_leaderboard(year_level=2)
        params = mock_get.call_args.kwargs["params"]
        assert params["year_level"] == 2

    def test_search_included_when_provided(self, client):
        with patch("requests.get", return_value=_ok(_leaderboard_payload())) as mock_get:
            client.get_leaderboard(search="alice")
        params = mock_get.call_args.kwargs["params"]
        assert params["search"] == "alice"

    def test_search_omitted_when_empty_string(self, client):
        with patch("requests.get", return_value=_ok(_leaderboard_payload())) as mock_get:
            client.get_leaderboard(search="")
        params = mock_get.call_args.kwargs["params"]
        assert "search" not in params

    def test_custom_page_and_page_size(self, client):
        with patch("requests.get", return_value=_ok(_leaderboard_payload())) as mock_get:
            client.get_leaderboard(page=3, page_size=10)
        params = mock_get.call_args.kwargs["params"]
        assert params["page"] == 3
        assert params["page_size"] == 10

    def test_university_name_field_present_in_entries(self, client):
        entry = {
            "rank": 1,
            "user_id": 1,
            "display_name": "Alice",
            "university_name": "Test University",
            "year_level": 1,
            "weighted_avg": 8.5,
            "credits": 30,
            "is_current_user": True,
        }
        payload = _leaderboard_payload(podium=[entry], total=1)
        with patch("requests.get", return_value=_ok(payload)):
            result = client.get_leaderboard()
        assert result["podium"][0]["university_name"] == "Test University"


class TestGetLeaderboardVisibility:

    def test_returns_true_when_visible(self, client):
        with patch("requests.get", return_value=_ok({"visible": True})):
            assert client.get_leaderboard_visibility() is True

    def test_returns_false_when_hidden(self, client):
        with patch("requests.get", return_value=_ok({"visible": False})):
            assert client.get_leaderboard_visibility() is False

    def test_raises_on_http_error(self, client):
        r = MagicMock()
        r.status_code = 401
        r.raise_for_status.side_effect = Exception("401 Unauthorized")
        with patch("requests.get", return_value=r):
            with pytest.raises(Exception):
                client.get_leaderboard_visibility()


class TestSetLeaderboardVisibility:

    def test_set_false_returns_false(self, client):
        with patch("requests.patch", return_value=_ok({"visible": False})):
            assert client.set_leaderboard_visibility(False) is False

    def test_set_true_returns_true(self, client):
        with patch("requests.patch", return_value=_ok({"visible": True})):
            assert client.set_leaderboard_visibility(True) is True

    def test_payload_contains_visible_field(self, client):
        with patch("requests.patch", return_value=_ok({"visible": False})) as mock_patch:
            client.set_leaderboard_visibility(False)
        payload = mock_patch.call_args.kwargs["json"]
        assert payload == {"visible": False}

    def test_raises_on_http_error(self, client):
        r = MagicMock()
        r.status_code = 401
        r.raise_for_status.side_effect = Exception("401 Unauthorized")
        with patch("requests.patch", return_value=r):
            with pytest.raises(Exception):
                client.set_leaderboard_visibility(True)
