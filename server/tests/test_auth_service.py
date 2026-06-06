"""
Tests for the authentication service.
"""

import pytest

from models import User
from services.auth_service import AuthService


class TestAuthServicePasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test that password hashing produces a hash."""
        password = "test_password"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test verifying a correct password."""
        password = "test_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying an incorrect password."""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False


class TestAuthServiceTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test token creation."""
        user_id = 1
        token = AuthService.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = 123
        token = AuthService.create_access_token(user_id)
        verified_id = AuthService.verify_token(token)

        assert verified_id == user_id

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        verified_id = AuthService.verify_token(invalid_token)

        assert verified_id is None

    def test_verify_malformed_token(self):
        """Test verifying a malformed token."""
        malformed_token = "not.a.valid.jwt.token"
        verified_id = AuthService.verify_token(malformed_token)

        assert verified_id is None


class TestAuthServiceSignUp:
    """Test user registration."""

    def test_sign_up_success(self, test_db, test_user_data):
        """Test successful user registration."""
        user = AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )

        assert user.username == test_user_data["username"]
        assert user.id is not None

        # Verify user was actually saved to database
        db_user = (
            test_db.query(User)
            .filter(User.username == test_user_data["username"])
            .first()
        )
        assert db_user is not None

    def test_sign_up_creates_academic_years(self, test_db, test_user_data):
        """Test that signup creates academic years and semesters."""
        user = AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )

        # Reload user from database to access relationships
        db_user = test_db.query(User).filter(User.id == user.id).first()
        assert len(db_user.academic_years) == 3

        # Check that semesters were created
        for year in db_user.academic_years:
            assert len(year.semesters) == 2

    def test_sign_up_duplicate_username(self, test_db, test_user_data):
        """Test that duplicate username raises error."""
        AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
        )

        with pytest.raises(ValueError, match="Username already exists"):
            AuthService.sign_up(
                test_db,
                test_user_data["username"],
                "different_password",
                test_user_data["num_years"],
            )

    def test_sign_up_default_credit_requirements(self, test_db):
        """Test signup with default credit requirements."""
        user = AuthService.sign_up(
            test_db, "newuser", "password123", num_years=2
        )

        db_user = test_db.query(User).filter(User.id == user.id).first()
        years = db_user.academic_years

        assert len(years) == 2
        for year in years:
            assert year.credit_requirement == 60


class TestAuthServiceLogin:
    """Test user login."""

    def test_login_success(self, test_db, test_user_data):
        """Test successful login."""
        # First register a user
        AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
        )

        # Then try to login
        user = AuthService.login(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
        )

        assert user.username == test_user_data["username"]

    def test_login_wrong_password(self, test_db, test_user_data):
        """Test login with wrong password."""
        AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
        )

        with pytest.raises(ValueError, match="Invalid username or password"):
            AuthService.login(
                test_db, test_user_data["username"], "wrong_password"
            )

    def test_login_nonexistent_user(self, test_db):
        """Test login with nonexistent user."""
        with pytest.raises(ValueError, match="Invalid username or password"):
            AuthService.login(test_db, "nonexistent", "password")
