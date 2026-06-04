"""
Tests for authentication API endpoints.
"""

from fastapi import status


class TestAuthRoutes:
    """Test authentication endpoints."""

    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_username(self, client, test_user_data):
        """Test registration with duplicate username."""
        # Register first user
        client.post("/auth/register", json=test_user_data)

        # Try to register with same username
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already exists" in response.json()["detail"]

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post("/auth/register", json={"username": "test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Register user first
        client.post("/auth/register", json=test_user_data)

        # Login
        response = client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user_data):
        """Test login with wrong password."""
        client.post("/auth/register", json=test_user_data)

        response = client.post(
            "/auth/login",
            json={
                "username": test_user_data["username"],
                "password": "wrong_password",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post("/auth/login", json={"username": "test"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_verify_token_success(self, client, registered_user):
        """Test token verification with valid token."""
        response = client.post(
            "/auth/verify-token",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )

        assert response.status_code == status.HTTP_200_OK

    def test_verify_token_invalid(self, client):
        """Test token verification with invalid token."""
        response = client.post(
            "/auth/verify-token",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_missing(self, client):
        """Test token verification without token."""
        response = client.post("/auth/verify-token")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "No token provided" in response.json()["detail"]

    def test_verify_token_via_query_param(self, client, registered_user):
        """Test token verification via query parameter."""
        response = client.post(
            f"/auth/verify-token?token={registered_user['token']}"
        )

        assert response.status_code == status.HTTP_200_OK


class TestTokenExpiration:
    """Test token expiration behavior."""

    def test_token_has_expiration(self, registered_user):
        """Test that issued tokens have expiration."""
        import jwt
        from config import ALGORITHM, SECRET_KEY

        token = registered_user["token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "exp" in payload
        assert payload["exp"] > 0

    def test_token_contains_user_id(self, registered_user):
        """Test that token contains user ID."""
        import jwt
        from config import ALGORITHM, SECRET_KEY

        token = registered_user["token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "sub" in payload
        assert payload["sub"].isdigit()
