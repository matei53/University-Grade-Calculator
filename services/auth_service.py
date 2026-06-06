from client.api_client import APIClient


class AuthService:
    def __init__(self):
        self.client = APIClient()

    def sign_up(
        self,
        username: str,
        password: str,
        num_years: int = 3,
        credit_requirements: list = None,
    ) -> dict:
        try:
            user = self.client.register(
                username, password, num_years, credit_requirements
            )
            return user
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(
                f"Registration failed: {type(e).__name__}: {str(e)}"
            )

    def login(self, username: str, password: str) -> dict:
        try:
            token = self.client.login(username, password)
            # Return user info from the client after login
            profile = self.client.get_profile()
            return {
                "id": self.client.user_id,
                "username": profile.get("username"),
                "token": token,
            }
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Login failed: {str(e)}")
