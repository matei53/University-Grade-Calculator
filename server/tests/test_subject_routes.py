"""
Tests for subject and assessment API endpoints.
"""

from fastapi import status


class TestSubjectRoutes:
    """Test subject API endpoints."""

    def test_add_subject_success(self, client, authenticated_headers, test_db):
        """Test successfully adding a subject."""
        response = client.post(
            "/subjects",
            json={
                "name": "Mathematics",
                "credits": 6,
                "semester_index": 1,
                "year_level": 1,
                "passing_grade": 5.0,
                "max_grade": 10.0,
            },
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Mathematics"
        assert data["credit_value"] == 6

    def test_add_subject_missing_auth(self, client):
        """Test adding subject without authentication."""
        response = client.post(
            "/subjects",
            json={
                "name": "Mathematics",
                "credits": 6,
                "semester_index": 1,
                "year_level": 1,
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_subject_invalid_token(self, client):
        """Test adding subject with invalid token."""
        response = client.post(
            "/subjects",
            json={
                "name": "Mathematics",
                "credits": 6,
                "semester_index": 1,
                "year_level": 1,
            },
            headers={"Authorization": "Bearer invalid.token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_subject_with_custom_grades(self, client, authenticated_headers):
        """Test adding subject with custom grade boundaries."""
        response = client.post(
            "/subjects",
            json={
                "name": "Advanced Physics",
                "credits": 8,
                "semester_index": 2,
                "year_level": 2,
                "passing_grade": 4.0,
                "max_grade": 20.0,
            },
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["passing_grade"] == 4.0
        assert data["max_grade"] == 20.0

    def test_get_academic_years(self, client, authenticated_headers):
        """Test retrieving user's academic years."""
        response = client.get("/subjects/years", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        years = response.json()
        assert isinstance(years, list)
        assert len(years) == 3  # Default 3 years

    def test_get_academic_years_missing_auth(self, client):
        """Test getting years without authentication."""
        response = client.get("/subjects/years")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_subject_with_added_subject(self, client, authenticated_headers):
        """Test that subjects appear in years endpoint."""
        # Add a subject
        client.post(
            "/subjects",
            json={
                "name": "Chemistry",
                "credits": 5,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )

        # Get years
        response = client.get("/subjects/years", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        years = response.json()

        # Check first year has subjects
        assert len(years[0]["subjects"]) > 0
        assert years[0]["subjects"][0]["name"] == "Chemistry"


class TestAssessmentRoutes:
    """Test assessment API endpoints."""

    def test_add_assessment_success(self, client, authenticated_headers):
        """Test adding an assessment to a subject."""
        # First add a subject
        subject_response = client.post(
            "/subjects",
            json={
                "name": "Mathematics",
                "credits": 6,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        # Add assessment
        response = client.post(
            f"/assessments/{subject_id}",
            json={
                "name": "Midterm Exam",
                "weight": 0.4,
                "score": 8.5,
                "max_score": 10.0,
                "passing_grade": 5.0,
            },
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Midterm Exam"
        assert data["weight"] == 0.4

    def test_add_assessment_missing_auth(self, client):
        """Test adding assessment without authentication."""
        response = client.post(
            "/assessments/1",
            json={"name": "Quiz", "weight": 0.2, "score": 7.5},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_assessment_nonexistent_subject(self, client, authenticated_headers):
        """Test adding assessment to nonexistent subject."""
        response = client.post(
            "/assessments/9999",
            json={"name": "Quiz", "weight": 0.2, "score": 7.5},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Subject not found" in response.json()["detail"]

    def test_add_multiple_assessments(self, client, authenticated_headers):
        """Test adding multiple assessments to same subject."""
        # Add subject
        subject_response = client.post(
            "/subjects",
            json={
                "name": "Physics",
                "credits": 6,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        # Add first assessment
        response1 = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Quiz 1", "weight": 0.2, "score": 8.0},
            headers=authenticated_headers,
        )

        # Add second assessment
        response2 = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Quiz 2", "weight": 0.2, "score": 7.5},
            headers=authenticated_headers,
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json()["name"] != response2.json()["name"]

    def test_add_assessment_appears_in_subject(self, client, authenticated_headers):
        """Test that assessment appears when retrieving subject details."""
        # Add subject
        subject_response = client.post(
            "/subjects",
            json={
                "name": "English",
                "credits": 4,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        # Add assessment
        client.post(
            f"/assessments/{subject_id}",
            json={"name": "Essay", "weight": 0.6, "score": 9.0},
            headers=authenticated_headers,
        )

        # Get years and check
        response = client.get("/subjects/years", headers=authenticated_headers)

        years = response.json()
        subject = years[0]["subjects"][0]
        assert len(subject["assessments"]) > 0
        assert subject["assessments"][0]["name"] == "Essay"
