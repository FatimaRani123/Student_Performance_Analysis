"""
import_data.py
─────────────
Reads your two Kaggle CSVs and loads them into PostgreSQL.

Datasets expected in the /data folder:
  1. student-mat.csv or student-por.csv  (UCI dataset — has g1, g2, g3)
  2. StudentPerformanceFactors.csv        (Kaggle factors dataset)

Run: python scripts/import_data.py
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

# ─── DB CONFIG — change these to match your PostgreSQL setup ──
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "student_performance",   # create this DB in pgAdmin first
    "user":     "postgres",
    "password": "admin1234"     # ← change this
}

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ─── HELPER ──────────────────────────────────────────────────
def connect():
    return psycopg2.connect(**DB_CONFIG)

def clean_num(val, default=0.0):
    try:
        v = float(val)
        return default if np.isnan(v) else v
    except:
        return default

# ─── STEP 1: Load datasets ────────────────────────────────────
def load_csvs():
    # Try both math and portuguese variants of UCI dataset
    uci_path = None
    for name in ['student-mat.csv', 'student-por.csv', 'student_mat.csv']:
        p = os.path.join(DATA_DIR, name)
        if os.path.exists(p):
            uci_path = p
            break

    factors_path = None
    for name in ['StudentPerformanceFactors.csv', 'student_performance_factors.csv']:
        p = os.path.join(DATA_DIR, name)
        if os.path.exists(p):
            factors_path = p
            break

    df_uci     = pd.read_csv(uci_path,     sep=';') if uci_path     else None
    df_factors = pd.read_csv(factors_path)           if factors_path else None

    if df_uci is not None:
        print(f"✓ UCI dataset loaded: {len(df_uci)} rows, columns: {list(df_uci.columns)}")
    else:
        print("⚠ UCI dataset not found — will generate synthetic G1/G2/G3 grades")

    if df_factors is not None:
        print(f"✓ Factors dataset loaded: {len(df_factors)} rows, columns: {list(df_factors.columns)}")
    else:
        print("⚠ Factors dataset not found — will generate synthetic study/sleep hours")

    return df_uci, df_factors

# ─── STEP 2: Insert students ──────────────────────────────────
def insert_students(conn, df_uci, df_factors):
    cur = conn.cursor()

    # Get dept ids
    cur.execute("SELECT dept_id, dept_code FROM departments")
    depts = {code: did for did, code in cur.fetchall()}
    dept_list = list(depts.values())

    students = []
    n = len(df_factors) if df_factors is not None else (len(df_uci) if df_uci is not None else 200)
    n = min(n, 500)  # cap at 500 for manageable demo

    for i in range(n):
        # Gender
        if df_uci is not None and i < len(df_uci):
            gender = 'M' if df_uci.iloc[i].get('sex', 'M') == 'M' else 'F'
            age    = int(clean_num(df_uci.iloc[i].get('age', 18), 18))
            age    = max(15, min(age, 30))
        elif df_factors is not None and i < len(df_factors):
            gender = df_factors.iloc[i].get('Gender', 'M')[0].upper()
            age    = 18
        else:
            gender = 'M' if i % 2 == 0 else 'F'
            age    = 18

        # Study hours, sleep hours, motivation, family support
        if df_factors is not None and i < len(df_factors):
            row = df_factors.iloc[i]
            study_h  = clean_num(row.get('Hours_Studied', 5), 5)
            sleep_h  = clean_num(row.get('Sleep_Hours', 7),   7)
            motiv    = str(row.get('Motivation_Level', 'Medium')).strip().capitalize()
            famsup   = str(row.get('Family_Support', 'Medium')).strip().capitalize()
        else:
            study_h  = round(np.random.uniform(2, 10), 1)
            sleep_h  = round(np.random.uniform(5, 9), 1)
            motiv    = np.random.choice(['Low', 'Medium', 'High'])
            famsup   = np.random.choice(['Low', 'Medium', 'High'])

        if motiv not in ('Low', 'Medium', 'High'):   motiv  = 'Medium'
        if famsup not in ('Low', 'Medium', 'High'):  famsup = 'Medium'

        dept_id  = dept_list[i % len(dept_list)]
        fname    = f"Student{i+1}"
        lname    = f"Last{i % 50 + 1}"

        students.append((fname, lname, gender, age, dept_id,
                         study_h, sleep_h, motiv, famsup))

    execute_values(cur, """
        INSERT INTO students
            (first_name, last_name, gender, age, dept_id,
             study_hours, sleep_hours, motivation_level, family_support)
        VALUES %s
    """, students)

    conn.commit()
    print(f"✓ Inserted {len(students)} students")
    cur.close()
    return n

# ─── STEP 3: Insert courses & enrollment ─────────────────────
def insert_courses_and_enrollment(conn, n_students):
    cur = conn.cursor()

    cur.execute("SELECT dept_id, dept_code FROM departments")
    depts = {code: did for did, code in cur.fetchall()}

    # Insert sample courses
    courses = [
        ('Data Structures',         depts['CS'],   3, 1),
        ('Algorithms',              depts['CS'],   3, 2),
        ('Database Systems',        depts['CS'],   3, 3),
        ('Operating Systems',       depts['CS'],   3, 4),
        ('Calculus I',              depts['MATH'], 3, 1),
        ('Linear Algebra',          depts['MATH'], 3, 2),
        ('Probability & Stats',     depts['MATH'], 3, 3),
        ('Classical Mechanics',     depts['PHY'],  3, 1),
        ('Electromagnetism',        depts['PHY'],  3, 2),
        ('Academic Writing',        depts['ENG'],  3, 1),
        ('Literature Studies',      depts['ENG'],  3, 2),
    ]
    execute_values(cur, """
        INSERT INTO courses (course_name, dept_id, credits, semester) VALUES %s
    """, courses)

    # Enroll each student in courses matching their dept + a couple cross-dept
    cur.execute("SELECT student_id, dept_id FROM students ORDER BY student_id")
    students = cur.fetchall()

    cur.execute("SELECT course_id, dept_id, semester FROM courses")
    all_courses = cur.fetchall()

    enrollments = []
    for sid, dept_id in students:
        dept_courses = [c for c in all_courses if c[1] == dept_id]
        for course_id, _, semester in dept_courses:
            enrollments.append((sid, course_id, 2024, semester))

    execute_values(cur, """
        INSERT INTO enrollment (student_id, course_id, academic_year, semester)
        VALUES %s ON CONFLICT DO NOTHING
    """, enrollments)

    conn.commit()
    print(f"✓ Inserted {len(courses)} courses and {len(enrollments)} enrollments")
    cur.close()

# ─── STEP 4: Insert grades ────────────────────────────────────
def insert_grades(conn, df_uci):
    cur = conn.cursor()

    cur.execute("SELECT enrollment_id, student_id, semester FROM enrollment ORDER BY enrollment_id")
    enrollments = cur.fetchall()

    grades = []
    for idx, (eid, sid, semester) in enumerate(enrollments):
        # Use UCI real grades if available, else generate
        if df_uci is not None and idx < len(df_uci):
            row = df_uci.iloc[idx]
            g1 = clean_num(row.get('G1', 10), 10)
            g2 = clean_num(row.get('G2', 10), 10)
            g3 = clean_num(row.get('G3', 10), 10)
        else:
            g1 = round(np.random.normal(12, 3), 1)
            g2 = round(g1 + np.random.normal(0, 1.5), 1)
            g3 = round(g2 + np.random.normal(0, 1.5), 1)
            g1, g2, g3 = [max(0, min(20, v)) for v in (g1, g2, g3)]

        exam_score = round((g3 / 20) * 100, 1)   # convert to 0-100 scale
        grades.append((eid, g1, g2, g3, exam_score, semester))

    execute_values(cur, """
        INSERT INTO grades (enrollment_id, g1, g2, g3, exam_score, semester)
        VALUES %s
    """, grades)

    conn.commit()
    print(f"✓ Inserted {len(grades)} grade records")
    cur.close()

# ─── STEP 5: Insert attendance ────────────────────────────────
def insert_attendance(conn, df_factors):
    cur = conn.cursor()

    cur.execute("SELECT enrollment_id FROM enrollment ORDER BY enrollment_id")
    enrollments = [r[0] for r in cur.fetchall()]

    attendance = []
    for idx, eid in enumerate(enrollments):
        total = 40
        if df_factors is not None and idx < len(df_factors):
            pct = clean_num(df_factors.iloc[idx].get('Attendance', 80), 80)
            attended = int((pct / 100) * total)
        else:
            attended = int(np.random.randint(20, 41))

        attendance.append((eid, total, attended))

    execute_values(cur, """
        INSERT INTO attendance (enrollment_id, total_classes, classes_attended)
        VALUES %s
    """, attendance)

    conn.commit()
    print(f"✓ Inserted {len(attendance)} attendance records")
    cur.close()

# ─── STEP 6: Refresh materialized views ───────────────────────
def refresh_views(conn):
    cur = conn.cursor()
    cur.execute("REFRESH MATERIALIZED VIEW mv_student_gpa")
    cur.execute("REFRESH MATERIALIZED VIEW mv_department_stats")
    conn.commit()
    print("✓ Materialized views refreshed")
    cur.close()

# ─── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n=== Student Performance — Data Import ===\n")
    df_uci, df_factors = load_csvs()

    conn = connect()
    print("✓ Connected to PostgreSQL\n")

    n = insert_students(conn, df_uci, df_factors)
    insert_courses_and_enrollment(conn, n)
    insert_grades(conn, df_uci)
    insert_attendance(conn, df_factors)
    refresh_views(conn)

    conn.close()
    print("\n✅ All done! Open pgAdmin or run the dashboard next.")
