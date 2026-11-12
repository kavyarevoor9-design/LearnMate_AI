"""
Progress Tracking Agent — tracks learning progress and generates AI insights.
"""
import json
from datetime import datetime, timedelta
import random
import streamlit as st
import granite_client as gc


def _get_or_init_progress() -> dict:
    """Return existing progress store or create a fresh one."""
    if "progress_data" not in st.session_state:
        st.session_state["progress_data"] = {
            "sessions": [],
            "completed_topics": [],
            "quiz_scores": {},
            "streak_days": 0,
            "total_hours": 0.0,
            "last_activity": None,
            "phase_progress": {},
        }
    return st.session_state["progress_data"]


def _build_insights_prompt(
    student_profile: dict,
    progress: dict,
    assessment: dict,
    roadmap: dict | None,
) -> str:
    return f"""You are an expert AI learning coach powered by IBM Granite.

Analyse this student's learning progress and provide actionable insights and encouragement.

Student: {student_profile.get('name', 'Student')}
Goal: {student_profile.get('goal', 'Not specified')}
Skill Level: {assessment.get('recommended_level', 'Intermediate')}

Progress Data:
- Total Study Hours: {progress.get('total_hours', 0):.1f} hours
- Study Streak: {progress.get('streak_days', 0)} days
- Completed Topics: {', '.join(progress.get('completed_topics', [])) or 'None yet'}
- Quiz Scores: {json.dumps(progress.get('quiz_scores', {}))}
- Sessions this week: {len([s for s in progress.get('sessions', []) if s.get('week') == _current_week()])}

Current Skill Gaps: {', '.join(assessment.get('gaps', []))}
Roadmap phases: {len(roadmap.get('phases', [])) if roadmap else 0}

Provide a concise, motivating progress report with:
1. A positive observation about their progress
2. The most important thing to focus on next
3. A specific study tip for this week
4. An estimated time to goal completion

Keep it conversational, encouraging, and under 200 words. No JSON — plain text please."""


def _current_week() -> str:
    return datetime.now().strftime("%Y-W%U")


