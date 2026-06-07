"""Tests for models/session.py — in-memory session state."""

import pytest

from models.session import Session


class TestSession:

    def setup_method(self):
        Session.logout()

    def teardown_method(self):
        Session.logout()

    # ------------------------------------------------------------------
    # Initial state
    # ------------------------------------------------------------------

    def test_not_logged_in_initially(self):
        assert not Session.is_logged_in()

    def test_get_user_raises_when_not_logged_in(self):
        with pytest.raises(RuntimeError):
            Session.get_user()

    def test_get_current_user_id_raises_when_not_logged_in(self):
        with pytest.raises(RuntimeError):
            Session.get_current_user_id()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def test_login_sets_logged_in(self):
        Session.login({"id": 1, "username": "alice", "token": "tok"})
        assert Session.is_logged_in()

    def test_login_stores_full_user_dict(self):
        user = {"id": 1, "username": "alice", "token": "tok"}
        Session.login(user)
        assert Session.get_user() == user

    def test_get_current_user_id_after_login(self):
        Session.login({"id": 42, "username": "bob", "token": "t"})
        assert Session.get_current_user_id() == 42

    def test_login_overwrites_previous_user(self):
        Session.login({"id": 1, "username": "alice", "token": "a"})
        Session.login({"id": 2, "username": "bob", "token": "b"})
        assert Session.get_current_user_id() == 2
        assert Session.get_user()["username"] == "bob"

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def test_logout_clears_state(self):
        Session.login({"id": 1, "username": "alice", "token": "tok"})
        Session.logout()
        assert not Session.is_logged_in()

    def test_get_user_raises_after_logout(self):
        Session.login({"id": 1, "username": "alice", "token": "tok"})
        Session.logout()
        with pytest.raises(RuntimeError):
            Session.get_user()

    def test_get_current_user_id_raises_after_logout(self):
        Session.login({"id": 1, "username": "alice", "token": "tok"})
        Session.logout()
        with pytest.raises(RuntimeError):
            Session.get_current_user_id()

    def test_double_logout_is_safe(self):
        Session.logout()
        Session.logout()
        assert not Session.is_logged_in()
