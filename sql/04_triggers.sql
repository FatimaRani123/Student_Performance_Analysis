-- ============================================================
--  TRIGGERS & STORED PROCEDURES
-- ============================================================

-- ─── TRIGGER: Auto-flag at-risk students in a log table ──────
CREATE TABLE IF NOT EXISTS at_risk_log (
    log_id          SERIAL PRIMARY KEY,
    student_id      INT,
    student_name    VARCHAR(100),
    attendance_pct  NUMERIC(5,2),
    flagged_at      TIMESTAMP DEFAULT NOW(),
    action_taken    VARCHAR(200) DEFAULT 'Email alert sent to advisor'
);

CREATE OR REPLACE FUNCTION fn_flag_at_risk()
RETURNS TRIGGER AS $$
DECLARE
    v_student_name VARCHAR(100);
    v_student_id   INT;
BEGIN
    -- Only act when student drops below 75% attendance
    IF NEW.attendance_pct < 75 AND (OLD.attendance_pct IS NULL OR OLD.attendance_pct >= 75) THEN
        -- Get the student details
        SELECT s.student_id, s.first_name || ' ' || s.last_name
        INTO v_student_id, v_student_name
        FROM students s
        JOIN enrollment e ON s.student_id = e.student_id
        WHERE e.enrollment_id = NEW.enrollment_id;

        INSERT INTO at_risk_log (student_id, student_name, attendance_pct)
        VALUES (v_student_id, v_student_name, NEW.attendance_pct);

        RAISE NOTICE 'AT-RISK FLAG: Student % attendance dropped to %',
            v_student_name, NEW.attendance_pct;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_attendance_risk
AFTER INSERT OR UPDATE ON attendance
FOR EACH ROW EXECUTE FUNCTION fn_flag_at_risk();

-- ─── STORED PROCEDURE: Calculate CGPA for any student ────────
CREATE OR REPLACE FUNCTION fn_get_cgpa(p_student_id INT)
RETURNS TABLE (
    student_name    TEXT,
    dept_name       TEXT,
    semester        INT,
    semester_gpa    NUMERIC,
    cumulative_gpa  NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (s.first_name || ' ' || s.last_name)::TEXT,
        d.dept_name::TEXT,
        e.semester,
        ROUND(AVG(g.g3), 2)::NUMERIC,
        ROUND(AVG(AVG(g.g3)) OVER (
            PARTITION BY s.student_id
            ORDER BY e.semester
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2)::NUMERIC
    FROM students s
    JOIN departments d      ON s.dept_id       = d.dept_id
    JOIN enrollment  e      ON s.student_id    = e.student_id
    JOIN grades      g      ON e.enrollment_id = g.enrollment_id
    WHERE s.student_id = p_student_id
    GROUP BY s.student_id, s.first_name, s.last_name, d.dept_name, e.semester
    ORDER BY e.semester;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT * FROM fn_get_cgpa(1);

-- ─── STORED PROCEDURE: Top N students per department ─────────
CREATE OR REPLACE FUNCTION fn_top_students(p_dept_code VARCHAR, p_limit INT DEFAULT 10)
RETURNS TABLE (
    rank            BIGINT,
    student_name    TEXT,
    dept_name       TEXT,
    avg_grade       NUMERIC,
    avg_attendance  NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ROW_NUMBER() OVER (ORDER BY AVG(g.g3) DESC)::BIGINT,
        (s.first_name || ' ' || s.last_name)::TEXT,
        d.dept_name::TEXT,
        ROUND(AVG(g.g3), 2)::NUMERIC,
        ROUND(AVG(a.attendance_pct), 2)::NUMERIC
    FROM students s
    JOIN departments d      ON s.dept_id       = d.dept_id
    JOIN enrollment  e      ON s.student_id    = e.student_id
    JOIN grades      g      ON e.enrollment_id = g.enrollment_id
    JOIN attendance  a      ON e.enrollment_id = a.enrollment_id
    WHERE d.dept_code = p_dept_code
    GROUP BY s.student_id, s.first_name, s.last_name, d.dept_name
    ORDER BY AVG(g.g3) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT * FROM fn_top_students('CS', 10);
