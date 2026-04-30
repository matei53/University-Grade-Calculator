import bcrypt
from repositories.user_repo import UserRepo

class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()

    def sign_up(self, username: str, password: str) -> dict:
        if not username or not password:
            raise ValueError("Username and password are required.")
        if self.user_repo.find_by_username(username):
            raise ValueError("Username already exists.")
        password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()
        return self.user_repo.create(username, password_hash)

    def login(self, username: str, password: str) -> dict:
        user = self.user_repo.find_by_username(username)
        if not user or not bcrypt.checkpw(
            password.encode(), user["password_hash"].encode()):
            raise ValueError("Invalid username or password.")
        return dict(user)