"""
Tests for the /grades API endpoints covering error paths not exercised by
the happy-path tests in test_subject_routes.py.
"""

import pytest
from fastapi import status


@pytest.fixture
def subject_with_grade(client, authenticated_headers):
    """Create a subject → assessment → grade for the authenticated user."""
    subject_resp = client.post(
        "/subjects",
        json={"name": "Biology", "credits": 5, "semester_index": 1, "year_level": 1},
        headers=authenticated_headers,
    )
    subject_id = subject_resp.json()["id"]

    assessment_resp = client.post(
        f"/assessments/{subject_id}",
        json={"name": "Lab", "weight": 1.0, "score": 7.0, "max_score": 10.0, "passing_grade": 5.0},
        headers=authenticated_headers,
    )
    return assessment_resp.json()["grade"]["id"]


@pytest.fixture
def other_user_grade_id(client):
    """Grade belonging to a second user that the primary user must not access."""
    second_resp = client.post(
        "/auth/register",
        json={"username": "other_user", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
    )
    token = second_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    subject_resp = client.post(
        "/subjects",
        json={"name": "Chem", "credits": 4, "semester_index": 1, "year_level": 1},
        headers=headers,
    )
    assessment_resp = client.post(
        f"/assessments/{subject_resp.json()['id']}",
        json={"name": "Exam", "weight": 1.0, "score": 8.0},
        headers=headers,
    )
    return assessment_resp.json()["grade"]["id"]


class TestUpdateGradeRoute:
    def test_update_grade_not_found_returns_404(self, client, authenticated_headers):
        response = client.put(
            "/grades/99999",
            json={"score": 5.0},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_grade_wrong_user_returns_403(self, client, authenticated_headers, other_user_grade_id):
        response = client.put(
            f"/grades/{other_user_grade_id}",
            json={"score": 5.0},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_grade_requires_auth(self, client, subject_with_grade):
        response = client.put(f"/grades/{subject_with_grade}", json={"score": 5.0})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_grade_to_new_value(self, client, authenticated_headers, subject_with_grade):
        response = client.put(
            f"/grades/{subject_with_grade}",
            json={"score": 9.5},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["score"] == 9.5

    def test_update_grade_to_null_clears_score(self, client, authenticated_headers, subject_with_grade):
        response = client.put(
            f"/grades/{subject_with_grade}",
            json={"score": None},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["score"] is None


class TestDeleteGradeRoute:
    def test_delete_grade_not_found_returns_404(self, client, authenticated_headers):
        response = client.delete("/grades/99999", headers=authenticated_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_grade_wrong_user_returns_403(self, client, authenticated_headers, other_user_grade_id):
        response = client.delete(
            f"/grades/{other_user_grade_id}",
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_grade_requires_auth(self, client, subject_with_grade):
        response = client.delete(f"/grades/{subject_with_grade}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_grade_success(self, client, authenticated_headers, subject_with_grade):
        response = client.delete(
            f"/grades/{subject_with_grade}",
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
