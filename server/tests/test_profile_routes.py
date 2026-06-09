"""
Tests for profile API endpoints.
"""

from fastapi import status


class TestProfileRoutes:
    """Test profile API endpoints."""

    def test_get_profile_success(self, client, authenticated_headers, registered_user):
        """Test getting user profile."""
        response = client.get("/profile", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == registered_user["username"]
        assert data["id"] is not None

    def test_get_profile_missing_auth(self, client):
        """Test getting profile without authentication."""
        response = client.get("/profile")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token."""
        response = client.get(
            "/profile",
            headers={"Authorization": "Bearer invalid.token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_no_university(self, client, authenticated_headers):
        """Test profile with no university set."""
        response = client.get("/profile", headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["university_name"] is None
        assert data["major_name"] is None

    def test_update_profile_university(self, client, authenticated_headers, test_university):
        """Test updating user profile with university."""
        response = client.put(
            "/profile",
            json={
                "university_id": test_university.id,
                "major_id": None,
            },
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify update
        get_response = client.get("/profile", headers=authenticated_headers)
        profile = get_response.json()
        assert profile["university_name"] == test_university.name

    def test_update_profile_major(self, client, authenticated_headers, test_major):
        """Test updating user profile with major."""
        response = client.put(
            "/profile",
            json={"university_id": None, "major_id": test_major.id},
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify update
        get_response = client.get("/profile", headers=authenticated_headers)
        profile = get_response.json()
        assert profile["major_name"] == test_major.name

    def test_update_profile_both(
        self,
        client,
        authenticated_headers,
        test_university,
        test_major,
    ):
        """Test updating profile with both university and major."""
        response = client.put(
            "/profile",
            json={
                "university_id": test_university.id,
                "major_id": test_major.id,
            },
            headers=authenticated_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify update
        get_response = client.get("/profile", headers=authenticated_headers)
        profile = get_response.json()
        assert profile["university_name"] == test_university.name
        assert profile["major_name"] == test_major.name

    def test_update_profile_partial(self, client, authenticated_headers, test_university):
        """Test partial profile update (only university)."""
        # First set both
        client.put(
            "/profile",
            json={
                "university_id": test_university.id,
                "major_id": 999,
            },  # Non-existent
            headers=authenticated_headers,
        )

        # Get profile and check university is set
        get_response = client.get("/profile", headers=authenticated_headers)
        profile = get_response.json()
        assert profile["university_name"] is not None

    def test_update_profile_missing_auth(self, client, test_university):
        """Test updating profile without authentication."""
        response = client.put("/profile", json={"university_id": test_university.id})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_empty(self, client, authenticated_headers):
        """Test updating profile with empty data."""
        response = client.put("/profile", json={}, headers=authenticated_headers)

        assert response.status_code == status.HTTP_200_OK

    def test_update_profile_invalid_university(self, client, authenticated_headers):
        """Test updating profile with non-existent university."""
        # This might succeed but the university won't exist
        response = client.put(
            "/profile",
            json={"university_id": 9999},
            headers=authenticated_headers,
        )

        # Depends on implementation - may succeed but query returns None
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]
        
    def test_delete_profile(self, client, authenticated_headers):
        response = client.delete("/profile", headers=authenticated_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Once deleted, the token should no longer resolve to a user
        follow_response = client.get("/profile", headers=authenticated_headers)
        assert follow_response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUniversity:

    def test_creates_new_university(self, client):
        response = client.post("/profile/universities", json={"name": "MIT"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "MIT"
        assert isinstance(data["id"], int)

    def test_returns_existing_on_duplicate_name(self, client):
        client.post("/profile/universities", json={"name": "Oxford"})
        response = client.post("/profile/universities", json={"name": "Oxford"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Oxford"

    def test_duplicate_check_is_case_insensitive(self, client):
        first = client.post("/profile/universities", json={"name": "Cambridge"})
        second = client.post("/profile/universities", json={"name": "cambridge"})

        assert second.status_code == status.HTTP_200_OK
        assert second.json()["id"] == first.json()["id"]

    def test_new_university_appears_in_list(self, client):
        client.post("/profile/universities", json={"name": "Sorbonne"})
        response = client.get("/profile/universities")

        names = [u["name"] for u in response.json()]
        assert "Sorbonne" in names


class TestCreateMajor:

    def test_creates_new_major(self, client):
        response = client.post("/profile/majors", json={"name": "Philosophy"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Philosophy"
        assert isinstance(data["id"], int)

    def test_returns_existing_on_duplicate_name(self, client):
        client.post("/profile/majors", json={"name": "History"})
        response = client.post("/profile/majors", json={"name": "History"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "History"

    def test_duplicate_check_is_case_insensitive(self, client):
        first = client.post("/profile/majors", json={"name": "Biology"})
        second = client.post("/profile/majors", json={"name": "BIOLOGY"})

        assert second.status_code == status.HTTP_200_OK
        assert second.json()["id"] == first.json()["id"]

    def test_new_major_appears_in_list(self, client):
        client.post("/profile/majors", json={"name": "Sociology"})
        response = client.get("/profile/majors")

        names = [m["name"] for m in response.json()]
        assert "Sociology" in names
        
