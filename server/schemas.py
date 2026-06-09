from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# Auth
class UserRegister(BaseModel):
    username: str
    password: str
    num_years: int = 3
    credit_requirements: Optional[List[int]] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    university_id: Optional[int] = None
    major_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Profile
class UserProfile(BaseModel):
    id: int
    username: str
    university_name: Optional[str] = None
    major_name: Optional[str] = None


# University/Major
class CreateUniversityRequest(BaseModel):
    name: str


class CreateMajorRequest(BaseModel):
    name: str


class UniversityResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MajorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Academic structure
class SemesterResponse(BaseModel):
    id: int
    label: str
    order_index: int

    class Config:
        from_attributes = True


class SubjectRequest(BaseModel):
    name: str
    credits: int
    semester_index: int
    year_level: int
    passing_grade: float = 5.0
    max_grade: float = 10.0


class SubjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    semester_index: Optional[int] = None
    year_level: Optional[int] = None
    passing_grade: Optional[float] = None
    max_grade: Optional[float] = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    credit_value: int
    passing_grade: float
    max_grade: float
    semester_id: int
    academic_year_id: int
    assessments: List["AssessmentResponse"] = []

    class Config:
        from_attributes = True


class AcademicYearResponse(BaseModel):
    id: int
    label: str
    order_index: int
    credit_requirement: Optional[int]
    semesters: List[SemesterResponse]
    subjects: List[SubjectResponse] = []

    class Config:
        from_attributes = True


# Assessments
class AssessmentRequest(BaseModel):
    name: str
    weight: float
    score: Optional[float] = None
    max_score: float = 10.0
    passing_grade: float = 5.0


class AssessmentUpdateRequest(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    max_score: Optional[float] = None
    passing_grade: Optional[float] = None


class GradeResponse(BaseModel):
    id: int
    score: Optional[float]

    class Config:
        from_attributes = True


class UpdateGradeRequest(BaseModel):
    score: Optional[float] = None


class AssessmentResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    weight: float
    max_score: float
    passing_grade: float
    grade: Optional[GradeResponse] = None

    class Config:
        from_attributes = True


# Profile Updates
class UpdateProfileRequest(BaseModel):
    university_id: Optional[int] = None
    major_id: Optional[int] = None


UpdateUserProfile = UpdateProfileRequest


# Leaderboard
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    university_name: str
    year_level: int
    weighted_avg: float
    credits: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    podium: List[LeaderboardEntry] = []
    entries: List[LeaderboardEntry] = []
    total: int = 0
    page: int = 1
    page_size: int = 2
    total_pages: int = 0
    current_user_visible: bool
    filter_university: Optional[str] = None
    filter_major: Optional[str] = None
    filter_year_level: Optional[int] = None
    current_user_year_level: int = 1
    available_year_levels: List[int] = []


class VisibilityUpdate(BaseModel):
    visible: bool


class VisibilityResponse(BaseModel):
    visible: bool


# Graduation
class GraduationSettingsResponse(BaseModel):
    id: int
    subject_average_weight: float
    max_grade: float

    class Config:
        from_attributes = True


class GraduationSettingsUpdate(BaseModel):
    subject_average_weight: float
    max_grade: float = 10.0


class FinalAssessmentGradeResponse(BaseModel):
    id: int
    score: Optional[float]

    class Config:
        from_attributes = True


class FinalAssessmentResponse(BaseModel):
    id: int
    name: str
    weight: float
    max_score: float
    passing_grade: float
    grade: Optional[FinalAssessmentGradeResponse] = None

    class Config:
        from_attributes = True


class FinalAssessmentRequest(BaseModel):
    name: str
    weight: float
    max_score: float = 10.0
    passing_grade: float = 5.0


class FinalAssessmentUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    max_score: Optional[float] = None
    passing_grade: Optional[float] = None


class FinalAssessmentGradeUpdate(BaseModel):
    score: Optional[float] = None


# credit passing percentage
class YearProgressionRequirementResponse(BaseModel):
    id: int
    target_year: int
    credit_percentage: float
    cumulative: bool

    class Config:
        from_attributes = True


class YearProgressionRequirementUpdate(BaseModel):
    credit_percentage: float
    cumulative: bool = False


# credit passing percentage
class YearEligibilityResponse(BaseModel):
    target_year: int
    is_eligible: bool
    credits_earned: int
    credits_required: int
    current_percentage: float
    required_percentage: float
    cumulative: bool
