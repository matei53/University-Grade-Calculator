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

    def test_update_subject(self, client, authenticated_headers):
        response = client.post(
            "/subjects",
            json={
                "name": "History",
                "credits": 4,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = response.json()["id"]

        update_response = client.put(
            f"/subjects/{subject_id}",
            json={"name": "Modern History", "credits": 5, "passing_grade": 6.0},
            headers=authenticated_headers,
        )

        assert update_response.status_code == status.HTTP_200_OK
        data = update_response.json()
        assert data["name"] == "Modern History"
        assert data["credit_value"] == 5
        assert data["passing_grade"] == 6.0

    def test_delete_subject(self, client, authenticated_headers):
        response = client.post(
            "/subjects",
            json={
                "name": "Art",
                "credits": 3,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = response.json()["id"]

        delete_response = client.delete(f"/subjects/{subject_id}", headers=authenticated_headers)

        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        response = client.get("/subjects/years", headers=authenticated_headers)
        assert all(
            subject["id"] != subject_id for year in response.json() for subject in year["subjects"]
        )


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

    def test_add_assessment_to_other_users_subject_returns_403(self, client, authenticated_headers):
        """POST /assessments/{subject_id} must be 403 when the subject belongs to another user."""
        second_resp = client.post(
            "/auth/register",
            json={"username": "other_subj_user", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
        )
        other_headers = {"Authorization": f"Bearer {second_resp.json()['access_token']}"}
        subject_resp = client.post(
            "/subjects",
            json={"name": "Private Subject", "credits": 4, "semester_index": 1, "year_level": 1},
            headers=other_headers,
        )
        other_subject_id = subject_resp.json()["id"]

        response = client.post(
            f"/assessments/{other_subject_id}",
            json={"name": "Intruder Exam", "weight": 1.0, "score": 9.0},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

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

    def test_update_grade(self, client, authenticated_headers):
        subject_response = client.post(
            "/subjects",
            json={
                "name": "Biology",
                "credits": 5,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        assessment_response = client.post(
            f"/assessments/{subject_id}",
            json={
                "name": "Lab",
                "weight": 0.5,
                "score": 7.0,
                "max_score": 10.0,
                "passing_grade": 5.0,
            },
            headers=authenticated_headers,
        )
        grade_id = assessment_response.json()["grade"]["id"]

        update_response = client.put(
            f"/grades/{grade_id}",
            json={"score": 9.0},
            headers=authenticated_headers,
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["score"] == 9.0

    def test_delete_grade(self, client, authenticated_headers):
        subject_response = client.post(
            "/subjects",
            json={
                "name": "Geography",
                "credits": 4,
                "semester_index": 1,
                "year_level": 1,
            },
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        assessment_response = client.post(
            f"/assessments/{subject_id}",
            json={
                "name": "Map Quiz",
                "weight": 1.0,
                "score": 8.0,
                "max_score": 10.0,
                "passing_grade": 5.0,
            },
            headers=authenticated_headers,
        )
        grade_id = assessment_response.json()["grade"]["id"]

        delete_response = client.delete(f"/grades/{grade_id}", headers=authenticated_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify the grade is no longer present in the subject payload
        years_response = client.get("/subjects/years", headers=authenticated_headers)
        grade_values = [
            assessment.get("grade")
            for year in years_response.json()
            for subject in year["subjects"]
            for assessment in subject.get("assessments", [])
        ]
        assert all(g is None for g in grade_values)

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

    def test_add_assessment_without_score_creates_ungraded(self, client, authenticated_headers):
        """Omitting score should create an assessment whose grade.score is null."""
        subject_response = client.post(
            "/subjects",
            json={"name": "Statistics", "credits": 4, "semester_index": 1, "year_level": 1},
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        response = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Final Exam", "weight": 1.0},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["grade"]["score"] is None

    def test_add_assessment_explicit_null_score_creates_ungraded(
        self, client, authenticated_headers
    ):
        """Explicitly passing score=null should also create an ungraded assessment."""
        subject_response = client.post(
            "/subjects",
            json={"name": "Philosophy", "credits": 3, "semester_index": 1, "year_level": 1},
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        response = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Essay", "weight": 1.0, "score": None},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["grade"]["score"] is None

    def test_update_grade_to_null_clears_score(self, client, authenticated_headers):
        """Updating a grade with score=null should mark it ungraded."""
        subject_response = client.post(
            "/subjects",
            json={"name": "Chemistry", "credits": 5, "semester_index": 1, "year_level": 1},
            headers=authenticated_headers,
        )
        subject_id = subject_response.json()["id"]

        assessment_response = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Lab", "weight": 1.0, "score": 8.0},
            headers=authenticated_headers,
        )
        grade_id = assessment_response.json()["grade"]["id"]

        update_response = client.put(
            f"/grades/{grade_id}",
            json={"score": None},
            headers=authenticated_headers,
        )

        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["score"] is None


class TestAssessmentUpdateDeleteRoutes:
    """Test PUT and DELETE endpoints for assessments."""

    @staticmethod
    def _make_subject_and_assessment(client, headers, subject_name="TestSubject"):
        subject_resp = client.post(
            "/subjects",
            json={"name": subject_name, "credits": 4, "semester_index": 1, "year_level": 1},
            headers=headers,
        )
        subject_id = subject_resp.json()["id"]
        assessment_resp = client.post(
            f"/assessments/{subject_id}",
            json={"name": "Midterm", "weight": 50.0, "score": 7.0, "max_score": 10.0, "passing_grade": 5.0},
            headers=headers,
        )
        return assessment_resp.json()["id"]

    def test_update_assessment_name(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers)
        response = client.put(
            f"/assessments/{assessment_id}",
            json={"name": "Final Exam"},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Final Exam"

    def test_update_assessment_weight(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers)
        response = client.put(
            f"/assessments/{assessment_id}",
            json={"weight": 75.0},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["weight"] == 75.0

    def test_update_assessment_max_score_and_passing_grade(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers)
        response = client.put(
            f"/assessments/{assessment_id}",
            json={"max_score": 20.0, "passing_grade": 10.0},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["max_score"] == 20.0
        assert data["passing_grade"] == 10.0

    def test_update_assessment_not_found_returns_404(self, client, authenticated_headers):
        response = client.put(
            "/assessments/99999",
            json={"name": "Ghost"},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_assessment_wrong_user_returns_404(self, client, authenticated_headers):
        second_resp = client.post(
            "/auth/register",
            json={"username": "other2", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
        )
        other_headers = {"Authorization": f"Bearer {second_resp.json()['access_token']}"}
        other_assessment_id = self._make_subject_and_assessment(client, other_headers, "OtherSubject")

        response = client.put(
            f"/assessments/{other_assessment_id}",
            json={"name": "Stolen"},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_assessment_requires_auth(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers)
        response = client.put(f"/assessments/{assessment_id}", json={"name": "No Auth"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_assessment_success(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers, "DeleteMe")
        response = client.delete(f"/assessments/{assessment_id}", headers=authenticated_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_assessment_not_found_returns_404(self, client, authenticated_headers):
        response = client.delete("/assessments/99999", headers=authenticated_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assessment_wrong_user_returns_404(self, client, authenticated_headers):
        second_resp = client.post(
            "/auth/register",
            json={"username": "other3", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
        )
        other_headers = {"Authorization": f"Bearer {second_resp.json()['access_token']}"}
        other_assessment_id = self._make_subject_and_assessment(client, other_headers, "OtherSubject2")

        response = client.delete(f"/assessments/{other_assessment_id}", headers=authenticated_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_assessment_requires_auth(self, client, authenticated_headers):
        assessment_id = self._make_subject_and_assessment(client, authenticated_headers, "NoAuthDel")
        response = client.delete(f"/assessments/{assessment_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSubjectUpdateDeleteErrorPaths:
    """Error-path tests for PUT/DELETE /subjects/{id} not covered by TestSubjectRoutes."""

    def test_update_subject_not_found_returns_404(self, client, authenticated_headers):
        response = client.put(
            "/subjects/99999",
            json={"name": "Ghost Subject"},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_subject_not_found_returns_404(self, client, authenticated_headers):
        response = client.delete("/subjects/99999", headers=authenticated_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_subject_wrong_user_returns_404(self, client, authenticated_headers):
        second_resp = client.post(
            "/auth/register",
            json={"username": "other4", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
        )
        other_headers = {"Authorization": f"Bearer {second_resp.json()['access_token']}"}
        subject_resp = client.post(
            "/subjects",
            json={"name": "OtherSubject3", "credits": 4, "semester_index": 1, "year_level": 1},
            headers=other_headers,
        )
        subject_id = subject_resp.json()["id"]

        response = client.put(
            f"/subjects/{subject_id}",
            json={"name": "Stolen"},
            headers=authenticated_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_subject_wrong_user_returns_404(self, client, authenticated_headers):
        second_resp = client.post(
            "/auth/register",
            json={"username": "other5", "password": "pass123", "num_years": 1, "credit_requirements": [60]},
        )
        other_headers = {"Authorization": f"Bearer {second_resp.json()['access_token']}"}
        subject_resp = client.post(
            "/subjects",
            json={"name": "OtherSubject4", "credits": 4, "semester_index": 1, "year_level": 1},
            headers=other_headers,
        )
        subject_id = subject_resp.json()["id"]

        response = client.delete(f"/subjects/{subject_id}", headers=authenticated_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
