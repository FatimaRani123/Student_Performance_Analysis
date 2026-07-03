"""
dashboard.py — Enhanced Student Performance Analysis Dashboard
Run: streamlit run app/dashboard.py
"""



import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Analysis",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
/* Hide default streamlit header/footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #0f172a;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] * {
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important;
    padding: 6px 0 !important;
}

/* Main background */
.stApp { background: #0f172a; }

/* KPI card */
.kpi-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}
.kpi-label {
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 32px;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
}
.kpi-value.green { color: #34d399; }
.kpi-value.amber { color: #fbbf24; }
.kpi-value.red   { color: #f87171; }
.kpi-value.blue  { color: #60a5fa; }
.kpi-sub {
    font-size: 11px;
    color: #475569;
    margin-top: 4px;
}

/* Section header */
.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e293b;
}

/* Info box */
.info-box {
    background: #1e293b;
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 16px;
}

/* Risk badge */
.badge-risk {
    background: #450a0a;
    color: #fca5a5;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
.badge-safe {
    background: #052e16;
    color: #86efac;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}

/* Page title */
.page-title {
    font-size: 24px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.page-subtitle {
    font-size: 13px;
    color: #475569;
    margin-bottom: 24px;
}

/* Plotly chart bg */
.js-plotly-plot { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── PLOTLY DARK THEME ────────────────────────────────────────
CHART_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#1e293b",
    plot_bgcolor="#1e293b",
    font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=16, r=16, t=36, b=16),
)

# ─── DB CONNECTION ────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host="localhost", port=5432,
        database="student_performance",
        user="postgres",
        password="admin1234"    # ← change this
    )

@st.cache_data(ttl=60)
def query(sql, params=None):
    try:
        conn = get_conn()
        return pd.read_sql(sql, conn, params=params)
    except Exception:
        # Reset broken connection and retry once
        get_conn.clear()
        conn = get_conn()
        conn.rollback()
        return pd.read_sql(sql, conn, params=params)

# ─── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 20px 0;'>
        <div style='font-size:20px; font-weight:700; color:#f1f5f9;'>🎓 ADBMS</div>
        <div style='font-size:11px; color:#475569; margin-top:2px;'>Student Performance Analysis</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("", [
        "📊  Overview",
        "🏆  Rankings",
        "📈  Grade Trends",
        "⚠️  At-Risk Students",
        "🔍  Student Lookup",
        "⚡  Query Benchmarks",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("<div style='font-size:11px;color:#334155;'>PostgreSQL 18 · Partitioned</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════
if page == "📊  Overview":
    st.markdown('<div class="page-title">Overview Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">All departments · Academic year 2024</div>', unsafe_allow_html=True)

    kpi = query("""
        SELECT
            COUNT(DISTINCT student_id)                                    AS total_students,
            ROUND(AVG(avg_grade), 1)                                      AS overall_avg_grade,
            ROUND(AVG(avg_exam_score), 1)                                 AS overall_avg_exam,
            ROUND(SUM(courses_passed)::numeric / NULLIF(SUM(courses_taken),0) * 100, 1) AS pass_rate
        FROM mv_student_gpa
    """)

    at_risk_count = query("SELECT COUNT(*) AS n FROM attendance WHERE at_risk = TRUE")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Total Students</div>
            <div class="kpi-value blue">{int(kpi['total_students'][0])}</div>
            <div class="kpi-sub">across 4 departments</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        v = float(kpi['overall_avg_grade'][0])
        col = "green" if v >= 14 else "amber" if v >= 10 else "red"
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Avg Grade</div>
            <div class="kpi-value {col}">{v}</div>
            <div class="kpi-sub">out of 20.0</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        pr = float(kpi['pass_rate'][0])
        col = "green" if pr >= 75 else "amber" if pr >= 60 else "red"
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Pass Rate</div>
            <div class="kpi-value {col}">{pr}%</div>
            <div class="kpi-sub">grade ≥ 10</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        n = int(at_risk_count['n'][0])
        col = "red" if n > 50 else "amber" if n > 20 else "green"
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">At-Risk</div>
            <div class="kpi-value {col}">{n}</div>
            <div class="kpi-sub">attendance &lt; 75%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Performance by Department</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        dept = query("SELECT dept_name, dept_code, avg_grade, avg_attendance, total_students FROM mv_department_stats ORDER BY avg_grade DESC")
        fig = go.Figure()
        colors = ['#60a5fa','#34d399','#fbbf24','#f472b6']
        for i, row in dept.iterrows():
            fig.add_trace(go.Bar(
                x=[row['dept_code']], y=[row['avg_grade']],
                name=row['dept_name'],
                marker_color=colors[i % len(colors)],
                text=[f"{row['avg_grade']}"],
                textposition='outside',
                textfont=dict(color='#f1f5f9', size=13)
            ))
        fig.update_layout(**CHART_THEME,
            title=dict(text="Avg Grade by Department", font=dict(color='#f1f5f9', size=14)),
            showlegend=False,
            yaxis=dict(range=[0,22], gridcolor='#1e293b', zerolinecolor='#334155'),
            xaxis=dict(gridcolor='#1e293b'),
            height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        dist = query("""
            SELECT
                CASE
                    WHEN avg_grade >= 18 THEN 'Excellent 18-20'
                    WHEN avg_grade >= 14 THEN 'Good 14-17'
                    WHEN avg_grade >= 10 THEN 'Pass 10-13'
                    ELSE 'Fail < 10'
                END AS grade_band,
                COUNT(*) AS students
            FROM mv_student_gpa
            GROUP BY grade_band ORDER BY MIN(avg_grade) DESC
        """)
        fig = px.pie(dist, names='grade_band', values='students',
                     color_discrete_sequence=['#34d399','#60a5fa','#fbbf24','#f87171'],
                     hole=0.55)
        fig.update_layout(**CHART_THEME,
            title=dict(text="Grade Distribution", font=dict(color='#f1f5f9', size=14)),
            legend=dict(font=dict(color='#94a3b8'), bgcolor='rgba(0,0,0,0)'),
            height=300)
        fig.update_traces(textfont_color='#f1f5f9')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Study Hours vs Exam Score</div>", unsafe_allow_html=True)
    scatter = query("""
        SELECT study_hours, avg_exam_score, motivation_level, dept_name
        FROM mv_student_gpa WHERE study_hours IS NOT NULL
    """)
    fig = px.scatter(scatter, x='study_hours', y='avg_exam_score',
                     color='motivation_level', facet_col='dept_name',
                     labels={'study_hours':'Study Hours/Week','avg_exam_score':'Exam Score'},
                     color_discrete_map={'Low':'#f87171','Medium':'#fbbf24','High':'#34d399'})
    fig.update_layout(**CHART_THEME, height=320,
        title=dict(text="", font=dict(color='#f1f5f9')))
    fig.update_traces(marker=dict(size=7, opacity=0.7))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 2 — RANKINGS
# ══════════════════════════════════════════════════════════════
elif page == "🏆  Rankings":
    st.markdown('<div class="page-title">Department Rankings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">RANK() window function · PostgreSQL</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        depts = query("SELECT dept_code FROM departments ORDER BY dept_code")
        dept_choice = st.selectbox("Department", depts['dept_code'].tolist())
        top_n = st.slider("Top N", 5, 30, 10)

    top = query(f"SELECT * FROM fn_top_students('{dept_choice}', {top_n})")

    st.markdown(f"<div class='section-header'>Top {top_n} Students — {dept_choice}</div>", unsafe_allow_html=True)

    # Styled table with rank medals
    def render_rank(r):
        medals = {1:'🥇', 2:'🥈', 3:'🥉'}
        return medals.get(int(r), str(int(r)))

    top['#'] = top['rank'].apply(render_rank)
    top['attendance'] = top['avg_attendance'].apply(
        lambda x: f"🟢 {x}%" if x >= 75 else f"🔴 {x}%"
    )
    display = top[['#','student_name','dept_name','avg_grade','attendance']].copy()
    display.columns = ['Rank','Student','Department','Avg Grade','Attendance']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Grade comparison — all departments</div>", unsafe_allow_html=True)
    ranks = query("""
        SELECT student_name, dept_name, semester, avg_grade, dept_rank
        FROM v_student_dept_rank
        WHERE dept_rank <= 3
        ORDER BY dept_name, semester, dept_rank
    """)
    fig = px.bar(ranks, x='dept_name', y='avg_grade', color='dept_name',
                 barmode='group',
                 color_discrete_sequence=['#60a5fa','#34d399','#fbbf24','#f472b6'],
                 labels={'avg_grade':'Avg Grade','dept_name':'Department'})
    fig.update_layout(**CHART_THEME, height=320, showlegend=False,
        title=dict(text="Top 3 Students per Department", font=dict(color='#f1f5f9', size=14)))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 3 — GRADE TRENDS
# ══════════════════════════════════════════════════════════════
elif page == "📈  Grade Trends":
    st.markdown('<div class="page-title">Grade Trends</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">LAG() · AVG() OVER() · Window Functions</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-box">Uses SQL <code>LAG()</code> to compare each semester\'s grade against the previous one — a core ADBMS window function.</div>', unsafe_allow_html=True)

    trend = query("""
        SELECT student_name, dept_name, semester,
               avg_grade, prev_semester_grade, grade_change
        FROM v_grade_trend
        WHERE prev_semester_grade IS NOT NULL
        ORDER BY dept_name, semester
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='section-header'>Most improved students</div>", unsafe_allow_html=True)
        improving = trend[trend['grade_change'] > 0].nlargest(8, 'grade_change')[
            ['student_name','dept_name','grade_change']].copy()
        improving['grade_change'] = improving['grade_change'].apply(lambda x: f"▲ +{x:.1f}")
        improving.columns = ['Student','Dept','Change']
        st.dataframe(improving, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("<div class='section-header'>Most declined students</div>", unsafe_allow_html=True)
        declining = trend[trend['grade_change'] < 0].nsmallest(8, 'grade_change')[
            ['student_name','dept_name','grade_change']].copy()
        declining['grade_change'] = declining['grade_change'].apply(lambda x: f"▼ {x:.1f}")
        declining.columns = ['Student','Dept','Change']
        st.dataframe(declining, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Cumulative GPA — top 5 students</div>", unsafe_allow_html=True)
    cgpa = query("""
        SELECT student_name, dept_name, semester, cumulative_gpa
        FROM v_cumulative_gpa
        WHERE student_id IN (
            SELECT student_id FROM mv_student_gpa
            GROUP BY student_id
            ORDER BY MAX(avg_grade) DESC LIMIT 5
        )
        ORDER BY student_name, semester
    """)
    fig = px.line(cgpa, x='semester', y='cumulative_gpa',
                  color='student_name', markers=True,
                  color_discrete_sequence=['#60a5fa','#34d399','#fbbf24','#f472b6','#a78bfa'],
                  labels={'semester':'Semester','cumulative_gpa':'Cumulative GPA','student_name':'Student'})
    fig.update_layout(**CHART_THEME, height=360,
        title=dict(text="Cumulative GPA trend over semesters", font=dict(color='#f1f5f9', size=14)),
        legend=dict(font=dict(color='#94a3b8'), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(tickmode='linear', dtick=1, gridcolor='#334155'),
        yaxis=dict(gridcolor='#334155'))
    fig.update_traces(line=dict(width=2.5), marker=dict(size=8))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 4 — AT-RISK STUDENTS
# ══════════════════════════════════════════════════════════════
elif page == "⚠️  At-Risk Students":
    st.markdown('<div class="page-title">At-Risk Students</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Trigger-based auto-flagging · attendance &lt; 75%</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Students are automatically flagged by a <code>PostgreSQL TRIGGER</code> the moment their attendance drops below 75%.</div>', unsafe_allow_html=True)

    at_risk = query("""
        SELECT
            s.student_id,
            s.first_name || ' ' || s.last_name  AS student_name,
            d.dept_name,
            a.attendance_pct,
            a.classes_attended,
            a.total_classes
        FROM attendance a
        JOIN enrollment e  ON a.enrollment_id = e.enrollment_id
        JOIN students s    ON e.student_id    = s.student_id
        JOIN departments d ON s.dept_id       = d.dept_id
        WHERE a.at_risk = TRUE
        ORDER BY a.attendance_pct ASC
        LIMIT 100
    """)

    total_students = query("SELECT COUNT(DISTINCT student_id) AS n FROM students")
    pct = round(len(at_risk) / int(total_students['n'][0]) * 100, 1)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">At-Risk Count</div>
            <div class="kpi-value red">{len(at_risk)}</div>
            <div class="kpi-sub">{pct}% of all students</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        avg_att = round(float(at_risk['attendance_pct'].mean()), 1) if not at_risk.empty else 0
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Avg Attendance</div>
            <div class="kpi-value amber">{avg_att}%</div>
            <div class="kpi-sub">among at-risk students</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        lowest = round(float(at_risk['attendance_pct'].min()), 1) if not at_risk.empty else 0
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Lowest Attendance</div>
            <div class="kpi-value red">{lowest}%</div>
            <div class="kpi-sub">worst case</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>At-risk student list</div>", unsafe_allow_html=True)
    if not at_risk.empty:
        at_risk['status'] = at_risk['attendance_pct'].apply(
            lambda x: '🔴 Critical' if x < 60 else '🟡 Warning'
        )
        display = at_risk[['student_id','student_name','dept_name','attendance_pct','status']].copy()
        display.columns = ['ID','Student','Department','Attendance %','Status']
        st.dataframe(display, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='section-header'>Trigger log</div>", unsafe_allow_html=True)
        log = query("SELECT student_name, attendance_pct, flagged_at FROM at_risk_log ORDER BY flagged_at DESC LIMIT 15")
        if log.empty:
            st.info("No trigger events logged yet.")
        else:
            st.dataframe(log, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("<div class='section-header'>Attendance distribution</div>", unsafe_allow_html=True)
        att_dist = query("""
            SELECT ROUND(attendance_pct / 5) * 5 AS bucket, COUNT(*) AS count
            FROM attendance GROUP BY bucket ORDER BY bucket
        """)
        att_dist['color'] = att_dist['bucket'].apply(
            lambda x: '#f87171' if x < 75 else '#34d399'
        )
        fig = go.Figure(go.Bar(
            x=att_dist['bucket'], y=att_dist['count'],
            marker_color=att_dist['color'],
            text=att_dist['count'], textposition='outside',
            textfont=dict(color='#f1f5f9')
        ))
        fig.update_layout(**CHART_THEME, height=280,
            xaxis_title="Attendance %", yaxis_title="Students",
            xaxis=dict(gridcolor='#334155'), yaxis=dict(gridcolor='#334155'))
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 5 — STUDENT LOOKUP
# ══════════════════════════════════════════════════════════════
elif page == "🔍  Student Lookup":
    st.markdown('<div class="page-title">Student Lookup</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Calls fn_get_cgpa() stored procedure · PostgreSQL</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        student_id = st.number_input("Student ID", min_value=1, step=1, value=1)
        search = st.button("🔍  Search", use_container_width=True)

    if search:
        result = query(f"SELECT * FROM fn_get_cgpa({int(student_id)})")
        if result.empty:
            st.error("Student not found.")
        else:
            name = result['student_name'].iloc[0]
            dept = result['dept_name'].iloc[0]
            final_cgpa = float(result['cumulative_gpa'].iloc[-1])
            color = "green" if final_cgpa >= 14 else "amber" if final_cgpa >= 10 else "red"

            st.markdown("<div class='section-header'>Student profile</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""<div class="kpi-card">
                    <div class="kpi-label">Name</div>
                    <div class="kpi-value blue" style="font-size:18px">{name}</div>
                    <div class="kpi-sub">ID: {student_id}</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="kpi-card">
                    <div class="kpi-label">Department</div>
                    <div class="kpi-value blue" style="font-size:18px">{dept}</div>
                    <div class="kpi-sub">enrolled</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class="kpi-card">
                    <div class="kpi-label">Final CGPA</div>
                    <div class="kpi-value {color}">{final_cgpa}</div>
                    <div class="kpi-sub">cumulative</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>Semester breakdown</div>", unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=result['semester'], y=result['semester_gpa'],
                name='Semester GPA', marker_color='#60a5fa',
                text=result['semester_gpa'], textposition='outside',
                textfont=dict(color='#f1f5f9')
            ))
            fig.add_trace(go.Scatter(
                x=result['semester'], y=result['cumulative_gpa'],
                name='Cumulative GPA', mode='lines+markers',
                line=dict(color='#34d399', width=2.5),
                marker=dict(size=8, color='#34d399')
            ))
            fig.update_layout(**CHART_THEME, height=340,
                xaxis=dict(title='Semester', tickmode='linear', dtick=1, gridcolor='#334155'),
                yaxis=dict(title='GPA', range=[0,22], gridcolor='#334155'),
                legend=dict(font=dict(color='#94a3b8'), bgcolor='rgba(0,0,0,0)'))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<div class='section-header'>Raw data</div>", unsafe_allow_html=True)
            st.dataframe(result, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
#  PAGE 6 — QUERY BENCHMARKS
# ══════════════════════════════════════════════════════════════
elif page == "⚡  Query Benchmarks":
    st.markdown('<div class="page-title">Query Benchmarks</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">EXPLAIN ANALYZE · Index performance · Partition pruning</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Copy these queries into pgAdmin Query Tool and take screenshots before and after creating indexes. This is one of the strongest sections of your ADBMS report.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Before Index", "After Index", "Partition Pruning"])

    with tab1:
        st.markdown("<div class='section-header'>Run this BEFORE creating indexes</div>", unsafe_allow_html=True)
        st.code("""-- Drop indexes first to simulate no-index state
DROP INDEX IF EXISTS idx_enrollment_student_semester;
DROP INDEX IF EXISTS idx_grades_enrollment;

-- Now run EXPLAIN ANALYZE — look for "Seq Scan" and high cost
EXPLAIN ANALYZE
SELECT s.student_id, AVG(g.g3)
FROM students s
JOIN enrollment e ON s.student_id = e.student_id
JOIN grades g     ON e.enrollment_id = g.enrollment_id
GROUP BY s.student_id;

-- Expected output: Seq Scan, cost ~5000ms""", language="sql")

    with tab2:
        st.markdown("<div class='section-header'>Run this AFTER creating indexes</div>", unsafe_allow_html=True)
        st.code("""-- Re-create indexes
CREATE INDEX idx_enrollment_student_semester
    ON enrollment (student_id, semester, academic_year);

CREATE INDEX idx_grades_enrollment
    ON grades (enrollment_id, g3);

-- Same query — now look for "Index Scan" and much lower cost
EXPLAIN ANALYZE
SELECT s.student_id, AVG(g.g3)
FROM students s
JOIN enrollment e ON s.student_id = e.student_id
JOIN grades g     ON e.enrollment_id = g.enrollment_id
GROUP BY s.student_id;

-- Expected: Index Scan, cost drops to ~50ms""", language="sql")

    with tab3:
        st.markdown("<div class='section-header'>Partition pruning demo</div>", unsafe_allow_html=True)
        st.code("""-- PostgreSQL will ONLY scan grades_sem1_2 partition
-- Other 3 partitions are completely skipped
EXPLAIN ANALYZE
SELECT * FROM grades WHERE semester = 1;

-- Look for: "Partitions: grades_sem1_2"
-- This proves range partitioning is working correctly""", language="sql")

    st.markdown("<div class='section-header'>What to include in your report</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""**Screenshot 1**
- EXPLAIN before index
- Shows `Seq Scan`
- High cost number""")
    with col2:
        st.markdown("""**Screenshot 2**
- EXPLAIN after index
- Shows `Index Scan`
- Much lower cost""")
    with col3:
        st.markdown("""**Screenshot 3**
- Partition pruning
- Only 1 of 4 partitions scanned
- Proves partitioning works""")
