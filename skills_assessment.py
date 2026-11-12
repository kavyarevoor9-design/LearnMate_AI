"""
Skills Assessment Agent — evaluates student proficiency via IBM Granite.
"""
import json
import streamlit as st
import granite_client as gc


DOMAIN_TOPICS = {
    "Artificial Intelligence & Machine Learning": [
        "Python", "Machine Learning", "Deep Learning", "Statistics",
        "SQL", "Data Visualisation", "NLP", "Computer Vision",
    ],
    "Web Development": [
        "HTML/CSS", "JavaScript", "React", "Node.js",
        "REST APIs", "Databases", "Git", "TypeScript",
    ],
    "Data Science": [
        "Python", "R", "SQL", "Statistics", "Data Wrangling",
        "Visualisation", "Machine Learning", "Big Data",
    ],
    "Cloud Computing": [
        "AWS", "Azure", "GCP", "Docker", "Kubernetes",
        "CI/CD", "Infrastructure as Code", "Serverless",
    ],
    "Cybersecurity": [
        "Network Security", "Cryptography", "Ethical Hacking",
        "SIEM", "Incident Response", "Cloud Security", "Python", "Linux",
    ],
    "Mobile Development": [
        "React Native", "Flutter", "Swift", "Kotlin",
        "REST APIs", "UI/UX", "Firebase", "Git",
    ],
}


def _build_assessment_prompt(student_profile: dict, self_scores: dict) -> str:
    return f"""You are an expert educational AI assistant powered by IBM Granite.

Analyse the following student profile and self-assessment scores to evaluate their current skill levels.

Student Profile:
- Name: {student_profile.get('name', 'Student')}
- Learning Goal: {student_profile.get('goal', 'Not specified')}
- Domain of Interest: {student_profile.get('domain', 'Not specified')}
- Prior Experience: {student_profile.get('experience', 'Not specified')}
- Weekly Study Hours: {student_profile.get('hours', 'Not specified')}

Self-Assessment Scores (0-100):
{json.dumps(self_scores, indent=2)}

Based on this profile, provide a comprehensive skill assessment in the following JSON format:
{{
  "proficiency_scores": {{"skill_name": score_0_to_100, ...}},
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2", "gap3"],
  "recommended_level": "Beginner|Intermediate|Advanced"
}}

Return ONLY the JSON object. No additional text."""


def render_skill_assessment(student_profile: dict) -> dict | None:
    """Render the skill assessment UI and return results dict, or None."""
    st.markdown("## 🧠 Skill Assessment")
    st.markdown(
        "Rate your current proficiency in each topic. IBM Granite will analyse "
        "your responses to build a personalised learning profile."
    )

    domain   = student_profile.get("domain", "Artificial Intelligence & Machine Learning")
    topics   = DOMAIN_TOPICS.get(domain, DOMAIN_TOPICS["Artificial Intelligence & Machine Learning"])
    scores   = {}

    st.markdown("### Self-Assessment (slide each bar)")
    cols = st.columns(2)
    for i, topic in enumerate(topics):
        with cols[i % 2]:
            scores[topic] = st.slider(
                label=topic,
                min_value=0,
                max_value=100,
                value=50,
                step=5,
                key=f"skill_{topic}",
                help="0 = No knowledge  |  100 = Expert",
            )

    st.markdown("---")
    if st.button("🔍 Analyse My Skills with IBM Granite", type="primary", use_container_width=True):
        with st.spinner("IBM Granite is evaluating your skill profile…"):
            prompt = _build_assessment_prompt(student_profile, scores)
            try:
                raw = gc.generate(prompt)
                # Extract JSON even if model wraps it in markdown fences
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                result = json.loads(raw.strip())
                st.session_state["assessment_result"] = result
                st.session_state["self_scores"]       = scores
                return result
            except Exception as exc:
                st.error(f"Assessment error: {exc}")
                return None
    return st.session_state.get("assessment_result")


def render_assessment_results(result: dict) -> None:
    """Render a visual summary of the assessment results."""
    if not result:
        return

    st.markdown("### 📊 Your Skill Profile")

    prof = result.get("proficiency_scores", {})
    if prof:
        import pandas as pd
        df = pd.DataFrame(
            {"Skill": list(prof.keys()), "Proficiency (%)": list(prof.values())}
        ).sort_values("Proficiency (%)", ascending=False)
        st.bar_chart(df.set_index("Skill"))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### ✅ Strengths")
        for s in result.get("strengths", []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("#### ⚠️ Skill Gaps")
        for g in result.get("gaps", []):
            st.markdown(f"- {g}")
    with col3:
        level = result.get("recommended_level", "Intermediate")
        level_color = {"Beginner": "🟢", "Intermediate": "🟡", "Advanced": "🔴"}.get(level, "🟡")
        st.markdown("#### 🎯 Recommended Level")
        st.markdown(f"### {level_color} {level}")
        st.markdown("_Based on your profile_")
