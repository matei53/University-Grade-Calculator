from database.db import get_connection

class AssessmentRepo:
    @staticmethod
    def add_assessment(subject_id, name, weight, score, max_score=10.0, passing_grade=5.0):
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO assessments (subject_id, name, weight, max_score, passing_grade) VALUES (?, ?, ?, ?, ?)",
                (subject_id, name, weight, max_score, passing_grade)
            )
            assessment_id = cursor.lastrowid
            
            cursor.execute(
                "INSERT INTO grades (assessment_id, score) VALUES (?, ?)",
                (assessment_id, score)
            )
            conn.commit()