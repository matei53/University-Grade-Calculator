from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from server.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from server.schemas import UserResponse
from sqlalchemy.orm import Session

from server.models import AcademicYear, Semester, User


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    @staticmethod
    def create_access_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> int:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def sign_up(
        db: Session,
        username: str,
        password: str,
        num_years: int = 3,
        credit_requirements: list = None,
    ) -> UserResponse:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("Username already exists")

        # Create user
        password_hash = AuthService.hash_password(password)
        user = User(username=username, password_hash=password_hash)
        db.add(user)
        db.flush()  # Get the user ID

        # Set up credit requirements
        if credit_requirements is None:
            credit_requirements = [60] * num_years

        # Create academic years and semesters
        for year_index in range(1, num_years + 1):
            credit_req = (
                credit_requirements[year_index - 1]
                if year_index - 1 < len(credit_requirements)
                else 60
            )

            academic_year = AcademicYear(
                user_id=user.id,
                label=f"Year {year_index}",
                order_index=year_index,
                credit_requirement=credit_req,
            )
            db.add(academic_year)
            db.flush()

            # Create semesters
            for sem_index in range(1, 3):
                semester = Semester(
                    academic_year_id=academic_year.id,
                    label=f"Semester {sem_index}",
                    order_index=sem_index,
                )
                db.add(semester)

        db.commit()
        db.refresh(user)

        return UserResponse.from_orm(user)

    @staticmethod
    def login(db: Session, username: str, password: str) -> UserResponse:
        user = db.query(User).filter(User.username == username).first()

        if not user or not AuthService.verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")

        return UserResponse.from_orm(user)
