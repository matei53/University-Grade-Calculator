from typing import Any, Dict, List, Optional

import requests


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self._restore_token()

    def _restore_token(self):
        """Try to restore token from session if available"""
        try:
            from models.session import Session

            if Session.is_logged_in():
                user = Session.get_user()
                token = user.get("token")
                if token:
                    self.token = token
        except (ImportError, RuntimeError, Exception):
            # Session not available or no user logged in
            pass

    def ensure_token(self):
        """Ensure token is available, refresh from session if needed"""
        if not self.token:
            self._restore_token()
        return self.token is not None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        # Always restore token from session to ensure we have the latest
        self._restore_token()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(
        self,
        username: str,
        password: str,
        num_years: int = 3,
        credit_requirements: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Register a new user"""
        payload = {
            "username": username,
            "password": password,
            "num_years": num_years,
        }
        if credit_requirements:
            payload["credit_requirements"] = credit_requirements

        response = requests.post(
            f"{self.base_url}/auth/register",
            json=payload,
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Registration error ({response.status_code}): {error_detail}")
        return response.json()

    def login(self, username: str, password: str) -> str:
        """Login and store token"""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Login error ({response.status_code}): {error_detail}")
        data = response.json()
        self.token = data["access_token"]

        # Try to get user info, but don't fail if it doesn't work
        try:
            user_data = self.get_profile()
            self.user_id = user_data.get("id")
        except Exception:
            pass

        return self.token

    def verify_token(self, token: str) -> bool:
        """Verify if a token is valid"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/verify-token",
                params={"token": token},
                headers=self._get_headers(),
            )
            return response.status_code == 200
        except Exception:
            return False

    # Profile endpoints
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/profile", headers=headers)
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Get profile error ({response.status_code}): {error_detail}")
        return response.json()

    def update_profile(
        self,
        university_id: Optional[int] = None,
        major_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update user profile"""
        payload = {}
        if university_id is not None:
            payload["university_id"] = university_id
        if major_id is not None:
            payload["major_id"] = major_id

        headers = self._get_headers()
        response = requests.put(f"{self.base_url}/profile", json=payload, headers=headers)
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Update profile error \
                    ({response.status_code}): {error_detail}")
        return response.json()

    def get_universities(self) -> List[Dict[str, Any]]:
        """Get list of universities"""
        response = requests.get(
            f"{self.base_url}/profile/universities",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Get universities error \
                    ({response.status_code}): {error_detail}")
        return response.json()

    def get_majors(self) -> List[Dict[str, Any]]:
        """Get list of majors"""
        response = requests.get(
            f"{self.base_url}/profile/majors",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Get majors error ({response.status_code}): {error_detail}")
        return response.json()

    # Subject endpoints
    def add_subject(
        self,
        name: str,
        credits: int,
        semester_index: int,
        year_level: int,
        passing_grade: float = 5.0,
        max_grade: float = 10.0,
    ) -> Dict[str, Any]:
        """Add a subject"""
        payload = {
            "name": name,
            "credits": credits,
            "semester_index": semester_index,
            "year_level": year_level,
            "passing_grade": passing_grade,
            "max_grade": max_grade,
        }
        headers = self._get_headers()
        response = requests.post(f"{self.base_url}/subjects", json=payload, headers=headers)
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Add subject error ({response.status_code}): {error_detail}")
        return response.json()

    def get_academic_years(self) -> List[Dict[str, Any]]:
        """Get user's academic years"""
        headers = self._get_headers()
        response = requests.get(f"{self.base_url}/subjects/years", headers=headers)
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Get academic years error \
                    ({response.status_code}): {error_detail}")
        return response.json()

    # Graduation endpoints
    def get_graduation_settings(self) -> Dict[str, Any]:
        """Get graduation settings (subject_average_weight, max_grade)"""
        response = requests.get(
            f"{self.base_url}/graduation/settings",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Get graduation settings error ({response.status_code})")
        return response.json()

    def update_graduation_settings(
        self,
        subject_average_weight: float,
        max_grade: float = 10.0,
    ) -> Dict[str, Any]:
        """Update graduation settings"""
        response = requests.put(
            f"{self.base_url}/graduation/settings",
            json={"subject_average_weight": subject_average_weight, "max_grade": max_grade},
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Update graduation settings error ({response.status_code})")
        return response.json()

    def get_final_assessments(self) -> List[Dict[str, Any]]:
        """Get all final assessments with their grades"""
        response = requests.get(
            f"{self.base_url}/graduation/assessments",
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Get final assessments error ({response.status_code})")
        return response.json()

    def add_final_assessment(
        self,
        name: str,
        weight: float,
        max_score: float = 10.0,
        passing_grade: float = 5.0,
    ) -> Dict[str, Any]:
        """Add a final assessment"""
        response = requests.post(
            f"{self.base_url}/graduation/assessments",
            json={
                "name": name,
                "weight": weight,
                "max_score": max_score,
                "passing_grade": passing_grade,
            },
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Add final assessment error ({response.status_code})")
        return response.json()

    def update_final_assessment(
        self,
        assessment_id: int,
        name: Optional[str] = None,
        weight: Optional[float] = None,
        max_score: Optional[float] = None,
        passing_grade: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update a final assessment"""
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if weight is not None:
            payload["weight"] = weight
        if max_score is not None:
            payload["max_score"] = max_score
        if passing_grade is not None:
            payload["passing_grade"] = passing_grade
        response = requests.put(
            f"{self.base_url}/graduation/assessments/{assessment_id}",
            json=payload,
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Update final assessment error ({response.status_code})")
        return response.json()

    def delete_final_assessment(self, assessment_id: int) -> None:
        """Delete a final assessment"""
        response = requests.delete(
            f"{self.base_url}/graduation/assessments/{assessment_id}",
            headers=self._get_headers(),
        )
        if response.status_code not in (200, 204):
            raise ValueError(f"Delete final assessment error ({response.status_code})")

    def set_final_assessment_grade(
        self,
        assessment_id: int,
        score: Optional[float],
    ) -> Dict[str, Any]:
        """Set or update the grade for a final assessment"""
        response = requests.put(
            f"{self.base_url}/graduation/assessments/{assessment_id}/grade",
            json={"score": score},
            headers=self._get_headers(),
        )
        if response.status_code != 200:
            raise ValueError(f"Set final assessment grade error ({response.status_code})")
        return response.json()

    # Assessment endpoints
    def add_assessment(
        self,
        subject_id: int,
        name: str,
        weight: float,
        score: float,
        max_score: float = 10.0,
        passing_grade: float = 5.0,
    ) -> Dict[str, Any]:
        """Add an assessment to a subject"""
        payload = {
            "name": name,
            "weight": weight,
            "score": score,
            "max_score": max_score,
            "passing_grade": passing_grade,
        }
        headers = self._get_headers()
        response = requests.post(
            f"{self.base_url}/assessments/{subject_id}",
            json=payload,
            headers=headers,
        )
        if response.status_code != 200:
            error_detail = response.json() if response.text else "No response body"
            raise ValueError(f"Add assessment error \
                    ({response.status_code}): {error_detail}")
        return response.json()
