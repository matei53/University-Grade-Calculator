"""Tests for progression settings screen and progression service.

credit passing percentage: Covers ProgressionService eligibility logic and ProgressionSettingsScreen UI behaviour
credit passing percentage: Uses in-memory SQLite via the test_db fixture from conftest.py
"""

# credit passing percentage: sys/os path manipulation removed — conftest.py handles it centrally
import importlib
import sys
from unittest.mock import MagicMock
import pytest
from server.models import AcademicYear, Assessment, Grade, Semester, Subject, User
from server.services.progression_service import ProgressionService


def _load_qt_widgets():
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication, QMessageBox

    return QApplication, QMessageBox


def _load_progression_settings_screen():
    pytest.importorskip("PyQt6")
    module = importlib.import_module("ui.screens.progression_settings_screen")
    return module.ProgressionSettingsScreen


# credit passing percentage: Define local qapp fixture for UI testing fallback
@pytest.fixture(scope="session")
def qapp():
    QApplication, _ = _load_qt_widgets()
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DummyRouter:
    def __init__(self):
        self.navigated_to = None

    def navigate(self, route):
        self.navigated_to = route


# ---------------------------------------------------------------------------
# ProgressionService tests
# ---------------------------------------------------------------------------

class TestProgressionService:
    def test_get_or_create_progression_requirement_creates_default(self, test_db):
        # credit passing percentage: Verify a fresh requirement is created with 70 % default threshold
        user = User(username="progress_user", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        requirement = ProgressionService.get_or_create_progression_requirement(
            test_db, user.id, target_year=2
        )

        assert requirement.user_id == user.id
        assert requirement.target_year == 2
        assert requirement.credit_percentage == 70.0
        assert requirement.cumulative is False

    def test_update_progression_requirement_updates_existing(self, test_db):
        # credit passing percentage: Verify updating an existing requirement changes percentage and cumulative flag
        user = User(username="progress_user2", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        first = ProgressionService.get_or_create_progression_requirement(
            test_db, user.id, target_year=2
        )

        updated = ProgressionService.update_progression_requirement(
            test_db, user.id, target_year=2, credit_percentage=85.0, cumulative=True
        )

        # credit passing percentage: Must update in-place, not create a new record
        assert updated.id == first.id
        assert updated.credit_percentage == 85.0
        assert updated.cumulative is True

    def test_check_year_eligibility_with_passing_subject(self, test_db):
        # credit passing percentage: A subject with score 80/100 (above 50 passing grade) should grant eligibility
        user = User(username="progress_user3", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year1 = AcademicYear(
            user_id=user.id,
            label="Year 1",
            order_index=1,
            credit_requirement=60,
        )
        test_db.add(year1)
        test_db.commit()
        test_db.refresh(year1)

        semester = Semester(
            academic_year_id=year1.id,
            label="Semester 1",
            order_index=1,
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        subject = Subject(
            semester_id=semester.id,
            academic_year_id=year1.id,
            name="Mathematics",
            credit_value=10,
            passing_grade=50.0,
            max_grade=100.0,
        )
        test_db.add(subject)
        test_db.commit()
        test_db.refresh(subject)

        assessment = Assessment(
            subject_id=subject.id,
            name="Final Exam",
            weight=100.0,
            max_score=100.0,
            passing_grade=50.0,
        )
        test_db.add(assessment)
        test_db.commit()
        test_db.refresh(assessment)

        grade = Grade(assessment_id=assessment.id, score=80.0)
        test_db.add(grade)
        test_db.commit()

        eligibility = ProgressionService.check_year_eligibility(test_db, user.id, target_year=2)

        assert eligibility["target_year"] == 2
        assert eligibility["is_eligible"] is True
        assert eligibility["credits_earned"] == 10
        assert eligibility["credits_required"] == 10
        assert eligibility["current_percentage"] == 100.0
        assert eligibility["required_percentage"] == 70.0
        assert eligibility["cumulative"] is False

    # credit passing percentage: Extra test: failing subject (score below passing grade) should not grant eligibility
    def test_check_year_eligibility_with_failing_subject(self, test_db):
        user = User(username="progress_user4", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year1 = AcademicYear(
            user_id=user.id, label="Year 1", order_index=1, credit_requirement=60
        )
        test_db.add(year1)
        test_db.commit()
        test_db.refresh(year1)

        semester = Semester(
            academic_year_id=year1.id, label="Semester 1", order_index=1
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        subject = Subject(
            semester_id=semester.id,
            academic_year_id=year1.id,
            name="Physics",
            credit_value=10,
            passing_grade=50.0,
            max_grade=100.0,
        )
        test_db.add(subject)
        test_db.commit()
        test_db.refresh(subject)

        assessment = Assessment(
            subject_id=subject.id,
            name="Final Exam",
            weight=100.0,
            max_score=100.0,
            passing_grade=50.0,
        )
        test_db.add(assessment)
        test_db.commit()
        test_db.refresh(assessment)

        # credit passing percentage: Score 30 is below passing grade of 50 — subject should not contribute credits
        grade = Grade(assessment_id=assessment.id, score=30.0)
        test_db.add(grade)
        test_db.commit()

        eligibility = ProgressionService.check_year_eligibility(test_db, user.id, target_year=2)

        assert eligibility["is_eligible"] is False
        assert eligibility["credits_earned"] == 0
        assert eligibility["credits_required"] == 10
        assert eligibility["current_percentage"] == 0.0

    # credit passing percentage: Extra test: cumulative mode should sum credits from all prior years
    def test_check_year_eligibility_cumulative(self, test_db):
        user = User(username="progress_user5", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # credit passing percentage: Create two academic years with one passing subject each
        for order, label in [(1, "Year 1"), (2, "Year 2")]:
            ay = AcademicYear(
                user_id=user.id, label=label, order_index=order, credit_requirement=60
            )
            test_db.add(ay)
            test_db.commit()
            test_db.refresh(ay)

            sem = Semester(academic_year_id=ay.id, label="Sem 1", order_index=1)
            test_db.add(sem)
            test_db.commit()
            test_db.refresh(sem)

            subj = Subject(
                semester_id=sem.id,
                academic_year_id=ay.id,
                name=f"Subject Y{order}",
                credit_value=10,
                passing_grade=50.0,
                max_grade=100.0,
            )
            test_db.add(subj)
            test_db.commit()
            test_db.refresh(subj)

            asmt = Assessment(
                subject_id=subj.id,
                name="Exam",
                weight=100.0,
                max_score=100.0,
                passing_grade=50.0,
            )
            test_db.add(asmt)
            test_db.commit()
            test_db.refresh(asmt)

            test_db.add(Grade(assessment_id=asmt.id, score=75.0))
            test_db.commit()

        # credit passing percentage: Set Year 3 requirement as cumulative with 70% threshold
        ProgressionService.update_progression_requirement(
            test_db, user.id, target_year=3, credit_percentage=70.0, cumulative=True
        )

        eligibility = ProgressionService.check_year_eligibility(test_db, user.id, target_year=3)

        # credit passing percentage: Both years pass — cumulative earned should be 20/20 = 100%
        assert eligibility["cumulative"] is True
        assert eligibility["credits_earned"] == 20
        assert eligibility["credits_required"] == 20
        assert eligibility["is_eligible"] is True


# ---------------------------------------------------------------------------
# ProgressionSettingsScreen tests
# ---------------------------------------------------------------------------

class TestProgressionSettingsScreen:
    # credit passing percentage: Suppress all QMessageBox dialogs so tests don't block waiting for user input
    @pytest.fixture(autouse=True)
    def disable_message_boxes(self, monkeypatch):
        _, QMessageBox = _load_qt_widgets()
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
        monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)
        monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)

    def test_load_eligibility_data_creates_requirement_cards(self, qapp):
        router = DummyRouter()
        ProgressionSettingsScreen = _load_progression_settings_screen()
        screen = ProgressionSettingsScreen(router)
        mock_client = MagicMock()
        mock_client.get_all_year_eligibility.return_value = [
            {
                "target_year": 2,
                "credits_earned": 15,
                "credits_required": 20,
                "current_percentage": 75.0,
                "required_percentage": 70.0,
                "cumulative": False,
                "is_eligible": True,
            }
        ]
        screen.api_client = mock_client

        screen.load_eligibility_data()

        assert len(screen.requirement_widgets) == 1
        widget_data = screen.requirement_widgets[0]
        assert widget_data["target_year"] == 2
        assert widget_data["percentage_spinner"].value() == 70.0
        assert widget_data["cumulative_check"].isChecked() is False

    def test_save_all_requirements_calls_api_and_refreshes(self, qapp):
        router = DummyRouter()
        ProgressionSettingsScreen = _load_progression_settings_screen()
        screen = ProgressionSettingsScreen(router)
        mock_client = MagicMock()
        mock_client.get_all_year_eligibility.return_value = [
            {
                "target_year": 2,
                "credits_earned": 15,
                "credits_required": 20,
                "current_percentage": 75.0,
                "required_percentage": 70.0,
                "cumulative": False,
                "is_eligible": True,
            }
        ]
        screen.api_client = mock_client
        screen.load_eligibility_data()
        assert len(screen.requirement_widgets) == 1

        widget_data = screen.requirement_widgets[0]
        widget_data["percentage_spinner"].setValue(85.0)
        widget_data["cumulative_check"].setChecked(True)

        screen.load_eligibility_data = MagicMock()
        screen.save_all_requirements()

        mock_client.update_progression_requirement.assert_called_once_with(
            target_year=2,
            credit_percentage=85.0,
            cumulative=True,
        )
        screen.load_eligibility_data.assert_called_once()

    def test_exit_to_dashboard_uses_router(self, qapp):
        router = DummyRouter()
        ProgressionSettingsScreen = _load_progression_settings_screen()
        screen = ProgressionSettingsScreen(router)

        screen.exit_to_dashboard()

        assert router.navigated_to == "dashboard"

    # credit passing percentage: Extra test: partial API failure should still call load_eligibility_data
    def test_save_partial_failure_still_refreshes(self, qapp):
        router = DummyRouter()
        ProgressionSettingsScreen = _load_progression_settings_screen()
        screen = ProgressionSettingsScreen(router)
        mock_client = MagicMock()
        mock_client.get_all_year_eligibility.return_value = [
            {
                "target_year": 2,
                "credits_earned": 10,
                "credits_required": 20,
                "current_percentage": 50.0,
                "required_percentage": 70.0,
                "cumulative": False,
                "is_eligible": False,
            },
            {
                "target_year": 3,
                "credits_earned": 5,
                "credits_required": 20,
                "current_percentage": 25.0,
                "required_percentage": 70.0,
                "cumulative": True,
                "is_eligible": False,
            },
        ]
        screen.api_client = mock_client
        screen.load_eligibility_data()

        # credit passing percentage: Make the second call (Year 3) raise an exception
        call_count = {"n": 0}

        def side_effect(**kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("Server error")

        mock_client.update_progression_requirement.side_effect = side_effect
        screen.load_eligibility_data = MagicMock()

        screen.save_all_requirements()

        # credit passing percentage: Both years were attempted despite Year 3 failing
        assert mock_client.update_progression_requirement.call_count == 2
        # credit passing percentage: Refresh must still happen even after a partial failure
        screen.load_eligibility_data.assert_called_once()