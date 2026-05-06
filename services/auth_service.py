import bcrypt
from repositories.user_repo import UserRepo
from repositories.subject_repo import SubjectRepo

class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()

    def sign_up(self, username: str, password: str, num_years: int = 3, credit_requirements: list = None) -> dict:
        if not username or not password:
            raise ValueError("Username and password are required.")
        if self.user_repo.find_by_username(username):
            raise ValueError("Username already exists.")
        password_hash = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()
        user = self.user_repo.create(username, password_hash)
        
        # Use provided credit requirements or default to 60 for each year
        if credit_requirements is None:
            credit_requirements = [60] * num_years
        
        # Create years and semesters for the user
        try:
            print(f"Creating {num_years} years with credit requirements: {credit_requirements}")
            SubjectRepo.create_years_for_user(user["id"], num_years, credit_requirements)
            print(f"Successfully created years for user {user['id']}")
        except Exception as e:
            print(f"Error creating years: {e}")
            raise ValueError(f"Failed to create academic years: {str(e)}")
        
        return user

    def login(self, username: str, password: str) -> dict:
        user = self.user_repo.find_by_username(username)
        if not user or not bcrypt.checkpw(
            password.encode(), user["password_hash"].encode()):
            raise ValueError("Invalid username or password.")
        return dict(user)