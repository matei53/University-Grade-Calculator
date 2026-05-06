from database.db import get_connection

class SubjectRepo:
    @staticmethod
    def create_years_for_user(user_id, num_years, credit_requirements=None):
        """Create multiple years with semesters for a user during signup."""
        if credit_requirements is None:
            credit_requirements = [60] * num_years
        
        print(f"[SubjectRepo] Creating {num_years} years for user {user_id}")
        
        with get_connection() as conn:
            cursor = conn.cursor()
            for year_index in range(1, num_years + 1):
                # Get credit requirement for this year (or default to 60)
                credit_req = credit_requirements[year_index - 1] if year_index - 1 < len(credit_requirements) else 60
                
                print(f"[SubjectRepo] Inserting Year {year_index} with {credit_req} credits")
                
                # Create academic year with label "Year X"
                cursor.execute(
                    "INSERT INTO academic_years (user_id, label, order_index, credit_requirement) VALUES (?, ?, ?, ?)",
                    (user_id, f"Year {year_index}", year_index, credit_req)
                )
                year_id = cursor.lastrowid
                
                print(f"[SubjectRepo] Created year with ID {year_id}")
                
                # Create 2 semesters for this year
                cursor.execute(
                    "INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semester 1', 1)",
                    (year_id,)
                )
                cursor.execute(
                    "INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semester 2', 2)",
                    (year_id,)
                )
            conn.commit()
            print(f"[SubjectRepo] Committed all years to database")

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