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
    score: float
    max_score: float = 10.0
    passing_grade: float = 5.0


class GradeResponse(BaseModel):
    id: int
    score: Optional[float]

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    weight: float
    max_score: float
    passing_grade: float
    grades: List[GradeResponse] = []

    class Config:
        from_attributes = True


# Profile Updates
class UpdateProfileRequest(BaseModel):
    university_id: Optional[int] = None
    major_id: Optional[int] = None


UpdateUserProfile = UpdateProfileRequest

# Dashboard
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    university_short: str
    year_level: int
    weighted_avg: float
    credits: int
    is_current_user: bool

class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    current_user_visible: bool
    filter_university: Optional[str] = None
    filter_major: Optional[str] = None

class VisibilityUpdate(BaseModel):
    visible: bool

class VisibilityResponse(BaseModel):
    visible: bool
