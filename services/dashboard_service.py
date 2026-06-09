from typing import Optional

from client.api_client import APIClient


class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user_id):
        """Fetches dynamic data from the API server."""
        client = APIClient()
        all_data = {}

        try:
            years = client.get_academic_years()

            for year in years:
                year_num = year["order_index"]
                all_data[year_num] = {
                    "target_credits": year.get("credit_requirement"),
                    "subjects": [],
                }

                for subject in year.get("subjects", []):
                    # Calculate average grade from assessments
                    assessments = subject.get("assessments", [])

                    total_grade = 0.0
                    has_grades = False
                    subject_max = subject.get("max_grade", 10.0)

                    grade_infos = []
                    for assessment in assessments:
                        grade_obj = assessment.get("grade")
                        if grade_obj is not None:
                            score = grade_obj.get("score")
                            if score is not None:
                                has_grades = True
                                max_score = assessment.get("max_score", 10.0)
                                # Normalize and weight the score
                                normalized_score = (
                                    (float(score) / float(max_score)) if float(max_score) > 0 else 0
                                )
                                total_grade += (
                                    normalized_score
                                    * (float(assessment.get("weight", 0)) / 100.0)
                                    * float(subject_max)
                                )
                            if grade_obj.get("id") is not None:
                                grade_infos.append(
                                    {
                                        "grade_id": grade_obj["id"],
                                        "assessment_id": assessment.get("id"),
                                        "name": assessment.get("name"),
                                        "score": score,
                                    }
                                )

                    subject_grade_id = grade_infos[0]["grade_id"] if len(grade_infos) == 1 else None

                    assessments_list = []
                    for assessment in subject.get("assessments", []):
                        grade_obj = assessment.get("grade")
                        assessments_list.append(
                            {
                                "id": assessment.get("id"),
                                "name": assessment.get("name"),
                                "weight": float(assessment.get("weight", 0.0)),
                                "max_score": float(assessment.get("max_score", 10.0)),
                                "passing_grade": float(assessment.get("passing_grade", 5.0)),
                                "grade_id": grade_obj.get("id") if grade_obj else None,
                                "grade_score": grade_obj.get("score") if grade_obj else None,
                            }
                        )

                    all_data[year_num]["subjects"].append(
                        {
                            "subject_id": subject["id"],
                            "name": subject["name"],
                            "credits": subject["credit_value"],
                            "grade": (round(total_grade, 2) if has_grades else None),
                            "semester_index": subject.get("semester_index", 1),
                            "year_level": subject.get("year_level", year_num),
                            "passing_grade": subject.get("passing_grade", 5.0),
                            "max_grade": subject_max,
                            "grade_id": subject_grade_id,
                            "grade_details": grade_infos,
                            "assessments": assessments_list,
                        }
                    )
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")
            return {}

        return all_data

    @staticmethod
    def calculate_stats(
        all_years_data,
        up_to_year,
        total_program_credits=180,
        passing_grade=5.0,
    ):
        total_weighted_points = 0
        total_credits_with_grades = 0
        total_credits_earned = 0

        for year_num, year_data in all_years_data.items():
            if year_num <= up_to_year:
                for subject in year_data["subjects"]:
                    grade = subject.get("grade")
                    credits = subject.get("credits", 0)
                    subj_passing_grade = subject.get("passing_grade", passing_grade)

                    if grade is not None:
                        total_weighted_points += grade * credits
                        total_credits_with_grades += credits
                        if grade >= subj_passing_grade:
                            total_credits_earned += credits

        weighted_avg = (
            total_weighted_points / total_credits_with_grades
            if total_credits_with_grades > 0
            else 0.0
        )

        return {
            "weighted_avg": round(weighted_avg, 2),
            "credits": total_credits_earned,
            "progress": (
                int((total_credits_earned / total_program_credits) * 100)
                if total_program_credits > 0
                else 0
            ),
        }

    @staticmethod
    def calculate_graduation_grade(
        overall_avg: Optional[float],
        settings: dict,
        final_assessments: list[dict],
    ) -> Optional[float]:
        """
        Compute the final graduation grade.

        Formula:
          final = (subject_average_weight/100) × overall_avg
                + Σ [(fa_weight/100) × (fa_score/fa_max_score) × max_grade]

        Returns None when there are no grades at all to base a result on.
        """
        if overall_avg is None and not final_assessments:
            return None

        max_grade = float(settings.get("max_grade", 10.0))
        subj_weight = float(settings.get("subject_average_weight", 100.0))

        total = (subj_weight / 100.0) * (overall_avg or 0.0)

        for fa in final_assessments:
            grade_obj = fa.get("grade")
            if grade_obj is None or grade_obj.get("score") is None:
                continue
            score = float(grade_obj["score"])
            fa_max = float(fa.get("max_score", 10.0))
            weight = float(fa.get("weight", 0.0))
            if fa_max > 0:
                total += (weight / 100.0) * (score / fa_max) * max_grade

        return round(total, 2)
