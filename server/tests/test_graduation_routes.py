"""Tests for graduation API routes."""

import pytest
from fastapi import status


class TestGraduationSettings:

    def test_get_settings_returns_defaults(self, client, authenticated_headers):
        response = client.get("/graduation/settings", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["subject_average_weight"] == 100.0
        assert data["max_grade"] == 10.0

    def test_get_settings_missing_auth(self, client):
        response = client.get("/graduation/settings")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_settings_idempotent(self, client, authenticated_headers):
        first = client.get("/graduation/settings", headers=authenticated_headers).json()
        second = client.get("/graduation/settings", headers=authenticated_headers).json()

        assert first["id"] == second["id"]

    def test_update_settings(self, client, authenticated_headers):
        response = client.put(
            "/graduation/settings",
            json={"subject_average_weight": 70.0, "max_grade": 10.0},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["subject_average_weight"] == 70.0

    def test_update_settings_max_grade(self, client, authenticated_headers):
        response = client.put(
            "/graduation/settings",
            json={"subject_average_weight": 50.0, "max_grade": 20.0},
            headers=authenticated_headers,
        )

        assert response.json()["max_grade"] == 20.0

    def test_update_settings_missing_auth(self, client):
        response = client.put(
            "/graduation/settings",
            json={"subject_average_weight": 50.0, "max_grade": 10.0},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGraduationAssessments:

    @pytest.fixture
    def assessment(self, client, authenticated_headers):
        response = client.post(
            "/graduation/assessments",
            json={"name": "Thesis", "weight": 0.5},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        return response.json()

    def test_get_assessments_empty(self, client, authenticated_headers):
        response = client.get("/graduation/assessments", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_assessments_missing_auth(self, client):
        response = client.get("/graduation/assessments")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_assessment_stores_fields(self, client, authenticated_headers):
        response = client.post(
            "/graduation/assessments",
            json={"name": "Oral Exam", "weight": 0.3, "max_score": 20.0, "passing_grade": 10.0},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Oral Exam"
        assert data["weight"] == 0.3
        assert data["max_score"] == 20.0
        assert data["passing_grade"] == 10.0
        assert isinstance(data["id"], int)

    def test_add_assessment_default_values(self, client, authenticated_headers):
        response = client.post(
            "/graduation/assessments",
            json={"name": "Thesis", "weight": 0.5},
            headers=authenticated_headers,
        )

        data = response.json()
        assert data["max_score"] == 10.0
        assert data["passing_grade"] == 5.0

    def test_add_assessment_missing_auth(self, client):
        response = client.post(
            "/graduation/assessments",
            json={"name": "Thesis", "weight": 0.5},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_assessment_appears_in_list(self, client, authenticated_headers, assessment):
        response = client.get("/graduation/assessments", headers=authenticated_headers)

        ids = [a["id"] for a in response.json()]
        assert assessment["id"] in ids

    def test_update_assessment(self, client, authenticated_headers, assessment):
        response = client.put(
            f"/graduation/assessments/{assessment['id']}",
            json={"name": "Dissertation"},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Dissertation"

    def test_update_assessment_not_found(self, client, authenticated_headers):
        response = client.put(
            "/graduation/assessments/9999",
            json={"name": "X"},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_assessment_missing_auth(self, client, assessment):
        response = client.put(
            f"/graduation/assessments/{assessment['id']}",
            json={"name": "X"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_assessment(self, client, authenticated_headers, assessment):
        response = client.delete(
            f"/graduation/assessments/{assessment['id']}",
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        remaining = client.get("/graduation/assessments", headers=authenticated_headers).json()
        assert not any(a["id"] == assessment["id"] for a in remaining)

    def test_delete_assessment_not_found(self, client, authenticated_headers):
        response = client.delete(
            "/graduation/assessments/9999",
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assessment_missing_auth(self, client, assessment):
        response = client.delete(f"/graduation/assessments/{assessment['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_set_grade(self, client, authenticated_headers, assessment):
        response = client.put(
            f"/graduation/assessments/{assessment['id']}/grade",
            json={"score": 8.5},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["grade"]["score"] == 8.5

    def test_set_grade_updates_existing(self, client, authenticated_headers, assessment):
        client.put(
            f"/graduation/assessments/{assessment['id']}/grade",
            json={"score": 7.0},
            headers=authenticated_headers,
        )
        response = client.put(
            f"/graduation/assessments/{assessment['id']}/grade",
            json={"score": 9.0},
            headers=authenticated_headers,
        )

        assert response.json()["grade"]["score"] == 9.0

    def test_set_grade_not_found(self, client, authenticated_headers):
        response = client.put(
            "/graduation/assessments/9999/grade",
            json={"score": 5.0},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_set_grade_missing_auth(self, client, assessment):
        response = client.put(
            f"/graduation/assessments/{assessment['id']}/grade",
            json={"score": 5.0},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
