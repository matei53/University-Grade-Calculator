from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserRegister, UserLogin, Token, UserResponse
from services.auth_service import AuthService
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = AuthService.sign_up(
            db,
            user_data.username,
            user_data.password,
            user_data.num_years,
            user_data.credit_requirements
        )
        token = AuthService.create_access_token(user.id)
        return {"access_token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = AuthService.login(db, user_data.username, user_data.password)
        token = AuthService.create_access_token(user.id)
        return {"access_token": token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/verify-token")
def verify_token(token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    # Try to get token from query param first, then from Authorization header
    actual_token = token
    
    if not actual_token and authorization:
        try:
            scheme, token_from_header = authorization.split()
            if scheme.lower() == "bearer":
                actual_token = token_from_header
        except ValueError:
            pass
    
    if not actual_token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    user_id = AuthService.verify_token(actual_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": user_id}
