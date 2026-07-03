-- ============================================================
--  MATERIALIZED VIEWS & ADVANCED QUERIES
--  These demonstrate the "A" in ADBMS — Advanced features
-- ============================================================

-- ─── MATERIALIZED VIEW 1: Student GPA Summary ────────────────
-- Pre-computes CGPA so the dashboard loads fast
CREATE MATERIALIZED VIEW mv_student_gpa AS
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name   AS student_name,
    d.dept_name,
    d.dept_code,
    s.study_hours,
    s.sleep_hours,
    s.motivation_level,
    e.semester,
    ROUND(AVG(g.g3), 2)                  AS avg_grade,
    ROUND(AVG(g.exam_score), 2)          AS avg_exam_score,
    COUNT(g.grade_id)                    AS courses_taken,
    SUM(CASE WHEN g.passed THEN 1 ELSE 0 END) AS courses_passed
FROM students s
JOIN departments d      ON s.dept_id       = d.dept_id
JOIN enrollment e       ON s.student_id    = e.student_id
JOIN grades g           ON e.enrollment_id = g.enrollment_id
GROUP BY s.student_id, student_name, d.dept_name, d.dept_code,
         s.study_hours, s.sleep_hours, s.motivation_level, e.semester;

-- Refresh with: REFRESH MATERIALIZED VIEW mv_student_gpa;

-- ─── MATERIALIZED VIEW 2: Department Rankings ────────────────
CREATE MATERIALIZED VIEW mv_department_stats AS
SELECT
    d.dept_name,
    d.dept_code,
    COUNT(DISTINCT s.student_id)         AS total_students,
    ROUND(AVG(g.g3), 2)                  AS avg_grade,
    ROUND(AVG(g.exam_score), 2)          AS avg_exam_score,
    ROUND(AVG(a.attendance_pct), 2)      AS avg_attendance,
    SUM(CASE WHEN a.at_risk THEN 1 ELSE 0 END) AS at_risk_count
FROM departments d
JOIN students    s ON d.dept_id       = s.dept_id
JOIN enrollment  e ON s.student_id    = e.student_id
JOIN grades      g ON e.enrollment_id = g.enrollment_id
JOIN attendance  a ON e.enrollment_id = a.enrollment_id
GROUP BY d.dept_name, d.dept_code;

-- ─── WINDOW FUNCTION QUERIES ──────────────────────────────────

-- Query 1: Rank students within each department
-- (Run this to show RANK() window function in your demo)
CREATE OR REPLACE VIEW v_student_dept_rank AS
SELECT
    student_name,
    dept_name,
    semester,
    avg_grade,
    RANK() OVER (PARTITION BY dept_name, semester ORDER BY avg_grade DESC) AS dept_rank,
    ROUND(AVG(avg_grade) OVER (PARTITION BY dept_name, semester), 2)       AS dept_avg
FROM mv_student_gpa;

-- Query 2: Semester-on-semester grade trend using LAG()
-- (Shows if a student is improving or declining)
CREATE OR REPLACE VIEW v_grade_trend AS
SELECT
    student_id,
    student_name,
    dept_name,
    semester,
    avg_grade,
    LAG(avg_grade) OVER (PARTITION BY student_id ORDER BY semester) AS prev_semester_grade,
    ROUND(avg_grade - LAG(avg_grade) OVER (PARTITION BY student_id ORDER BY semester), 2) AS grade_change
FROM mv_student_gpa;

-- Query 3: Cumulative average over semesters
CREATE OR REPLACE VIEW v_cumulative_gpa AS
SELECT
    student_id,
    student_name,
    dept_name,
    semester,
    avg_grade,
    ROUND(AVG(avg_grade) OVER (
        PARTITION BY student_id
        ORDER BY semester
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS cumulative_gpa
FROM mv_student_gpa
ORDER BY student_id, semester;
