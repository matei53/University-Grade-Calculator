"""
Tests for _SignupWorker in ui/screens/signup_screen.py.

The worker is tested by calling .run() directly (synchronous, no actual thread
spawning) with all external services mocked. A QApplication is required for
PyQt6 signals to work and is provided by the session-scoped fixture in conftest.py.
"""

import pytest

pytest.importorskip("PyQt6")

from unittest.mock import patch

from ui.screens.signup_screen import _SignupWorker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _worker(
    username="alice",
    password="pass",
    num_years=3,
    credits=None,
    uni_id=None,
    major_id=None,
    custom_uni="",
    custom_major="",
):
    return _SignupWorker(
        username,
        password,
        num_years,
        credits or [60, 60, 60],
        uni_id,
        major_id,
        custom_uni,
        custom_major,
    )


def _capture(worker):
    """Return lists that collect success/failure signal emissions."""
    success, failure = [], []
    worker.success.connect(lambda tok, cu, cm: success.append((tok, cu, cm)))
    worker.failure.connect(failure.append)
    return success, failure


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestSignupWorkerSuccess:

    def test_emits_success_with_token(self, qapp):
        w = _worker(uni_id=1, major_id=2)
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.Session"
        ):
            mock_auth = MockAuth.return_value
            mock_auth.sign_up.return_value = {"access_token": "tok123"}
            mock_auth.client.get_profile.return_value = {"id": 1}
            w.run()

        assert not failure
        assert len(success) == 1
        assert success[0][0] == "tok123"

    def test_no_custom_fields_flags_are_false(self, qapp):
        w = _worker(uni_id=1, major_id=2)
        success, _ = _capture(w)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.Session"
        ):
            MockAuth.return_value.sign_up.return_value = {"access_token": "t"}
            MockAuth.return_value.client.get_profile.return_value = {"id": 1}
            w.run()

        _tok, used_uni, used_major = success[0]
        assert used_uni is False
        assert used_major is False

    def test_custom_university_resolved_and_flag_set(self, qapp):
        w = _worker(custom_uni="MIT", major_id=2)
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.DataService"
        ) as MockData, patch("ui.screens.signup_screen.Session"):
            MockData.add_university.return_value = 99
            MockAuth.return_value.sign_up.return_value = {"access_token": "t"}
            MockAuth.return_value.client.get_profile.return_value = {"id": 1}
            w.run()

        assert not failure
        MockData.add_university.assert_called_once_with("MIT")
        assert success[0][1] is True  # used_custom_uni

    def test_custom_major_resolved_and_flag_set(self, qapp):
        w = _worker(uni_id=1, custom_major="CS")
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.DataService"
        ) as MockData, patch("ui.screens.signup_screen.Session"):
            MockData.add_major.return_value = 88
            MockAuth.return_value.sign_up.return_value = {"access_token": "t"}
            MockAuth.return_value.client.get_profile.return_value = {"id": 1}
            w.run()

        assert not failure
        MockData.add_major.assert_called_once_with("CS")
        assert success[0][2] is True  # used_custom_major

    def test_update_profile_called_with_both_ids(self, qapp):
        w = _worker(uni_id=5, major_id=10)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.Session"
        ):
            mock_auth = MockAuth.return_value
            mock_auth.sign_up.return_value = {"access_token": "t"}
            mock_auth.client.get_profile.return_value = {"id": 1}
            w.run()

        mock_auth.client.update_profile.assert_called_once_with(university_id=5, major_id=10)

    def test_update_profile_not_called_without_ids(self, qapp):
        w = _worker()  # no uni_id, no major_id, no custom values

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.Session"
        ):
            mock_auth = MockAuth.return_value
            mock_auth.sign_up.return_value = {"access_token": "t"}
            mock_auth.client.get_profile.return_value = {"id": 1}
            w.run()

        mock_auth.client.update_profile.assert_not_called()

    def test_session_login_receives_correct_data(self, qapp):
        w = _worker(username="bob", uni_id=1, major_id=2)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth, patch(
            "ui.screens.signup_screen.Session"
        ) as MockSession:
            mock_auth = MockAuth.return_value
            mock_auth.sign_up.return_value = {"access_token": "mytoken"}
            mock_auth.client.get_profile.return_value = {"id": 42}
            w.run()

        MockSession.login.assert_called_once()
        payload = MockSession.login.call_args[0][0]
        assert payload["username"] == "bob"
        assert payload["token"] == "mytoken"
        assert payload["id"] == 42


# ---------------------------------------------------------------------------
# Failure tests
# ---------------------------------------------------------------------------


class TestSignupWorkerFailure:

    def test_custom_university_error_emits_failure_and_stops(self, qapp):
        w = _worker(custom_uni="MIT", major_id=2)
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.DataService") as MockData, patch(
            "ui.screens.signup_screen.AuthService"
        ) as MockAuth:
            MockData.add_university.side_effect = ValueError("already exists")
            w.run()

        assert failure == ["Error adding university: already exists"]
        assert not success
        MockAuth.return_value.sign_up.assert_not_called()

    def test_custom_major_error_emits_failure_and_stops(self, qapp):
        w = _worker(uni_id=1, custom_major="CS")
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.DataService") as MockData, patch(
            "ui.screens.signup_screen.AuthService"
        ) as MockAuth:
            MockData.add_major.side_effect = ValueError("duplicate")
            w.run()

        assert failure == ["Error adding major: duplicate"]
        assert not success
        MockAuth.return_value.sign_up.assert_not_called()

    def test_signup_error_emits_failure(self, qapp):
        w = _worker(uni_id=1, major_id=2)
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.AuthService") as MockAuth:
            MockAuth.return_value.sign_up.side_effect = ValueError("username taken")
            w.run()

        assert "username taken" in failure[0]
        assert not success

    def test_custom_major_not_attempted_after_university_error(self, qapp):
        w = _worker(custom_uni="MIT", custom_major="CS")
        success, failure = _capture(w)

        with patch("ui.screens.signup_screen.DataService") as MockData:
            MockData.add_university.side_effect = ValueError("bad")
            w.run()

        MockData.add_major.assert_not_called()
        assert failure
        assert not success
