"""
Course Recommendation Agent — suggests relevant courses via IBM Granite.
"""
import json
import streamlit as st
import granite_client as gc


SAMPLE_COURSES = {
    "Artificial Intelligence & Machine Learning": [
        {"title": "Machine Learning Specialisation",        "provider": "Coursera (Andrew Ng)",    "level": "Intermediate", "duration": "3 months",  "url": "https://www.coursera.org/specializations/machine-learning-introduction", "tags": ["ML", "Python", "Algorithms"]},
        {"title": "Deep Learning Specialisation",           "provider": "Coursera (deeplearning.ai)","level": "Intermediate","duration": "5 months", "url": "https://www.coursera.org/specializations/deep-learning",                "tags": ["Deep Learning", "TensorFlow", "Neural Networks"]},
        {"title": "fast.ai Practical Deep Learning",        "provider": "fast.ai",                 "level": "Intermediate", "duration": "7 weeks",   "url": "https://course.fast.ai",                                                "tags": ["PyTorch", "Deep Learning", "Practical"]},
        {"title": "IBM AI Engineering Certificate",         "provider": "Coursera (IBM)",           "level": "Intermediate", "duration": "6 months",  "url": "https://www.coursera.org/professional-certificates/ai-engineer",       "tags": ["AI", "ML", "IBM Watson"]},
        {"title": "Statistics for Machine Learning",        "provider": "Udemy",                   "level": "Beginner",     "duration": "20 hours",  "url": "https://www.udemy.com",                                                "tags": ["Statistics", "Math", "ML Foundations"]},
        {"title": "Applied Data Science with Python",       "provider": "Coursera (Univ. Michigan)","level": "Intermediate", "duration": "5 months", "url": "https://www.coursera.org/specializations/data-science-python",         "tags": ["Python", "Data Science", "Visualisation"]},
    ],
    "Web Development": [
        {"title": "The Complete Web Developer Bootcamp",    "provider": "Udemy (Colt Steele)",     "level": "Beginner",     "duration": "63 hours",  "url": "https://www.udemy.com",                                                "tags": ["HTML", "CSS", "JavaScript", "Node.js"]},
        {"title": "Full-Stack React & Node.js",             "provider": "freeCodeCamp",            "level": "Intermediate", "duration": "Self-paced","url": "https://www.freecodecamp.org",                                         "tags": ["React", "Node.js", "REST API"]},
        {"title": "TypeScript Deep Dive",                   "provider": "Udemy",                   "level": "Intermediate", "duration": "15 hours",  "url": "https://www.udemy.com",                                                "tags": ["TypeScript", "JavaScript"]},
        {"title": "Next.js & React — The Complete Guide",   "provider": "Udemy (Maximilian S.)",   "level": "Intermediate", "duration": "25 hours",  "url": "https://www.udemy.com",                                                "tags": ["React", "Next.js", "Full-Stack"]},
    ],
    "Data Science": [
        {"title": "IBM Data Science Professional Certificate","provider": "Coursera (IBM)",        "level": "Beginner",     "duration": "10 months", "url": "https://www.coursera.org/professional-certificates/ibm-data-science", "tags": ["Python", "SQL", "ML", "IBM"]},
        {"title": "Data Science with R",                    "provider": "DataCamp",                "level": "Beginner",     "duration": "4 months",  "url": "https://www.datacamp.com",                                             "tags": ["R", "Statistics", "Visualisation"]},
        {"title": "SQL for Data Analysis",                  "provider": "Udacity",                 "level": "Beginner",     "duration": "2 months",  "url": "https://www.udacity.com",                                              "tags": ["SQL", "Data Analysis"]},
    ],
    "Cloud Computing": [
        {"title": "AWS Cloud Practitioner Essentials",      "provider": "AWS Training",            "level": "Beginner",     "duration": "6 hours",   "url": "https://aws.amazon.com/training",                                      "tags": ["AWS", "Cloud", "Fundamentals"]},
        {"title": "Google Cloud Associate Engineer",        "provider": "Google Cloud Skills Boost","level": "Intermediate","duration": "3 months",  "url": "https://cloud.google.com/learn",                                        "tags": ["GCP", "Kubernetes", "Cloud"]},
        {"title": "Docker & Kubernetes: The Practical Guide","provider": "Udemy",                  "level": "Intermediate", "duration": "24 hours",  "url": "https://www.udemy.com",                                                "tags": ["Docker", "Kubernetes", "DevOps"]},
    ],
    "Cybersecurity": [
        {"title": "CompTIA Security+ Exam Prep",            "provider": "Udemy",                   "level": "Beginner",     "duration": "21 hours",  "url": "https://www.udemy.com",                                                "tags": ["Security", "CompTIA", "Networking"]},
        {"title": "Ethical Hacking Bootcamp",               "provider": "TCM Security",            "level": "Intermediate", "duration": "25 hours",  "url": "https://academy.tcm-sec.com",                                          "tags": ["Penetration Testing", "Ethical Hacking"]},
        {"title": "IBM Cybersecurity Analyst Certificate",  "provider": "Coursera (IBM)",          "level": "Beginner",     "duration": "8 months",  "url": "https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst", "tags": ["SIEM", "Incident Response", "IBM"]},
    ],
    "Mobile Development": [
        {"title": "Flutter & Dart — The Complete Guide",    "provider": "Udemy",                   "level": "Beginner",     "duration": "43 hours",  "url": "https://www.udemy.com",                                                "tags": ["Flutter", "Dart", "iOS", "Android"]},
        {"title": "React Native — The Practical Guide",     "provider": "Udemy",                   "level": "Intermediate", "duration": "33 hours",  "url": "https://www.udemy.com",                                                "tags": ["React Native", "JavaScript", "iOS", "Android"]},
    ],
}


