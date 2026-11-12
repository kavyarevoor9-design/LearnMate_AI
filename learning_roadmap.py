"""
Learning Roadmap Agent — generates adaptive roadmaps via IBM Granite.
"""
import json
import streamlit as st
import granite_client as gc


def _build_roadmap_prompt(student_profile: dict, assessment: dict, courses: list) -> str:
    return f"""You are an expert educational AI assistant powered by IBM Granite.

Create a personalised, adaptive learning roadmap for this student.

Student Profile:
- Name: {student_profile.get('name', 'Student')}
- Goal: {student_profile.get('goal')}
- Domain: {student_profile.get('domain')}
- Current Level: {assessment.get('recommended_level', 'Intermediate')}
- Skill Gaps: {', '.join(assessment.get('gaps', []))}
- Strengths: {', '.join(assessment.get('strengths', []))}
- Weekly Study Hours Available: {student_profile.get('hours', 5)} hours
- Preferred Learning Style: {student_profile.get('learning_style', 'Mixed')}

Top Recommended Courses: {', '.join([c.get('title','') for c in (courses or [])[:4]])}

Generate a detailed, week-by-week roadmap in this JSON format:
{{
  "title": "Personalised Roadmap Title",
  "duration_weeks": <integer>,
  "goal_statement": "One sentence describing what the student will achieve",
  "phases": [
    {{
      "phase": 1,
      "title": "Phase Name",
      "weeks": "1-4",
      "focus": "What this phase focuses on",
      "topics": ["Topic 1", "Topic 2", "Topic 3"],
      "milestones": ["What the student can do by end of phase"],
      "resources": ["Specific resource or activity"]
    }}
  ],
  "weekly_schedule": {{
    "monday": "Activity",
    "tuesday": "Activity",
    "wednesday": "Activity",
    "thursday": "Activity",
    "friday": "Activity",
    "weekend": "Activity"
  }},
  "success_metrics": ["Metric 1", "Metric 2", "Metric 3"]
}}

Return ONLY valid JSON. No additional text."""


def render_learning_roadmap(student_profile: dict, assessment: dict, courses: list) -> dict | None:
    """Render the learning roadmap UI and return the roadmap dict."""
    st.markdown("## 🗺️ Adaptive Learning Roadmap")
    st.markdown(
        "IBM Granite builds a week-by-week plan tailored to your goals, "
        "current skills, and available study time."
    )

    if not assessment:
        st.info("Complete the Skill Assessment first to generate your personalised roadmap.")
        return None

    cached = st.session_state.get("roadmap")
    if not cached:
        with st.spinner("IBM Granite is crafting your learning roadmap…"):
            prompt = _build_roadmap_prompt(student_profile, assessment, courses)
            try:
                raw = gc.generate(prompt, max_new_tokens=1500)
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                cached = json.loads(raw.strip())
                st.session_state["roadmap"] = cached
            except Exception as exc:
                st.error(f"Roadmap generation error: {exc}")
                return None

    if not cached:
        return None

    # ---- Hero banner ----
    st.markdown(
        f"""<div style='background:linear-gradient(135deg,#1e3a5f,#2563eb);
        border-radius:12px;padding:24px;color:white;margin-bottom:20px'>
        <h2 style='margin:0;color:white'>🎯 {cached.get('title','Your Roadmap')}</h2>
        <p style='margin:8px 0 0;opacity:0.9'>{cached.get('goal_statement','')}</p>
        <p style='margin:6px 0 0;opacity:0.7'>⏱ {cached.get('duration_weeks',12)} weeks total</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ---- Phases ----
    st.markdown("### 📅 Learning Phases")
    phases = cached.get("phases", [])
    phase_colours = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"]

    for idx, phase in enumerate(phases):
        colour = phase_colours[idx % len(phase_colours)]
        with st.expander(
            f"Phase {phase.get('phase','')}: {phase.get('title','')}  |  Weeks {phase.get('weeks','')}",
            expanded=(idx == 0),
        ):
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(f"**Focus:** {phase.get('focus','')}")
                st.markdown("**Topics:**")
                for topic in phase.get("topics", []):
                    st.markdown(f"  - {topic}")
                st.markdown("**Milestones:**")
                for ms in phase.get("milestones", []):
                    st.markdown(f"  ✅ {ms}")
            with col_b:
                st.markdown("**Resources & Activities:**")
                for res in phase.get("resources", []):
                    st.markdown(f"  📌 {res}")
                # Progress bar placeholder (driven by progress tracker)
                prog_key = f"phase_{phase.get('phase', idx)}_progress"
                prog = st.session_state.get(prog_key, 0)
                st.markdown(f"**Your Progress:** {prog}%")
                st.progress(prog / 100)

    # ---- Weekly schedule ----
    schedule = cached.get("weekly_schedule", {})
    if schedule:
        st.markdown("### 📆 Suggested Weekly Schedule")
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "weekend"]
        day_labels = {"monday":"Mon","tuesday":"Tue","wednesday":"Wed","thursday":"Thu","friday":"Fri","weekend":"Wknd"}
        cols = st.columns(len(days))
        for col, day in zip(cols, days):
            with col:
                st.markdown(
                    f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;"
                    f"padding:10px;text-align:center'><b style='color:#3b82f6'>{day_labels[day]}</b>"
                    f"<br><span style='font-size:0.8rem;color:#374151'>{schedule.get(day,'Rest')}</span></div>",
                    unsafe_allow_html=True,
                )

    # ---- Success metrics ----
    metrics = cached.get("success_metrics", [])
    if metrics:
        st.markdown("### 🏆 Success Metrics")
        cols = st.columns(min(len(metrics), 3))
        for col, metric in zip(cols, metrics):
            with col:
                st.markdown(
                    f"<div style='background:#f0fdf4;border-left:4px solid #22c55e;"
                    f"padding:12px;border-radius:4px;font-size:0.9rem'>{metric}</div>",
                    unsafe_allow_html=True,
                )

    if st.button("🔄 Regenerate Roadmap", use_container_width=True):
        st.session_state.pop("roadmap", None)
        st.rerun()

    return cached
