from database.db import get_connection

class AssessmentRepo:
    @staticmethod
    def add_assessment(subject_id, name, weight, score):
        with get_connection() as conn:
            cursor = conn.cursor()
            # 1. Save to assessments table (it expects max_score, not the actual score)[cite: 5]
            cursor.execute(
                "INSERT INTO assessments (subject_id, name, weight, max_score) VALUES (?, ?, ?, 10.0)",
                (subject_id, name, weight)
            )
            assessment_id = cursor.lastrowid
            
            # 2. Save the actual grade to the dedicated grades table[cite: 5]
            cursor.execute(
                "INSERT INTO grades (assessment_id, score) VALUES (?, ?)",
                (assessment_id, score)
            )
            conn.commit()