def _build_recommendation_prompt(student_profile: dict, assessment: dict) -> str:
    domain  = student_profile.get("domain", "AI/ML")
    courses = SAMPLE_COURSES.get(domain, [])
    return f"""You are an expert educational AI assistant powered by IBM Granite.

Based on the student's profile and skill assessment, recommend the most relevant courses from the catalogue below.

Student Profile:
- Goal: {student_profile.get('goal')}
- Domain: {domain}
- Level: {assessment.get('recommended_level', 'Intermediate')}
- Skill Gaps: {', '.join(assessment.get('gaps', []))}
- Strengths: {', '.join(assessment.get('strengths', []))}
- Weekly Study Hours: {student_profile.get('hours', 5)}

Available Courses:
{json.dumps(courses, indent=2)}

Return a JSON object in this exact format:
{{
  "courses": [
    {{
      "title": "...",
      "provider": "...",
      "level": "...",
      "duration": "...",
      "match_score": 0-100,
      "reason": "Why this course fits this student"
    }},
    ...
  ]
}}

Include all courses ranked by match_score. Return ONLY the JSON object."""


def render_course_recommendations(student_profile: dict, assessment: dict) -> list:
    """Render course recommendations UI; return list of recommended courses."""
    st.markdown("## 📚 Recommended Courses")
    st.markdown(
        "IBM Granite analyses your skill gaps and goals to surface the courses "
        "most likely to move you forward."
    )

    if not assessment:
        st.info("Complete the Skill Assessment first to get personalised course recommendations.")
        return []

    cached = st.session_state.get("course_recommendations")
    if not cached:
        with st.spinner("IBM Granite is curating your course list…"):
            prompt = _build_recommendation_prompt(student_profile, assessment)
            try:
                raw = gc.generate(prompt)
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data  = json.loads(raw.strip())
                courses = data.get("courses", [])

                # Merge match_score / reason from AI into the static catalogue
                domain   = student_profile.get("domain", "Artificial Intelligence & Machine Learning")
                catalogue = SAMPLE_COURSES.get(domain, [])
                merged   = []
                for ai_c in courses:
                    base = next((c for c in catalogue if c["title"] == ai_c["title"]), {})
                    merged.append({**base, **ai_c})
                if not merged:
                    merged = courses
                st.session_state["course_recommendations"] = merged
                cached = merged
            except Exception as exc:
                st.error(f"Recommendation error: {exc}")
                return []

    if not cached:
        return []

    # Sort by match score
    cached.sort(key=lambda c: c.get("match_score", 0), reverse=True)

    # Filter controls
    levels = ["All"] + sorted({c.get("level", "All") for c in cached})
    sel_level = st.selectbox("Filter by level:", levels)

    filtered = cached if sel_level == "All" else [c for c in cached if c.get("level") == sel_level]

    for i, course in enumerate(filtered):
        score = course.get("match_score", 80)
        score_colour = "#22c55e" if score >= 85 else "#f59e0b" if score >= 70 else "#ef4444"
        with st.expander(f"{'⭐ ' if i == 0 else ''}**{course.get('title', 'Course')}** — {course.get('provider', '')}", expanded=(i == 0)):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.markdown(f"**Provider:** {course.get('provider', 'N/A')}")
                st.markdown(f"**Duration:** {course.get('duration', 'N/A')}")
                st.markdown(f"**Level:** {course.get('level', 'N/A')}")
                reason = course.get("reason", "")
                if reason:
                    st.markdown(f"**Why this course:** _{reason}_")
                tags = course.get("tags", [])
                if tags:
                    st.markdown(" ".join([f"`{t}`" for t in tags]))
            with c2:
                st.markdown(
                    f"<div style='text-align:center; font-size:2rem; font-weight:700; color:{score_colour}'>"
                    f"{score}%</div><div style='text-align:center; font-size:0.75rem; color:#6b7280'>AI Match Score</div>",
                    unsafe_allow_html=True,
                )
            with c3:
                url = course.get("url", "#")
                st.markdown(
                    f"<br><a href='{url}' target='_blank'>"
                    "<button style='background:#3b82f6;color:white;border:none;padding:8px 16px;"
                    "border-radius:6px;cursor:pointer;width:100%'>🔗 Open Course</button></a>",
                    unsafe_allow_html=True,
                )

    if st.button("🔄 Refresh Recommendations", use_container_width=True):
        st.session_state.pop("course_recommendations", None)
        st.rerun()

    return cached
