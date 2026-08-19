import os
import tempfile
import streamlit as st
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Internal core modules
from auth_view import init_auth_session, render_auth_view, render_user_sidebar
from database import save_scan_record, get_user_scan_history
from resume_parser import ResumeParser
from ats_engine import ATSEngine

# Page Configuration
st.set_page_config(
    page_title="AI Placement Co-Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Pill Badges and Metric Cards
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #334155;
    }
    .skill-badge-matched {
        display: inline-block;
        background-color: #065f46;
        color: #d1fae5;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        border: 1px solid #059669;
    }
    .skill-badge-missing {
        display: inline-block;
        background-color: #7f1d1d;
        color: #fee2e2;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        border: 1px solid #dc2626;
    }
</style>
""", unsafe_allow_html=True)


def render_circular_gauge(score: float, title: str = "ATS Match Score"):
    """Renders an interactive circular gauge chart for match scoring."""
    color = "#10b981" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 20, "color": "#f8fafc"}},
        number={"suffix": "%", "font": {"size": 36, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
            "bar": {"color": color},
            "bgcolor": "#1e293b",
            "borderwidth": 2,
            "bordercolor": "#334155",
            "steps": [
                {"range": [0, 50], "color": "rgba(239, 68, 68, 0.15)"},
                {"range": [50, 75], "color": "rgba(245, 158, 11, 0.15)"},
                {"range": [75, 100], "color": "rgba(16, 185, 129, 0.15)"}
            ],
        }
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc"}
    )
    return fig


def render_ats_scanner_tab():
    """Renders Tab 1: Drag-and-Drop ATS Scanner, Analytics & Skill Badges."""
    st.subheader("📊 ATS Match Analytics & Skill Diagnosis")
    st.caption("Upload your resume and provide a target job description to generate hybrid match scoring.")

    col_upload, col_jd = st.columns([1, 1], gap="large")

    with col_upload:
        st.markdown("#### 📄 Upload Resume")
        uploaded_file = st.file_uploader(
            "Drop your PDF resume here",
            type=["pdf"],
            help="Upload your PDF resume to extract skills and experience text."
        )

    with col_jd:
        st.markdown("#### 💼 Target Job Details")
        target_role = st.text_input("Target Job Title", value="Python AI Engineer")
        job_description = st.text_area(
            "Paste Job Description / Requirements",
            height=160,
            placeholder="Paste technical requirements, qualifications, and role responsibilities here..."
        )

    if st.button("🚀 Analyze ATS Match Score", type="primary", use_container_width=True):
        if not uploaded_file or not job_description.strip():
            st.warning("⚠️ Please provide both a PDF resume and a target job description.")
            return

        with st.spinner("Parsing resume, calculating semantic embeddings & keyword overlaps..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                # 1. Parse Resume
                parser = ResumeParser()
                parsed_resume = parser.parse(tmp_path)
                resume_text = parsed_resume["raw_text"]

                # 2. Compute ATS Scorecard
                engine = ATSEngine()
                scorecard = engine.calculate_ats_score(resume_text, job_description)

                # 3. Log to SQLite Scans History
                if st.session_state.get("user_id"):
                    save_scan_record(
                        user_id=st.session_state["user_id"],
                        target_role=target_role,
                        overall_score=scorecard["overall_ats_score"],
                        cosine_sim=scorecard["cosine_similarity"],
                        jaccard_sim=scorecard["jaccard_keyword_match"],
                        matched_count=len(scorecard["matched_skills"]),
                        missing_count=len(scorecard["missing_skills"])
                    )

                # Persist scan in session memory for cross-tab sharing
                st.session_state["last_scan"] = {
                    "target_role": target_role,
                    "parsed_resume": parsed_resume,
                    "scorecard": scorecard
                }

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        st.success("✅ Analysis Complete!")

    # Display Visual Match Analytics
    if "last_scan" in st.session_state:
        scan = st.session_state["last_scan"]
        score = scan["scorecard"]

        st.divider()
        st.markdown(f"### 🎯 Results for **{scan['target_role']}**")

        col_gauge, col_metrics = st.columns([1, 1.2], gap="large")

        with col_gauge:
            st.plotly_chart(
                render_circular_gauge(score["overall_ats_score"]),
                use_container_width=True
            )

        with col_metrics:
            st.markdown("#### Score Composition")
            st.markdown(f"**Candidate Fit Level:** `{score['fit_level']}`")
            m1, m2 = st.columns(2)
            m1.metric("Dense Semantic Match", f"{score['cosine_similarity']}%")
            m2.metric("Sparse Keyword Match", f"{score['jaccard_keyword_match']}%")

            st.markdown("#### Skill Count Diagnostic")
            c1, c2 = st.columns(2)
            c1.metric("Matched Skills", len(score["matched_skills"]))
            c2.metric("Missing Skill Gaps", len(score["missing_skills"]))

        # Skill Pill Badges
        c_left, c_right = st.columns(2, gap="medium")

        with c_left:
            st.markdown(f"#### ✅ Matched Skills ({len(score['matched_skills'])})")
            if score["matched_skills"]:
                pills = "".join([f'<span class="skill-badge-matched">✓ {s}</span>' for s in score["matched_skills"]])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.info("No direct skill matches found.")

        with c_right:
            st.markdown(f"#### ⚠️ Missing Critical Skills ({len(score['missing_skills'])})")
            if score["missing_skills"]:
                pills = "".join([f'<span class="skill-badge-missing">✗ {s}</span>' for s in score["missing_skills"]])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.success("No critical skill gaps identified!")


def main():
    init_auth_session()

    # Route to Auth Page if not authenticated
    if not st.session_state.get("authenticated", False):
        render_auth_view()
        return

    # Render Sidebar with User Profile & Past Scan Records
    render_user_sidebar()
    with st.sidebar:
        st.divider()
        st.markdown("### 📜 Scan History")
        history = get_user_scan_history(st.session_state["user_id"])
        if history:
            for item in history[:5]:
                st.caption(f"**{item['target_role']}** — `{item['overall_score']}%` ({item['timestamp'][:10]})")
        else:
            st.caption("No previous scans recorded.")

    # Horizontal Option Menu Navigation Shell
    selected_tab = option_menu(
        menu_title=None,
        options=["ATS Scanner", "Resume Optimizer", "Mock Interview"],
        icons=["speedometer2", "file-earmark-text", "mic"],
        orientation="horizontal",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"font-size": "1.05rem"},
            "nav-link": {
                "font-size": "1rem",
                "text-align": "center",
                "margin": "0px 8px",
                "padding": "10px 20px",
                "--hover-color": "#1e293b",
            },
            "nav-link-selected": {"background-color": "#0284c7"},
        }
    )

    # Route to active tab view
    if selected_tab == "ATS Scanner":
        render_ats_scanner_tab()
    elif selected_tab == "Resume Optimizer":
        st.info("🛠️ **Resume Optimizer (Tab 2)** will be integrated in Day 12.")
    elif selected_tab == "Mock Interview":
        st.info("🎙️ **Targeted Mock Interview (Tab 3)** will be integrated in Day 13.")


if __name__ == "__main__":
    main()
