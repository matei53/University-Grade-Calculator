"""
Tests for the /progression API endpoints.

Covers GET requirements, PUT requirements/{target_year},
GET eligibility/{target_year}, and GET eligibility.
"""

from fastapi import status


class TestProgressionRequirementsRoutes:
    def test_get_requirements_empty_for_new_user(self, client, authenticated_headers):
        response = client.get("/progression/requirements", headers=authenticated_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_requirements_returns_created_entries(self, client, authenticated_headers):
        client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 75.0, "cumulative": False},
            headers=authenticated_headers,
        )
        response = client.get("/progression/requirements", headers=authenticated_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["target_year"] == 2
        assert data[0]["credit_percentage"] == 75.0
        assert data[0]["cumulative"] is False

    def test_get_requirements_requires_auth(self, client):
        response = client.get("/progression/requirements")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_requirement_success(self, client, authenticated_headers):
        response = client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 80.0, "cumulative": False},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["target_year"] == 2
        assert data["credit_percentage"] == 80.0
        assert data["message"] == "Progression requirement updated"

    def test_update_requirement_sets_cumulative_true(self, client, authenticated_headers):
        response = client.put(
            "/progression/requirements/3",
            json={"credit_percentage": 60.0, "cumulative": True},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["cumulative"] is True

    def test_update_requirement_overwrites_previous(self, client, authenticated_headers):
        client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 70.0, "cumulative": False},
            headers=authenticated_headers,
        )
        client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 90.0, "cumulative": False},
            headers=authenticated_headers,
        )
        response = client.get("/progression/requirements", headers=authenticated_headers)
        assert response.json()[0]["credit_percentage"] == 90.0

    def test_update_requirement_invalid_percentage_below_zero(self, client, authenticated_headers):
        response = client.put(
            "/progression/requirements/2",
            json={"credit_percentage": -5.0, "cumulative": False},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert "error" in response.json()

    def test_update_requirement_invalid_percentage_above_100(self, client, authenticated_headers):
        response = client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 110.0, "cumulative": False},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert "error" in response.json()

    def test_update_requirement_requires_auth(self, client):
        response = client.put(
            "/progression/requirements/2",
            json={"credit_percentage": 70.0, "cumulative": False},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProgressionEligibilityRoutes:
    def test_get_year_eligibility_returns_expected_shape(self, client, authenticated_headers):
        response = client.get("/progression/eligibility/2", headers=authenticated_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["target_year"] == 2
        assert "is_eligible" in data
        assert "credits_earned" in data
        assert "credits_required" in data
        assert "current_percentage" in data
        assert "required_percentage" in data
        assert "cumulative" in data

    def test_get_year_eligibility_not_eligible_with_no_grades(self, client, authenticated_headers):
        response = client.get("/progression/eligibility/2", headers=authenticated_headers)
        data = response.json()
        assert data["is_eligible"] is False
        assert data["credits_earned"] == 0

    def test_get_year_eligibility_eligible_after_passing_subjects(self, client, authenticated_headers):
        # Add a subject in year 1 and give it a passing grade
        subject_resp = client.post(
            "/subjects",
            json={"name": "Maths", "credits": 6, "semester_index": 1, "year_level": 1},
            headers=authenticated_headers,
        )
        subject_id = subject_resp.json()["id"]
        assessment_resp = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Exam", "weight": 100.0, "score": 8.0, "max_score": 10.0, "passing_grade": 5.0},
            headers=authenticated_headers,
        )
        assert assessment_resp.status_code == status.HTTP_200_OK

        response = client.get("/progression/eligibility/2", headers=authenticated_headers)
        data = response.json()
        assert data["is_eligible"] is True
        assert data["credits_earned"] == 6
        assert data["credits_required"] == 6

    def test_get_year_eligibility_requires_auth(self, client):
        response = client.get("/progression/eligibility/2")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all_eligibility_returns_list(self, client, authenticated_headers):
        # User registered with 3 years → eligibility for years 2 and 3
        response = client.get("/progression/eligibility", headers=authenticated_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        target_years = {item["target_year"] for item in data}
        assert target_years == {2, 3}

    def test_get_all_eligibility_requires_auth(self, client):
        response = client.get("/progression/eligibility")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
