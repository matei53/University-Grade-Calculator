"""
Tests for leaderboard API and service logic.
"""

import pytest
from fastapi import status

from models import University, User
from services.leaderboard_service import build_leaderboard, university_short
from services.subject_service import AssessmentService, SubjectService


def _all_names(data: dict) -> set[str]:
    return {e["display_name"] for e in data["podium"] + data["entries"]}


@pytest.fixture
def profiled_user(client, test_university, test_major):
    """Register a user with university and major set."""

    def _register(username: str, password: str = "password123"):
        response = client.post(
            "/auth/register",
            json={
                "username": username,
                "password": password,
                "num_years": 3,
                "credit_requirements": [60, 60, 60],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.put(
            "/profile",
            json={
                "university_id": test_university.id,
                "major_id": test_major.id,
            },
            headers=headers,
        )
        return {"username": username, "token": token, "headers": headers}

    return _register

def _add_subject_grade(test_db, username: str, score: float, year_level: int = 1):
    # 1. Find the user and fetch their assigned test university record
    user = test_db.query(User).filter(User.username == username).first()
    university = user.university 

    # 2. Extract boundaries if they exist on your model, otherwise fall back to 
    # whatever scale your `test_university` fixture currently inserts into the DB
    passing = getattr(university, "passing_grade", 5.0)
    max_g = getattr(university, "max_grade", 10.0)

    # 3. Call your approved services using explicit keyword arguments
    subject = SubjectService.add_subject(
        db=test_db,
        user_id=user.id,
        name="Math",
        credits=6,
        semester_index=1,
        year_level=year_level,
        passing_grade=passing,
        max_grade=max_g
    )
    
    AssessmentService.add_assessment(
        db=test_db,
        subject_id=subject.id,
        name="Exam",
        weight=100.0,
        score=score,
        max_score=max_g,
        passing_grade=passing
    )
    
def _add_subject_grade(test_db, username: str, score: float, year_level: int = 1):
    user = test_db.query(User).filter(User.username == username).first()
    subject = SubjectService.add_subject(
        test_db, user.id, "Math", 6, 1, year_level
    )
    AssessmentService.add_assessment(
        test_db, subject.id, "Exam", 100.0, score
    )

class TestUniversityAbbreviation:
    """University short-name helper."""

    def test_known_ubb(self):
        assert university_short("UBB") == "UBB"

    def test_known_politehnica(self):
        assert university_short("Universitatea Politehnica") == "UPB"

    def test_known_bucuresti(self):
        assert university_short("Universitatea din Bucuresti") == "UB"

    def test_empty_name(self):
        assert university_short(None) == "—"
        assert university_short("") == "—"

    def test_multi_word_initials(self):
        assert university_short("Alexandru Ioan Cuza") == "AIC"


class TestLeaderboardRoutes:
    """Leaderboard HTTP endpoints."""

    def test_leaderboard_requires_auth(self, client):
        response = client.get("/leaderboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_leaderboard_empty_without_profile(self, client, authenticated_headers):
        response = client.get("/leaderboard", headers=authenticated_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["podium"] == []
        assert data["entries"] == []
        assert data["total"] == 0
        assert data["filter_university"] is None

    def test_leaderboard_shows_two_peers_same_course(
        self, client, profiled_user, test_university, test_major
    ):
        user_a = profiled_user("alice_leader")
        profiled_user("bob_leader")

        data = client.get("/leaderboard", headers=user_a["headers"]).json()
        assert data["total"] == 2
        assert len(data["podium"]) == 2
        assert data["entries"] == []
        assert "Alice Leader" in _all_names(data)
        assert "Bob Leader" in _all_names(data)
        for entry in data["podium"]:
            assert entry["university_short"] == university_short(test_university.name)

    def test_leaderboard_excludes_different_major(
        self, client, profiled_user, test_db, test_university
    ):
        from models import Major

        other_major = Major(name="Law")
        test_db.add(other_major)
        test_db.commit()
        test_db.refresh(other_major)

        user_a = profiled_user("carol_cs")
        response = client.post(
            "/auth/register",
            json={
                "username": "dave_law",
                "password": "password123",
                "num_years": 3,
            },
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.put(
            "/profile",
            json={
                "university_id": test_university.id,
                "major_id": other_major.id,
            },
            headers=headers,
        )

        data = client.get("/leaderboard", headers=user_a["headers"]).json()
        assert data["total"] == 1
        assert data["podium"][0]["display_name"] == "Carol Cs"

    def test_university_abbreviation_in_response(self, client, profiled_user, test_db):
        upb = University(name="Universitatea Politehnica")
        test_db.add(upb)
        test_db.commit()
        test_db.refresh(upb)

        from models import Major

        major = Major(name="Engineering")
        test_db.add(major)
        test_db.commit()
        test_db.refresh(major)

        response = client.post(
            "/auth/register",
            json={
                "username": "upb_student",
                "password": "password123",
                "num_years": 3,
            },
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.put(
            "/profile",
            json={"university_id": upb.id, "major_id": major.id},
            headers=headers,
        )

        data = client.get("/leaderboard", headers=headers).json()
        assert data["podium"][0]["university_short"] == "UPB"
        assert data["filter_university"] == "Universitatea Politehnica"


class TestLeaderboardVisibility:
    """Visibility toggle behaviour."""

    def test_get_visibility_default_true(self, client, profiled_user):
        user = profiled_user("visible_user")
        response = client.get("/leaderboard/visibility", headers=user["headers"])
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["visible"] is True

    def test_set_visibility_false(self, client, profiled_user):
        user = profiled_user("hidden_user")
        response = client.patch(
            "/leaderboard/visibility",
            json={"visible": False},
            headers=user["headers"],
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["visible"] is False

    def test_hidden_user_not_visible_to_peers(self, client, profiled_user):
        user_a = profiled_user("peer_a")
        user_b = profiled_user("peer_b")

        assert client.get("/leaderboard", headers=user_a["headers"]).json()["total"] == 2

        client.patch(
            "/leaderboard/visibility",
            json={"visible": False},
            headers=user_b["headers"],
        )

        data = client.get("/leaderboard", headers=user_a["headers"]).json()
        assert data["total"] == 1
        assert data["podium"][0]["display_name"] == "Peer A"

    def test_hidden_user_still_sees_self(self, client, profiled_user):
        user = profiled_user("self_hidden")
        client.patch(
            "/leaderboard/visibility",
            json={"visible": False},
            headers=user["headers"],
        )

        data = client.get("/leaderboard", headers=user["headers"]).json()
        assert data["total"] == 1
        assert data["podium"][0]["is_current_user"] is True
        assert data["current_user_visible"] is False

    def test_five_users_one_hidden_returns_four(self, client, profiled_user):
        users = [profiled_user(f"student_{i}") for i in range(1, 6)]
        client.patch(
            "/leaderboard/visibility",
            json={"visible": False},
            headers=users[1]["headers"],
        )

        data = client.get("/leaderboard", headers=users[0]["headers"]).json()
        assert data["total"] == 4
        assert len(data["podium"]) == 3
        assert len(data["entries"]) == 1
        assert "Student 2" not in _all_names(data)


class TestLeaderboardSearch:
    """Name search filter."""

    def test_search_by_name(self, client, profiled_user):
        user_a = profiled_user("alpha_one")
        profiled_user("beta_two")

        data = client.get(
            "/leaderboard",
            params={"search": "alpha"},
            headers=user_a["headers"],
        ).json()
        assert data["total"] == 1
        assert data["podium"][0]["display_name"] == "Alpha One"

    def test_search_case_insensitive(self, client, profiled_user):
        user = profiled_user("CamelCase_User")
        profiled_user("other_user")

        data = client.get(
            "/leaderboard",
            params={"search": "camelcase"},
            headers=user["headers"],
        ).json()
        assert data["total"] == 1

    def test_search_exact_name_jumps_to_matching_page(self, client, profiled_user):
        user = profiled_user("alpha")
        profiled_user("beta")
        profiled_user("charlie")
        profiled_user("delta")
        profiled_user("echo")
        profiled_user("t8")

        data = client.get(
            "/leaderboard",
            params={"search": "t8"},
            headers=user["headers"],
        ).json()

        assert data["page"] == 2
        assert any(entry["display_name"] == "T8" for entry in data["entries"])
        assert len(data["podium"]) == 3


class TestLeaderboardPagination:
    """Paginated table rows (20 per page)."""

    def test_pagination_splits_table_rows(self, client, profiled_user):
        user = profiled_user("page_host")
        for i in range(2, 25):
            profiled_user(f"pager_{i}")

        page1 = client.get(
            "/leaderboard",
            params={"page": 1, "page_size": 20},
            headers=user["headers"],
        ).json()
        assert page1["total"] == 24
        assert len(page1["podium"]) == 3
        assert len(page1["entries"]) == 20
        assert page1["entries"][0]["rank"] == 4
        assert page1["total_pages"] == 2

        page2 = client.get(
            "/leaderboard",
            params={"page": 2, "page_size": 20},
            headers=user["headers"],
        ).json()
        assert len(page2["entries"]) == 1
        assert page2["entries"][0]["rank"] == 24


class TestLeaderboardYearLevel:
    """Year-level selector and filtering."""

    def test_defaults_to_current_user_year(self, client, profiled_user, test_db):
        user_a = profiled_user("year_a")
        profiled_user("year_b")
        _add_subject_grade(test_db, "year_a", 8.0, year_level=2)
        _add_subject_grade(test_db, "year_b", 7.0, year_level=1)

        data = client.get("/leaderboard", headers=user_a["headers"]).json()
        assert data["filter_year_level"] == 2
        assert data["total"] == 1
        assert data["podium"][0]["display_name"] == "Year A"

    def test_explore_other_year_level(self, client, profiled_user, test_db):
        user_a = profiled_user("explore_a")
        profiled_user("explore_b")
        _add_subject_grade(test_db, "explore_a", 8.0, year_level=2)
        _add_subject_grade(test_db, "explore_b", 7.0, year_level=1)

        data = client.get(
            "/leaderboard",
            params={"year_level": 1},
            headers=user_a["headers"],
        ).json()
        assert data["filter_year_level"] == 1
        assert data["total"] == 1
        assert data["podium"][0]["display_name"] == "Explore B"
        assert 1 in data["available_year_levels"]
        assert 2 in data["available_year_levels"]


class TestLeaderboardSorting:
    """Ranking: average first, credits second."""

    def test_ranks_by_average(self, test_db, profiled_user, client):
        profiled_user("rank_a")
        profiled_user("rank_b")
        _add_subject_grade(test_db, "rank_a", 7.0)
        _add_subject_grade(test_db, "rank_b", 9.0)

        current = test_db.query(User).filter(User.username == "rank_a").first()
        result = build_leaderboard(test_db, current)
        assert result["podium"][0]["display_name"] == "Rank B"
        assert result["podium"][0]["weighted_avg"] == 9.0

    def test_credits_break_tie_on_average(self, test_db, profiled_user, client):
        profiled_user("tie_low_cr")
        profiled_user("tie_high_cr")
        # Use a real 10/10 score for a full subject average of 10.0
        _add_subject_grade(test_db, "tie_low_cr", 10.0)
        user_high = test_db.query(User).filter(User.username == "tie_high_cr").first()
        s1 = SubjectService.add_subject(test_db, user_high.id, "A", 6, 1, 1)
        AssessmentService.add_assessment(test_db, s1.id, "E1", 100.0, 8.0, 8.0)
        s2 = SubjectService.add_subject(test_db, user_high.id, "B", 6, 2, 1)
        AssessmentService.add_assessment(test_db, s2.id, "E2", 100.0, 8.0, 8.0)

        current = test_db.query(User).filter(User.username == "tie_low_cr").first()
        result = build_leaderboard(test_db, current)
        assert result["podium"][0]["display_name"] == "Tie High Cr"
        assert result["podium"][0]["credits"] > result["podium"][1]["credits"]

    def test_current_user_flag_in_table(self, client, profiled_user):
        users = [profiled_user(f"flag_{i}") for i in range(1, 6)]
        data = client.get("/leaderboard", headers=users[4]["headers"]).json()
        me_rows = [
            e for e in data["podium"] + data["entries"] if e["is_current_user"]
        ]
        assert len(me_rows) == 1
        assert me_rows[0]["display_name"] == "Flag 5"
