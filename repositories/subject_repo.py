from database.db import get_connection

class SubjectRepo:
    @staticmethod
    def add_academic_year(user_id, year_name, target_credits):
        with get_connection() as conn:
            cursor = conn.cursor()
            # Match the schema: label, order_index, credit_requirement
            cursor.execute(
                "INSERT INTO academic_years (user_id, label, order_index, credit_requirement) VALUES (?, ?, ?, ?)",
                (user_id, year_name, 1, target_credits)
            )
            year_id = cursor.lastrowid
            
            # Auto-generate Semesters for this year so the Subjects table has a semester_id to link to
            cursor.execute("INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semester 1', 1)", (year_id,))
            cursor.execute("INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semester 2', 2)", (year_id,))
            
            conn.commit()
            return year_id

    @staticmethod
    def add_subject(year_id, name, credits, semester_index):
        with get_connection() as conn:
            cursor = conn.cursor()
            # 1. Find the correct semester_id for this year
            sem_row = cursor.execute(
                "SELECT id FROM semesters WHERE academic_year_id = ? AND order_index = ?", 
                (year_id, semester_index)
            ).fetchone()
            
            if not sem_row:
                raise ValueError("Semester not found for this year.")
                
            # 2. Insert the subject matching the schema: semester_id, name, credit_value
            cursor.execute(
                "INSERT INTO subjects (semester_id, name, credit_value) VALUES (?, ?, ?)",
                (sem_row['id'], name, credits)
            )
            conn.commit()
            return cursor.lastrowid