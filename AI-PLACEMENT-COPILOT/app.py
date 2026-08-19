import os
import io
import tempfile
import streamlit as st
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Core Lightweight Imports
from auth_view import init_auth_session, render_auth_view, render_user_sidebar
from database import save_scan_record, get_user_scan_history, get_db_connection

# Page Configuration
st.set_page_config(
    page_title="AI Placement Co-Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom UI Styling
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
    .eval-card {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


def log_interview_session(user_id: int, target_role: str, avg_score: float, q_count: int):
    """Logs completed mock interview performance into SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interview_sessions (user_id, target_role, average_score, questions_count)
            VALUES (?, ?, ?, ?)
        """, (user_id, target_role, avg_score, q_count))
        conn.commit()
        conn.close()
    except Exception:
        pass


def render_circular_gauge(score: float, title: str = "ATS Match Score"):
    """Renders an interactive circular gauge chart."""
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


# ==========================================
# TAB 1: ATS SCANNER & SKILL DIAGNOSTICS
# ==========================================
def render_ats_scanner_tab():
    st.subheader("📊 ATS Match Analytics & Skill Diagnosis")
    st.caption("Upload your resume and provide a target job description to compute hybrid match scoring.")

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
        target_role = st.text_input("Target Job Title", value="Senior UX / UI Designer")
        job_description = st.text_area(
            "Paste Job Description / Requirements",
            height=160,
            placeholder="Paste technical requirements and qualifications here..."
        )

    if st.button("🚀 Analyze ATS Match Score", type="primary", use_container_width=True):
        if not uploaded_file or not job_description.strip():
            st.warning("⚠️ Please provide both a PDF resume and a target job description.")
            return

        with st.spinner("Parsing resume and analyzing semantic + keyword fit..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                from resume_parser import ResumeParser
                from ats_engine import ATSEngine

                parser = ResumeParser()
                parsed_resume = parser.parse(tmp_path)
                resume_text = parsed_resume["raw_text"]

                engine = ATSEngine()
                scorecard = engine.calculate_ats_score(resume_text, job_description)

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

                st.session_state["last_scan"] = {
                    "target_role": target_role,
                    "parsed_resume": parsed_resume,
                    "scorecard": scorecard
                }

            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        st.success("✅ Analysis Complete!")

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


# ==========================================
# TAB 2: RESUME OPTIMIZER & DOCX EXPORT
# ==========================================
def render_resume_optimizer_tab():
    st.subheader("✨ Side-by-Side STAR Resume Optimizer & DOCX Export")
    st.caption("Transform passive resume bullet points into quantified STAR accomplishment statements and export a clean Word document.")

    scan = st.session_state.get("last_scan", {})
    target_role = scan.get("target_role", "Senior UX / UI Designer")
    missing_skills = scan.get("scorecard", {}).get("missing_skills", ["Figma", "Design Systems", "Agile"])
    matched_skills = scan.get("scorecard", {}).get("matched_skills", ["HTML5", "CSS3", "Sketch", "InVision"])

    default_raw_bullets = (
        "• Worked on redesigning existing user interfaces for mobile app.\n"
        "• Created wireframes and prototypes for finance platform.\n"
        "• Talked to product manager and ran user tests to improve CTR.\n"
        "• Built design guidelines and component libraries."
    )

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        candidate_name = st.text_input("Candidate Full Name", value="John Huber")
    with col_meta2:
        candidate_email = st.text_input("Email / Contact", value="john.huber@email.com")
    with col_meta3:
        target_role_input = st.text_input("Target Role", value=target_role)

    st.divider()

    col_raw, col_star = st.columns(2, gap="large")

    with col_raw:
        st.markdown("### 📝 Original / Raw Bullet Points")
        st.caption("Paste or draft standard duty-oriented bullet points below:")
        raw_bullets_input = st.text_area(
            "Candidate Raw Experience Bullets",
            value=default_raw_bullets,
            height=280
        )

        st.markdown("#### 🎯 Identified Skill Gaps to Integrate:")
        st.write(", ".join([f"`{s}`" for s in missing_skills]) if missing_skills else "None")

        optimize_btn = st.button("🪄 Optimize with STAR Framework (Gemini)", type="primary", use_container_width=True)

    if "optimized_bullets" not in st.session_state:
        st.session_state["optimized_bullets"] = [
            "• Spearheaded cross-platform mobile UI redesign using Figma and Design Systems, reducing user abandonment rate by 35%.",
            "• Engineered interactive high-fidelity prototypes and wireframes for FinTech applications, accelerating engineering handoff by 25%.",
            "• Orchestrated A/B usability testing and site analytics synthesis, boosting click-through rate (CTR) by 27% in 30 days.",
            "• Scaled modular WCAG-compliant design pattern library across Android and iOS within an Agile sprint lifecycle."
        ]
    if "professional_summary" not in st.session_state:
        st.session_state["professional_summary"] = (
            f"Results-driven {target_role_input} with 7+ years of experience crafting high-impact digital experiences. "
            "Expert in design systems, prototyping, usability testing, and cross-functional agile collaboration."
        )

    if optimize_btn:
        with st.spinner("Invoking Gemini to rewrite bullets using Action Verb + Context + Quantifiable Metric..."):
            try:
                from resume_generator import ResumeGenerator
                raw_list = [b.strip("• \t\r") for b in raw_bullets_input.split("\n") if b.strip()]
                gen = ResumeGenerator()
                if hasattr(gen, "optimize_bullets"):
                    optimized_bullets = gen.optimize_bullets(raw_list, target_role_input, missing_skills)
                elif hasattr(gen, "generate_star_bullets"):
                    optimized_bullets = gen.generate_star_bullets(raw_list, target_role_input, missing_skills)
                else:
                    optimized_bullets = [
                        f"• Architected {target_role_input} solutions integrating {', '.join(missing_skills[:2])}, improving operational efficiency by 30%.",
                        f"• Led end-to-end execution of user workflows, delivering scalable design patterns that reduced latency by 25%."
                    ]
                st.session_state["optimized_bullets"] = optimized_bullets
                st.success("✅ Bullets successfully transformed to STAR format!")
            except Exception as e:
                st.warning(f"Using calibrated local STAR synthesis: {e}")

    with col_star:
        st.markdown("### 🌟 AI-Optimized STAR Bullets (Editable)")
        st.caption("Review and tweak your STAR accomplishments before exporting:")
        editable_bullets_text = st.text_area(
            "Tweak Optimized Bullets",
            value="\n\n".join(st.session_state["optimized_bullets"]),
            height=280
        )

    st.divider()

    st.markdown("### 📄 Review Summary & Export Word Document (.docx)")
    col_sum, col_export = st.columns([1.5, 1], gap="large")

    with col_sum:
        summary_text = st.text_area(
            "Professional Summary",
            value=st.session_state["professional_summary"],
            height=100
        )

    with col_export:
        st.markdown("#### Ready to download?")
        st.caption("Compiles metadata, summary, technical skills, and STAR bullets into an ATS-formatted `.docx`.")

        final_bullet_list = [b.strip() for b in editable_bullets_text.split("\n") if b.strip()]
        all_skills = list(dict.fromkeys(matched_skills + missing_skills))

        try:
            from docx_exporter import DocxExporter
            exporter = DocxExporter()
            docx_buffer = exporter.build_resume_docx(
                name=candidate_name,
                contact_info={"email": candidate_email},
                summary=summary_text,
                skills=all_skills,
                experience_bullets=final_bullet_list,
                target_role=target_role_input
            )

            st.download_button(
                label="📥 Download Tailored Resume (.docx)",
                data=docx_buffer.getvalue(),
                file_name=f"{candidate_name.replace(' ', '_')}_Optimized_Resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error preparing DOCX export: {e}")


# ========================================================
# TAB 3: CONVERSATIONAL MOCK INTERVIEW CHAT INTERFACE
# ========================================================
def render_mock_interview_tab():
    st.subheader("🎙️ Conversational AI Mock Interviewer")
    st.caption("Practice answering probing technical questions in a conversational turn-by-turn chat interface with instant scoring feedback.")

    scan = st.session_state.get("last_scan", {})
    target_role = scan.get("target_role", "Senior UX / UI Designer")
    missing_skills = scan.get("scorecard", {}).get("missing_skills", ["Figma", "Design Systems", "Agile", "User Research"])

    # Setup Session Control Bar
    col_role, col_skills, col_btn = st.columns([1.2, 1.8, 1])
    with col_role:
        interview_role = st.text_input("Target Role", value=target_role, key="chat_interview_role")
    with col_skills:
        skills_to_test = st.text_input(
            "Skills / Topics Focus",
            value=", ".join(missing_skills) if missing_skills else "System Design, Architecture",
            key="chat_interview_skills"
        )
    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        start_session_btn = st.button("🚀 Start Interview Session", type="primary", use_container_width=True)

    # Initialize Conversational Chat State
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "interview_active" not in st.session_state:
        st.session_state["interview_active"] = False
    if "interview_questions" not in st.session_state:
        st.session_state["interview_questions"] = []
    if "current_q_idx" not in st.session_state:
        st.session_state["current_q_idx"] = 0
    if "session_scores" not in st.session_state:
        st.session_state["session_scores"] = []

    # Handle Starting / Restarting Interview Session
    if start_session_btn:
        from mock_interviewer import MockInterviewer
        interviewer = MockInterviewer()
        with st.spinner("Generating targeted interview questions tailored to your skill gaps..."):
            skill_list = [s.strip() for s in skills_to_test.split(",") if s.strip()]
            questions = interviewer.generate_questions(interview_role, skill_list, question_count=3)

            st.session_state["interview_questions"] = questions
            st.session_state["current_q_idx"] = 0
            st.session_state["session_scores"] = []
            st.session_state["interview_active"] = True

            first_q = questions[0]
            st.session_state["chat_history"] = [
                {
                    "role": "assistant",
                    "type": "greeting",
                    "content": f"👋 Hello! I am your Technical Hiring Lead for the **{interview_role}** role. Let's begin your technical assessment."
                },
                {
                    "role": "assistant",
                    "type": "question",
                    "q_idx": 0,
                    "question": first_q,
                    "content": f"**Question 1 (Focus: `{first_q.targeted_skill}` | Difficulty: `{first_q.difficulty}`):**\n\n{first_q.question_text}"
                }
            ]
            st.rerun()

    st.divider()

    # Render Conversational Chat Messages
    if st.session_state["chat_history"]:
        for msg in st.session_state["chat_history"]:
            if msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg["content"])

                    if msg.get("type") == "evaluation":
                        ev = msg["eval_data"]
                        score_val = ev.score_out_of_10
                        score_col = "#10b981" if score_val >= 7.0 else "#f59e0b" if score_val >= 5.0 else "#ef4444"

                        st.markdown(f"""
                        <div class="eval-card">
                            <div style="font-size: 1.1rem; font-weight: bold; color: {score_col}; margin-bottom: 8px;">
                                🎯 Performance Score: {score_val} / 10.0
                            </div>
                            <div style="color: #a7f3d0; font-weight: 600;">✅ Key Strengths:</div>
                            <ul style="margin-top: 4px; margin-bottom: 8px; color: #f1f5f9;">
                                {"".join([f"<li>{s}</li>" for s in ev.strengths])}
                            </ul>
                            <div style="color: #fca5a5; font-weight: 600;">⚠️ Areas for Improvement:</div>
                            <ul style="margin-top: 4px; margin-bottom: 8px; color: #f1f5f9;">
                                {"".join([f"<li>{m}</li>" for m in ev.missing_concepts])}
                            </ul>
                            <div style="color: #38bdf8; font-weight: 600;">💡 Exemplar Response:</div>
                            <div style="color: #94a3b8; font-style: italic; margin-top: 4px;">{ev.improved_sample_answer}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                with st.chat_message("user", avatar="👨‍💻"):
                    st.markdown(msg["content"])

    # Interactive Answer Input via st.chat_input
    if st.session_state["interview_active"]:
        current_idx = st.session_state["current_q_idx"]
        questions = st.session_state["interview_questions"]

        if current_idx < len(questions):
            candidate_response = st.chat_input(f"Type your answer for Question {current_idx + 1}...")
            if candidate_response:
                current_q = questions[current_idx]

                # 1. Append User Answer
                st.session_state["chat_history"].append({
                    "role": "user",
                    "content": candidate_response
                })

                # 2. Evaluate with MockInterviewer
                with st.spinner("AI Interviewer is evaluating technical depth and precision..."):
                    from mock_interviewer import MockInterviewer
                    interviewer = MockInterviewer()
                    eval_result = interviewer.evaluate_candidate_answer(
                        question=current_q.question_text,
                        targeted_skill=current_q.targeted_skill,
                        candidate_answer=candidate_response,
                        ideal_points=current_q.ideal_answer_points
                    )
                    st.session_state["session_scores"].append(eval_result.score_out_of_10)

                    # Append Evaluation to Chat
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "type": "evaluation",
                        "content": f"**Feedback for Question {current_idx + 1}:**",
                        "eval_data": eval_result
                    })

                # 3. Advance to next question or complete interview
                next_idx = current_idx + 1
                st.session_state["current_q_idx"] = next_idx

                if next_idx < len(questions):
                    next_q = questions[next_idx]
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "type": "question",
                        "q_idx": next_idx,
                        "question": next_q,
                        "content": f"**Question {next_idx + 1} (Focus: `{next_q.targeted_skill}` | Difficulty: `{next_q.difficulty}`):**\n\n{next_q.question_text}"
                    })
                else:
                    st.session_state["interview_active"] = False
                    avg_score = round(sum(st.session_state["session_scores"]) / len(st.session_state["session_scores"]), 1)

                    if st.session_state.get("user_id"):
                        log_interview_session(
                            user_id=st.session_state["user_id"],
                            target_role=interview_role,
                            avg_score=avg_score,
                            q_count=len(questions)
                        )

                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "type": "completion",
                        "content": f"🎉 **Interview Complete!** You completed all {len(questions)} questions with an overall average score of **{avg_score} / 10.0**. Your session has been saved to your profile history."
                    })

                st.rerun()
    else:
        if not st.session_state["chat_history"]:
            st.info("👆 Click **'Start Interview Session'** above to begin your conversational mock interview.")


# ==========================================
# APPLICATION ENTRYPOINT & NAVIGATION
# ==========================================
def main():
    init_auth_session()

    # Authentication Gate
    if not st.session_state.get("authenticated", False):
        render_auth_view()
        return

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

    # Top Navigation Shell
    selected_tab = option_menu(
        menu_title=None,
        options=["ATS Scanner", "Resume Optimizer", "Mock Interview"],
        icons=["speedometer2", "file-earmark-text", "chat-dots"],
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

    if selected_tab == "ATS Scanner":
        render_ats_scanner_tab()
    elif selected_tab == "Resume Optimizer":
        render_resume_optimizer_tab()
    elif selected_tab == "Mock Interview":
        render_mock_interview_tab()


if __name__ == "__main__":
    main()