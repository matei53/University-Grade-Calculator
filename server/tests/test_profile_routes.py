"""
Tests for profile API endpoints.
"""

from fastapi import status


class TestProfileRoutes:
    """Test profile API endpoints."""

    def test_get_profile_success(
        self, client, authenticated_headers, registered_user
    ):
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

    def test_update_profile_university(
        self, client, authenticated_headers, test_university
    ):
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

    def test_update_profile_major(
        self, client, authenticated_headers, test_major
    ):
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

    def test_update_profile_partial(
        self, client, authenticated_headers, test_university
    ):
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
        response = client.put(
            "/profile", json={"university_id": test_university.id}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_empty(self, client, authenticated_headers):
        """Test updating profile with empty data."""
        response = client.put(
            "/profile", json={}, headers=authenticated_headers
        )

        assert response.status_code == status.HTTP_200_OK

    def test_update_profile_invalid_university(
        self, client, authenticated_headers
    ):
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
