-- ============================================================
--  STUDENT PERFORMANCE ANALYSIS — Schema
--  ADBMS Project | PostgreSQL
-- ============================================================

-- Drop existing tables (safe to re-run)
DROP TABLE IF EXISTS grades CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS enrollment CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- ─── 1. DEPARTMENTS ──────────────────────────────────────────
CREATE TABLE departments (
    dept_id     SERIAL PRIMARY KEY,
    dept_name   VARCHAR(100) NOT NULL,
    dept_code   VARCHAR(10)  NOT NULL UNIQUE
);

INSERT INTO departments (dept_name, dept_code) VALUES
    ('Computer Science', 'CS'),
    ('Mathematics',      'MATH'),
    ('Physics',          'PHY'),
    ('English',          'ENG');

-- ─── 2. STUDENTS ─────────────────────────────────────────────
CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    gender          CHAR(1)      CHECK (gender IN ('M','F')),
    age             INT          CHECK (age BETWEEN 15 AND 30),
    dept_id         INT          REFERENCES departments(dept_id),
    study_hours     NUMERIC(4,1),   -- hours/week from dataset
    sleep_hours     NUMERIC(4,1),   -- hours/night from dataset
    motivation_level VARCHAR(10)  CHECK (motivation_level IN ('Low','Medium','High')),
    family_support  VARCHAR(10)  CHECK (family_support   IN ('Low','Medium','High')),
    enrolled_on     DATE DEFAULT CURRENT_DATE
);

-- ─── 3. COURSES ──────────────────────────────────────────────
CREATE TABLE courses (
    course_id   SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    dept_id     INT REFERENCES departments(dept_id),
    credits     INT DEFAULT 3,
    semester    INT CHECK (semester BETWEEN 1 AND 8)
);

-- ─── 4. ENROLLMENT ───────────────────────────────────────────
CREATE TABLE enrollment (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INT REFERENCES students(student_id) ON DELETE CASCADE,
    course_id       INT REFERENCES courses(course_id)   ON DELETE CASCADE,
    academic_year   INT  NOT NULL,
    semester        INT  NOT NULL CHECK (semester BETWEEN 1 AND 8),
    UNIQUE (student_id, course_id, academic_year, semester)
);

-- ─── 5. GRADES (PARTITIONED BY SEMESTER) ─────────────────────
--  This demonstrates RANGE PARTITIONING — a key ADBMS concept
CREATE TABLE grades (
    grade_id        SERIAL,
    enrollment_id   INT  NOT NULL,
    g1              NUMERIC(5,2),  -- first period grade  (0-20 scale from UCI)
    g2              NUMERIC(5,2),  -- second period grade
    g3              NUMERIC(5,2),  -- final grade
    exam_score      NUMERIC(5,2),  -- from Student Performance Factors dataset
    passed          BOOLEAN GENERATED ALWAYS AS (g3 >= 10) STORED,
    semester        INT  NOT NULL CHECK (semester BETWEEN 1 AND 8)
) PARTITION BY RANGE (semester);

-- Create partition for each semester pair
CREATE TABLE grades_sem1_2 PARTITION OF grades FOR VALUES FROM (1) TO (3);
CREATE TABLE grades_sem3_4 PARTITION OF grades FOR VALUES FROM (3) TO (5);
CREATE TABLE grades_sem5_6 PARTITION OF grades FOR VALUES FROM (5) TO (7);
CREATE TABLE grades_sem7_8 PARTITION OF grades FOR VALUES FROM (7) TO (9);

-- ─── 6. ATTENDANCE ───────────────────────────────────────────
CREATE TABLE attendance (
    attendance_id       SERIAL PRIMARY KEY,
    enrollment_id       INT REFERENCES enrollment(enrollment_id) ON DELETE CASCADE,
    total_classes       INT NOT NULL DEFAULT 40,
    classes_attended    INT NOT NULL DEFAULT 40,
    attendance_pct      NUMERIC(5,2) GENERATED ALWAYS AS
                            (ROUND((classes_attended::NUMERIC / total_classes) * 100, 2)) STORED,
    at_risk             BOOLEAN GENERATED ALWAYS AS
                            ((classes_attended::NUMERIC / total_classes) * 100 < 75) STORED
);
