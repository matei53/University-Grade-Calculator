from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import LeaderboardResponse, LeaderboardEntry, VisibilityUpdate, VisibilityResponse
from dependencies import get_current_user
from services.leaderboard_service import build_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("", response_model=LeaderboardResponse)
def get_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = build_leaderboard(db, current_user)
    return LeaderboardResponse(
        entries=[LeaderboardEntry(**e) for e in data["entries"]],
        current_user_visible=data["current_user_visible"],
        filter_university=data["filter_university"],
        filter_major=data["filter_major"],
    )

@router.get("/visibility", response_model=VisibilityResponse)
def get_visibility(current_user: User = Depends(get_current_user)):
    return VisibilityResponse(visible=bool(current_user.leaderboard_visible))

@router.patch("/visibility", response_model=VisibilityResponse)
def set_visibility(
    body: VisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    user.leaderboard_visible = body.visible
    db.commit()
    return VisibilityResponse(visible=body.visible)