def render_progress_tracker(
    student_profile: dict,
    assessment: dict,
    roadmap: dict | None,
) -> None:
    """Render the full progress tracking dashboard."""
    st.markdown("## 📈 Progress Dashboard")
    progress = _get_or_init_progress()

    # ---- Log a study session ----
    st.markdown("### ➕ Log Today's Study Session")
    with st.form("log_session_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            topic = st.text_input("Topic studied", placeholder="e.g. Neural Networks")
        with col2:
            hours = st.number_input("Hours spent", min_value=0.25, max_value=12.0, value=1.0, step=0.25)
        with col3:
            quiz_score = st.number_input("Quiz / exercise score (%)", min_value=0, max_value=100, value=75, step=5)

        notes = st.text_area("Notes (optional)", placeholder="What did you learn? Any blockers?", height=68)
        submitted = st.form_submit_button("✅ Log Session", use_container_width=True)

        if submitted and topic:
            progress["sessions"].append({
                "date":       datetime.now().isoformat(),
                "week":       _current_week(),
                "topic":      topic,
                "hours":      hours,
                "quiz_score": quiz_score,
                "notes":      notes,
            })
            if topic not in progress["completed_topics"]:
                progress["completed_topics"].append(topic)
            progress["total_hours"]  = round(progress["total_hours"] + hours, 2)
            progress["last_activity"] = datetime.now().isoformat()
            progress["quiz_scores"][topic] = quiz_score

            # Update streak (simplified)
            progress["streak_days"] = progress.get("streak_days", 0) + 1
            st.success(f"Session logged! +{hours}h on **{topic}** 🎉")

    st.markdown("---")

    # ---- KPI metrics ----
    st.markdown("### 📊 Your Stats")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Study Hours", f"{progress['total_hours']:.1f} h")
    with m2:
        st.metric("Topics Completed", len(progress["completed_topics"]))
    with m3:
        st.metric("Day Streak", f"{progress['streak_days']} 🔥")
    with m4:
        avg_score = (
            round(sum(progress["quiz_scores"].values()) / len(progress["quiz_scores"]))
            if progress["quiz_scores"] else 0
        )
        st.metric("Avg Quiz Score", f"{avg_score}%")

    # ---- Phase progress sliders ----
    if roadmap:
        st.markdown("### 🗺️ Roadmap Phase Progress")
        phases = roadmap.get("phases", [])
        if phases:
            cols = st.columns(len(phases))
            for col, phase in zip(cols, phases):
                with col:
                    key = f"phase_{phase.get('phase', 0)}_progress"
                    val = st.slider(
                        label=f"P{phase.get('phase','?')}: {phase.get('title','')}",
                        min_value=0, max_value=100,
                        value=st.session_state.get(key, 0),
                        step=5, key=key,
                    )
            # Overall progress
            all_keys = [f"phase_{p.get('phase', i)}_progress" for i, p in enumerate(phases)]
            overall = round(sum(st.session_state.get(k, 0) for k in all_keys) / len(all_keys))
            st.markdown(f"**Overall Roadmap Progress: {overall}%**")
            st.progress(overall / 100)

    # ---- Recent sessions table ----
    sessions = progress.get("sessions", [])
    if sessions:
        st.markdown("### 🗒️ Recent Study Sessions")
        import pandas as pd
        df = pd.DataFrame(sessions[-10:][::-1])[["date", "topic", "hours", "quiz_score", "notes"]]
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%b %d, %Y %H:%M")
        df.columns = ["Date", "Topic", "Hours", "Quiz %", "Notes"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Study hours chart
        st.markdown("### 📉 Hours by Topic")
        hours_by_topic: dict = {}
        for s in sessions:
            hours_by_topic[s["topic"]] = hours_by_topic.get(s["topic"], 0) + s["hours"]
        import pandas as pd
        chart_df = pd.DataFrame({"Topic": list(hours_by_topic.keys()), "Hours": list(hours_by_topic.values())})
        st.bar_chart(chart_df.set_index("Topic"))

    # ---- AI Insights ----
    st.markdown("### 🤖 AI Coach Insights")
    if st.button("💡 Get IBM Granite Insights", type="primary", use_container_width=True):
        with st.spinner("IBM Granite is analysing your progress…"):
            prompt = _build_insights_prompt(student_profile, progress, assessment, roadmap)
            try:
                insight = gc.generate(prompt, max_new_tokens=400)
                st.session_state["last_insight"] = insight
            except Exception as exc:
                st.error(f"Insights error: {exc}")

    insight = st.session_state.get("last_insight")
    if insight:
        st.markdown(
            f"<div style='background:#eff6ff;border-left:4px solid #3b82f6;"
            f"padding:16px;border-radius:6px;line-height:1.7'>{insight}</div>",
            unsafe_allow_html=True,
        )

    # ---- Quiz stub ----
    st.markdown("---")
    st.markdown("### 🧪 Quick Knowledge Check")
    _render_quick_quiz(assessment)


def _render_quick_quiz(assessment: dict) -> None:
    """Very lightweight quiz to keep the student engaged."""
    QUIZZES = {
        "Python": [
            ("What does `len([1,2,3])` return?", ["2", "3", "4", "Error"], "3"),
            ("Which keyword defines a function in Python?", ["func", "def", "define", "function"], "def"),
        ],
        "Machine Learning": [
            ("Which algorithm is used for classification AND regression?", ["K-Means", "SVM", "DBSCAN", "Apriori"], "SVM"),
            ("What does 'overfitting' mean?", ["Model too simple", "Model memorises training data", "Low bias", "High noise"], "Model memorises training data"),
        ],
        "SQL": [
            ("Which SQL clause filters rows?", ["GROUP BY", "ORDER BY", "WHERE", "SELECT"], "WHERE"),
            ("What does JOIN do?", ["Splits table", "Combines tables", "Deletes rows", "Creates index"], "Combines tables"),
        ],
    }
    strengths = assessment.get("strengths", ["Python"])
    topic = strengths[0].split()[0] if strengths else "Python"
    questions = QUIZZES.get(topic, QUIZZES["Python"])

    q = questions[len(st.session_state.get("quiz_history", [])) % len(questions)]
    question, options, answer = q

    with st.form("quick_quiz"):
        st.markdown(f"**{question}**")
        choice = st.radio("Your answer:", options, key="quiz_choice")
        submitted = st.form_submit_button("Submit Answer")
        if submitted:
            history = st.session_state.get("quiz_history", [])
            if choice == answer:
                st.success("✅ Correct! Well done.")
                history.append(1)
            else:
                st.error(f"❌ Incorrect. The correct answer is **{answer}**.")
                history.append(0)
            st.session_state["quiz_history"] = history
            acc = round(100 * sum(history) / len(history))
            st.markdown(f"Quiz accuracy so far: **{acc}%** ({sum(history)}/{len(history)} correct)")
