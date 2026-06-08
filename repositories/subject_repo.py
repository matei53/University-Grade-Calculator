from database.db import get_connection


class SubjectRepo:

    @staticmethod
    def create_years_for_user(user_id, num_years, credit_requirements=None):
        """
        Creates the academic years and semesters at account creation (Sign Up),
        using the custom credit requirements entered by the user.
        """
        if credit_requirements is None:
            credit_requirements = [60] * num_years

        with get_connection() as conn:
            cursor = conn.cursor()
            for year_index in range(1, num_years + 1):
                # Get the credits for the current year (or 60 as default)
                credit_req = (
                    credit_requirements[year_index - 1]
                    if year_index - 1 < len(credit_requirements)
                    else 60
                )

                # Create the year
                cursor.execute(
                    "INSERT INTO academic_years \
                    (user_id, label, order_index, credit_requirement) \
                    VALUES (?, ?, ?, ?)",
                    (
                        user_id,
                        f"Year {year_index}",
                        year_index,
                        credit_req,
                    ),
                )
                year_id = cursor.lastrowid

                # Create the 2 semesters for this year
                cursor.execute(
                    "INSERT INTO semesters \
                    (academic_year_id, label, order_index) \
                    VALUES (?, 'Semester 1', 1)",
                    (year_id,),
                )
                cursor.execute(
                    "INSERT INTO semesters \
                    (academic_year_id, label, order_index) \
                    VALUES (?, 'Semester 2', 2)",
                    (year_id,),
                )
            conn.commit()

    @staticmethod
    def _ensure_year_and_semesters_exist(conn, user_id, year_level):
        """
        Internal function: Checks if the Academic Year exists for the user.
        If it doesn't exist, it creates it automatically (fallback).
        """
        label = f"Year {year_level}"

        # 1. Look up the existing year
        year_row = conn.execute(
            "SELECT id FROM academic_years WHERE user_id = ? \
                AND order_index = ?",
            (user_id, year_level),
        ).fetchone()

        if year_row:
            return year_row["id"]

        # 2. If it doesn't exist, create the year with 60 default credits
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO academic_years \
            (user_id, label, order_index, credit_requirement) \
                VALUES (?, ?, ?, ?)",
            (user_id, label, year_level, 60),
        )
        year_id = cursor.lastrowid

        # 3. Automatically create semesters for this new year
        cursor.execute(
            "INSERT INTO semesters \
            (academic_year_id, label, order_index) \
            VALUES (?, 'Semester 1', 1)",
            (year_id,),
        )
        cursor.execute(
            "INSERT INTO semesters \
            (academic_year_id, label, order_index) \
            VALUES (?, 'Semester 2', 2)",
            (year_id,),
        )

        return year_id

    @staticmethod
    def add_subject(
        user_id,
        subject_name,
        credits,
        semester_index,
        year_level,
        passing_grade=5.0,
        max_grade=10.0,
    ):
        """
        Adds a subject. Creates the year automatically if needed via fallback.
        """
        with get_connection() as conn:
            year_id = SubjectRepo._ensure_year_and_semesters_exist(conn, user_id, year_level)
            cursor = conn.cursor()

            sem_row = cursor.execute(
                "SELECT id FROM semesters WHERE academic_year_id = ? \
                    AND order_index = ?",
                (year_id, semester_index),
            ).fetchone()

            if not sem_row:
                raise ValueError(f"Semester {semester_index} not found for Year {year_level}.")

            cursor.execute(
                "INSERT INTO subjects \
                (semester_id, academic_year_id, name, credit_value, \
                    passing_grade, max_grade) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    sem_row["id"],
                    year_id,
                    subject_name,
                    credits,
                    passing_grade,
                    max_grade,
                ),
            )
            conn.commit()
            return cursor.lastrowid
