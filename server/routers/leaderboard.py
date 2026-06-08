from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import User
from schemas import (
    LeaderboardEntry,
    LeaderboardResponse,
    VisibilityResponse,
    VisibilityUpdate,
)
from services.leaderboard_service import MAX_PAGE_SIZE, build_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardResponse)
def get_leaderboard(
    year_level: int | None = Query(None, ge=1, le=10),
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(2, ge=1, le=MAX_PAGE_SIZE),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = build_leaderboard(
        db,
        current_user,
        year_level=year_level,
        search=search,
        page=page,
        page_size=page_size,
    )
    return LeaderboardResponse(
        podium=[LeaderboardEntry(**e) for e in data["podium"]],
        entries=[LeaderboardEntry(**e) for e in data["entries"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        total_pages=data["total_pages"],
        current_user_visible=data["current_user_visible"],
        filter_university=data["filter_university"],
        filter_major=data["filter_major"],
        filter_year_level=data["filter_year_level"],
        current_user_year_level=data["current_user_year_level"],
        available_year_levels=data["available_year_levels"],
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
    current_user.leaderboard_visible = body.visible
    db.add(current_user)  # or just db.commit() if user is already tracked
    db.commit()
    return VisibilityResponse(visible=body.visible)
