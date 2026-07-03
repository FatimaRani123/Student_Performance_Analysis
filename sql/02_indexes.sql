-- ============================================================
--  INDEXES — Run EXPLAIN ANALYZE before AND after these
--  to show performance improvement (screenshots for report!)
-- ============================================================

-- Composite index: fastest for "find all grades for student X in semester Y"
CREATE INDEX idx_enrollment_student_semester
    ON enrollment (student_id, semester, academic_year);

-- Index on grades for fast GPA calculation queries
CREATE INDEX idx_grades_enrollment
    ON grades (enrollment_id, g3);

-- Index for attendance lookups
CREATE INDEX idx_attendance_risk
    ON attendance (at_risk, attendance_pct);

-- Index for student department lookups (used in ranking queries)
CREATE INDEX idx_students_dept
    ON students (dept_id, student_id);
