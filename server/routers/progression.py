"""
API endpoints for year progression eligibility and credit requirements.

credit passing percentage: Provides endpoints to retrieve and modify progression thresholds
credit passing percentage: Allows students to customize their advancement requirements
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import User
from schemas import YearProgressionRequirementResponse, YearProgressionRequirementUpdate, YearEligibilityResponse
from services.progression_service import ProgressionService



router = APIRouter(prefix="/progression", tags=["progression"])


@router.get("/requirements", response_model=list[YearProgressionRequirementResponse])
def get_progression_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    credit passing percentage: Retrieve all progression requirements for current user
    credit passing percentage: Returns customizable thresholds for advancing to each year

    Returns:
        List of progression requirement objects for each target year
    """
    # credit passing percentage: Get all requirements from service
    requirements = ProgressionService.get_progression_requirements(db, current_user.id)
    return requirements


@router.put("/requirements/{target_year}")
def update_progression_requirement(
    target_year: int,
    update_data: YearProgressionRequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    credit passing percentage: Update progression requirement for a specific target year
    credit passing percentage: Allows student to customize credit percentage needed to advance

    Args:
        target_year: Target year to advance to (e.g., 2 for advancing to Year 2)
        update_data: New credit percentage and cumulative flag

    Returns:
        Updated requirement object
    """
    # credit passing percentage: Validate input range
    if update_data.credit_percentage < 0 or update_data.credit_percentage > 100:
        return {"error": "Credit percentage must be between 0 and 100"}

    # credit passing percentage: Update requirement through service
    updated = ProgressionService.update_progression_requirement(
        db,
        current_user.id,
        target_year,
        update_data.credit_percentage,
        update_data.cumulative,
    )

    return {
        "message": "Progression requirement updated",
        "target_year": updated.target_year,
        "credit_percentage": updated.credit_percentage,
        "cumulative": updated.cumulative,
    }


@router.get("/eligibility/{target_year}", response_model=YearEligibilityResponse)
def get_year_eligibility(
    target_year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    credit passing percentage: Check if student is eligible to advance to specific year
    credit passing percentage: Shows earned credits vs required threshold

    Args:
        target_year: Target year to check eligibility for

    Returns:
        Eligibility status with credit details
    """
    # credit passing percentage: Check eligibility through service
    eligibility = ProgressionService.check_year_eligibility(db, current_user.id, target_year)
    return eligibility


@router.get("/eligibility", response_model=list[YearEligibilityResponse])
def get_all_year_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    credit passing percentage: Check eligibility for all years in student's program
    credit passing percentage: Returns advancement status for each academic year

    Returns:
        List of eligibility statuses for all years
    """
    # credit passing percentage: Get eligibility for all years through service
    eligibility_list = ProgressionService.get_all_year_eligibility(db, current_user.id)
    return eligibility_list
