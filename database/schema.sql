CREATE TABLE IF NOT EXISTS universities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    university_id INTEGER REFERENCES universities(id),
    major_id INTEGER REFERENCES majors(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS academic_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    label TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    credit_requirement INTEGER
);

CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year_id INTEGER NOT NULL REFERENCES academic_years(id),
    label TEXT NOT NULL,
    order_index INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester_id INTEGER NOT NULL REFERENCES semesters(id),
    academic_year_id INTEGER NOT NULL REFERENCES academic_years(id), -- ADD THIS LINE
    name TEXT NOT NULL,
    credit_value INTEGER NOT NULL,
    passing_grade REAL NOT NULL DEFAULT 5.0,
    max_grade REAL DEFAULT 10.0
);

-- CREATE TABLE IF NOT EXISTS subjects (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     semester_id INTEGER NOT NULL REFERENCES semesters(id),
--     name TEXT NOT NULL,
--     credit_value INTEGER NOT NULL,
--     passing_grade REAL NOT NULL DEFAULT 5.0,
--     max_grade REAL DEFAULT 10.0
-- );

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    name TEXT NOT NULL,
    weight REAL NOT NULL,
    max_score REAL NOT NULL DEFAULT 10.0,
    passing_grade REAL NOT NULL DEFAULT 5.0
);

CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id),
    score REAL,
    UNIQUE(assessment_id)
);

