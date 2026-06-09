"""
Service for managing year progression eligibility and credit requirements.

credit passing percentage: Handles calculation of whether students meet advancement criteria
credit passing percentage: Manages modifiable progression thresholds per user
"""

from sqlalchemy.orm import Session

from models import AcademicYear, Subject, YearProgressionRequirement, User


class ProgressionService:
    """
    credit passing percentage: Service to handle year progression eligibility logic
    credit passing percentage: Checks if students meet credit percentage requirements to advance
    """

    @staticmethod
    def get_or_create_progression_requirement(
        db: Session, user_id: int, target_year: int, credit_percentage: float = 70.0, cumulative: bool = False
    ) -> YearProgressionRequirement:
        """
        credit passing percentage: Get existing progression requirement or create default one
        credit passing percentage: Default threshold is 70% of credits for target year

        Args:
            db: Database session
            user_id: User ID
            target_year: Target academic year to advance to (e.g., 2 for Year 2)
            credit_percentage: Required credit percentage (default 70%)
            cumulative: Whether requirement is cumulative across years

        Returns:
            YearProgressionRequirement object
        """
        # credit passing percentage: Query existing requirement for this user and target year
        existing = (
            db.query(YearProgressionRequirement)
            .filter(
                YearProgressionRequirement.user_id == user_id,
                YearProgressionRequirement.target_year == target_year,
            )
            .first()
        )

        if existing:
            return existing

        # credit passing percentage: Create new default requirement if none exists
        new_req = YearProgressionRequirement(
            user_id=user_id,
            target_year=target_year,
            credit_percentage=credit_percentage,
            cumulative=cumulative,
        )
        db.add(new_req)
        db.commit()
        db.refresh(new_req)
        return new_req

    @staticmethod
    def get_progression_requirements(db: Session, user_id: int) -> list[YearProgressionRequirement]:
        """
        credit passing percentage: Retrieve all progression requirements for a user
        credit passing percentage: Lists thresholds for advancing to each year

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of YearProgressionRequirement objects
        """
        # credit passing percentage: Query all progression requirements for this user
        return (
            db.query(YearProgressionRequirement)
            .filter(YearProgressionRequirement.user_id == user_id)
            .order_by(YearProgressionRequirement.target_year)
            .all()
        )

    @staticmethod
    def update_progression_requirement(
        db: Session, user_id: int, target_year: int, credit_percentage: float, cumulative: bool = False
    ) -> YearProgressionRequirement:
        """
        credit passing percentage: Update progression requirement percentage for a target year
        credit passing percentage: Allows students to customize their advancement thresholds

        Args:
            db: Database session
            user_id: User ID
            target_year: Target year to advance to
            credit_percentage: New required percentage (0-100)
            cumulative: Whether to use cumulative credits

        Returns:
            Updated YearProgressionRequirement object
        """
        # credit passing percentage: Get or create the requirement
        req = ProgressionService.get_or_create_progression_requirement(
            db, user_id, target_year, credit_percentage, cumulative
        )

        # credit passing percentage: Update the percentage and cumulative flag
        req.credit_percentage = credit_percentage
        req.cumulative = cumulative
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def calculate_year_credits(db: Session, user_id: int, year_level: int) -> tuple[int, int]:
        """
        credit passing percentage: Calculate earned and total credits for a specific year
        credit passing percentage: Counts only passed subjects (grade >= passing_grade)

        Args:
            db: Database session
            user_id: User ID
            year_level: Academic year level (1, 2, 3, etc.)

        Returns:
            Tuple of (credits_earned, total_credits)
        """
        # credit passing percentage: Get all academic years for this user
        academic_year = (
            db.query(AcademicYear)
            .filter(
                AcademicYear.user_id == user_id,
                AcademicYear.order_index == year_level,
            )
            .first()
        )

        if not academic_year:
            return 0, 0

        # credit passing percentage: Get all subjects for this academic year
        subjects = db.query(Subject).filter(Subject.academic_year_id == academic_year.id).all()

        credits_earned = 0
        total_credits = 0

        for subject in subjects:
            total_credits += subject.credit_value

            if subject.assessments:
                total_score = 0.0
                total_weight = 0.0

                for assessment in subject.assessments:
                    if assessment.grade and assessment.grade.score is not None:
                        total_score += assessment.grade.score * assessment.weight
                        total_weight += assessment.weight

                if total_weight >= 100.0:
                    average_score = total_score / total_weight
                    if average_score >= subject.passing_grade:
                        credits_earned += subject.credit_value

        year_total = academic_year.credit_requirement if academic_year.credit_requirement else total_credits
        return credits_earned, year_total

    @staticmethod
    def calculate_cumulative_credits(db: Session, user_id: int, up_to_year: int) -> tuple[int, int]:
        """
        credit passing percentage: Calculate cumulative earned and total credits across multiple years
        credit passing percentage: Sums credits from Year 1 through up_to_year

        Args:
            db: Database session
            user_id: User ID
            up_to_year: Include years up to and including this year

        Returns:
            Tuple of (total_credits_earned, total_credits_required)
        """
        # credit passing percentage: Initialize cumulative totals
        total_earned = 0
        total_required = 0

        # credit passing percentage: Sum credits from each year up to target
        for year in range(1, up_to_year + 1):
            earned, required = ProgressionService.calculate_year_credits(db, user_id, year)
            total_earned += earned
            total_required += required

        return total_earned, total_required

    @staticmethod
    def check_year_eligibility(
        db: Session, user_id: int, target_year: int
    ) -> dict:
        """
        credit passing percentage: Check if student is eligible to advance to target year
        credit passing percentage: Compares earned credits to required percentage threshold

        Args:
            db: Database session
            user_id: User ID
            target_year: Target year to advance to (e.g., 2 for Year 2 advancement)

        Returns:
            Dictionary with eligibility status and credit details
        """
        # credit passing percentage: Get the progression requirement for this target year
        requirement = ProgressionService.get_or_create_progression_requirement(
            db, user_id, target_year
        )

        # credit passing percentage: Prerequisite year is always one below the target, floored at 1
        # credit passing percentage: Extracted once to avoid duplication across cumulative/single branches
        prerequisites_year = max(target_year - 1, 1)

        # credit passing percentage: Choose cumulative or single-year credit calculation
        if requirement.cumulative:
            # credit passing percentage: Sum credits across Year 1 through prerequisites_year
            earned, required = ProgressionService.calculate_cumulative_credits(
                db, user_id, prerequisites_year
            )
        else:
            # credit passing percentage: Count credits for the prerequisite year only
            earned, required = ProgressionService.calculate_year_credits(
                db, user_id, prerequisites_year
            )

        # credit passing percentage: Calculate percentage earned
        if required > 0:
            percentage_earned = (earned / required) * 100.0
        else:
            percentage_earned = 0.0

        # credit passing percentage: Check eligibility
        is_eligible = percentage_earned >= requirement.credit_percentage

        return {
            "target_year": target_year,
            "is_eligible": is_eligible,
            "credits_earned": earned,
            "credits_required": required,
            "current_percentage": round(percentage_earned, 2),
            "required_percentage": requirement.credit_percentage,
            "cumulative": requirement.cumulative,
        }

    @staticmethod
    def get_all_year_eligibility(db: Session, user_id: int) -> list[dict]:
        """
        credit passing percentage: Check eligibility for all years in student's program
        credit passing percentage: Returns status for advancing to Year 2, Year 3, etc.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of eligibility status dictionaries for each year
        """
        # credit passing percentage: Get user's academic years
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # credit passing percentage: Get max year level
        max_year = (
            db.query(AcademicYear)
            .filter(AcademicYear.user_id == user_id)
            .order_by(AcademicYear.order_index.desc())
            .first()
        )

        if not max_year:
            return []

        # credit passing percentage: Check eligibility for each possible target year
        eligibility_list = []
        for target_year in range(2, max_year.order_index + 1):
            eligibility = ProgressionService.check_year_eligibility(db, user_id, target_year)
            eligibility_list.append(eligibility)

        return eligibility_list