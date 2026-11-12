"""
LearnAI — Agentic AI Personalized Learning Platform
Powered by IBM Granite via watsonx.ai
Run: streamlit run app.py
"""
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Page config (MUST be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LearnAI – IBM Granite Powered Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #f0f4ff; }
[data-testid="stSidebar"]          { background: #0f172a; }
[data-testid="stSidebar"] *        { color: #e2e8f0 !important; }
.main .block-container             { padding-top: 1.5rem; max-width: 1200px; }

.learn-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
    margin-bottom: 16px;
}
.hero-banner {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 60%, #7c3aed 100%);
    border-radius: 16px;
    padding: 32px 40px;
    color: white;
    margin-bottom: 24px;
}
.hero-banner h1 { margin: 0; font-size: 2.2rem; color: white; }
.hero-banner p  { margin: 8px 0 0; opacity: 0.85; font-size: 1.05rem; }

div[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
div[data-testid="stMetricLabel"] { font-size: .8rem; color: #6b7280; }
div[data-testid="stMetricValue"] { font-size: 1.7rem; color: #1f2937; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "page":                   "home",
        "student_profile":        {},
        "onboarding_complete":    False,
        "assessment_result":      None,
        "self_scores":            {},
        "course_recommendations": None,
        "roadmap":                None,
        "last_insight":           None,
        "progress_data":          None,
        "quiz_history":           [],
        "chat_history":           [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ─────────────────────────────────────────────────────────────────────────────
def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:16px 0'>"
            "<span style='font-size:2.5rem'>🎓</span>"
            "<h2 style='margin:4px 0;color:white'>LearnAI</h2>"
            "<p style='font-size:0.75rem;color:#94a3b8;margin:0'>Powered by IBM Granite</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<hr style='border-color:#334155;margin:8px 0'>", unsafe_allow_html=True)

        profile = st.session_state.get("student_profile", {})
        if profile.get("name"):
            st.markdown(
                f"<div style='background:#1e293b;border-radius:8px;padding:12px;margin-bottom:12px'>"
                f"<p style='margin:0;font-size:.75rem;color:#94a3b8'>Logged in as</p>"
                f"<p style='margin:0;font-weight:600;color:white'>{profile['name']}</p>"
                f"<p style='margin:2px 0 0;font-size:.75rem;color:#64748b'>{profile.get('domain','')}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        pages = [
            ("🏠", "Home",               "home"),
            ("👤", "My Profile",         "profile"),
            ("🧠", "Skill Assessment",   "assessment"),
            ("📚", "Course Recommender", "courses"),
            ("🗺️", "Learning Roadmap",   "roadmap"),
            ("📈", "Progress Tracker",   "progress"),
            ("🤖", "AI Assistant",       "chat"),
        ]

        current = st.session_state.get("page", "home")
        for icon, label, key in pages:
            locked = (
                not st.session_state["onboarding_complete"]
                and key not in ("home", "profile")
            )
            button_label = f"{icon} {label}" + (" 🔒" if locked else "")
            if st.button(
                button_label,
                key=f"nav_{key}",
                use_container_width=True,
                disabled=locked,
            ):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("<hr style='border-color:#334155;margin:12px 0'>", unsafe_allow_html=True)

        if st.session_state["onboarding_complete"]:
            progress = st.session_state.get("progress_data") or {}
            st.markdown(
                f"<div style='font-size:.78rem;color:#94a3b8'>"
                f"⏱ Study Hours: <b style='color:white'>{progress.get('total_hours',0):.1f}h</b><br>"
                f"🔥 Streak: <b style='color:white'>{progress.get('streak_days',0)} days</b><br>"
                f"✅ Topics Done: <b style='color:white'>{len(progress.get('completed_topics',[]))}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='border-color:#334155;margin:12px 0'>", unsafe_allow_html=True)

        # Show live vs demo mode badge
        import os as _os
        _key = _os.getenv("WATSONX_API_KEY", "")
        _pid = _os.getenv("WATSONX_PROJECT_ID", "")
        _placeholder_key = _key in ("", "your_ibm_watsonx_api_key_here")
        _placeholder_pid = _pid in ("", "your_watsonx_project_id_here")
        if _placeholder_key or _placeholder_pid:
            st.markdown(
                "<div style='background:#78350f;border-radius:6px;padding:6px 10px;"
                "text-align:center;font-size:.72rem;color:#fde68a;margin-bottom:6px'>"
                "⚠️ Demo Mode<br><span style='opacity:.8'>Add credentials in .env<br>for live IBM Granite</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#14532d;border-radius:6px;padding:6px 10px;"
                "text-align:center;font-size:.72rem;color:#bbf7d0;margin-bottom:6px'>"
                "✅ Live Mode<br><span style='opacity:.8'>IBM Granite Active</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            "<p style='font-size:.7rem;color:#475569;text-align:center'>"
            "IBM Granite · watsonx.ai<br>© 2025 LearnAI Platform</p>",
            unsafe_allow_html=True,
        )

    return st.session_state.get("page", "home")


# ─────────────────────────────────────────────────────────────────────────────
# Page: Home
# ─────────────────────────────────────────────────────────────────────────────
def page_home() -> None:
    st.markdown(
        """<div class='hero-banner'>
        <h1>🎓 Welcome to LearnAI</h1>
        <p>An <b>Agentic AI-Powered Personalised Learning Platform</b> — driven by <b>IBM Granite</b> on watsonx.ai</p>
        </div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    features = [
        ("🧠", "Skill Assessment",    "AI evaluates your current knowledge and identifies precise gaps"),
        ("📚", "Course Recommender",  "Granite matches you with the best courses from top providers"),
        ("🗺️", "Adaptive Roadmap",    "A week-by-week personalised learning plan built just for you"),
        ("📈", "Progress Tracking",   "Log sessions, track streaks, visualise growth over time"),
        ("🤖", "AI Coach",            "Chat with IBM Granite for instant study support and motivation"),
        ("🧪", "Knowledge Quizzes",   "Reinforce learning with instant AI-generated quizzes"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        col = [c1, c2, c3][i % 3]
        with col:
            st.markdown(
                f"<div class='learn-card'><h3>{icon} {title}</h3>"
                f"<p style='color:#6b7280;font-size:.9rem'>{desc}</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown("### How It Works")
        steps = [
            ("1️⃣", "Create your profile",        "Tell us your learning goal, domain, and available time."),
            ("2️⃣", "Complete skill assessment",   "Rate yourself on core topics; Granite refines your profile."),
            ("3️⃣", "Get recommendations",         "Granite surfaces the most relevant courses from top providers."),
            ("4️⃣", "Follow your roadmap",          "A custom week-by-week plan adapts as you progress."),
            ("5️⃣", "Track & improve",              "Log study sessions, take quizzes, get AI coach insights."),
        ]
        for step_icon, step_title, step_desc in steps:
            st.markdown(
                f"<div style='display:flex;gap:12px;align-items:flex-start;margin-bottom:10px'>"
                f"<span style='font-size:1.3rem'>{step_icon}</span>"
                f"<div><b>{step_title}</b><br>"
                f"<span style='color:#6b7280;font-size:.88rem'>{step_desc}</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    with col_b:
        st.markdown(
            "<div class='learn-card' style='text-align:center'>"
            "<img src='https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg' "
            "width='80' style='margin-bottom:8px'><br>"
            "<b>IBM Granite</b><br>"
            "<span style='color:#6b7280;font-size:.8rem'>watsonx.ai foundation model</span>"
            "<hr style='margin:8px 0'>"
            "<span style='font-size:.8rem;color:#3b82f6'>granite-13b-instruct-v2</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if not st.session_state["onboarding_complete"]:
        if st.button("🚀 Get Started — Create My Profile", type="primary", use_container_width=True):
            st.session_state["page"] = "profile"
            st.rerun()
    else:
        name = st.session_state["student_profile"].get("name", "")
        st.success(f"Welcome back, **{name}**! Continue where you left off.")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧠 Skill Assessment", use_container_width=True):
                st.session_state["page"] = "assessment"; st.rerun()
        with col2:
            if st.button("🗺️ My Roadmap", use_container_width=True):
                st.session_state["page"] = "roadmap"; st.rerun()
        with col3:
            if st.button("📈 Progress Tracker", use_container_width=True):
                st.session_state["page"] = "progress"; st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Page: Profile
# ─────────────────────────────────────────────────────────────────────────────
def page_profile() -> None:
    st.markdown("## 👤 Student Profile")
    st.markdown(
        "Tell us about yourself so IBM Granite can personalise your entire experience."
    )

    domains = [
        "Artificial Intelligence & Machine Learning",
        "Web Development",
        "Data Science",
        "Cloud Computing",
        "Cybersecurity",
        "Mobile Development",
    ]
    experiences   = ["Complete Beginner", "Some Basics", "Intermediate", "Advanced"]
    styles        = ["Videos", "Reading", "Hands-on Projects", "Mixed"]

    saved = st.session_state["student_profile"]

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(
                "Full Name *",
                value=saved.get("name", ""),
                placeholder="e.g. Alex Johnson",
            )
            domain = st.selectbox(
                "Domain of Interest *",
                domains,
                index=domains.index(saved.get("domain", domains[0])),
            )
            experience = st.selectbox(
                "Prior Experience",
                experiences,
                index=experiences.index(saved.get("experience", "Some Basics")),
            )
        with col2:
            goal = st.text_area(
                "Learning Goal *",
                value=saved.get("goal", ""),
                placeholder="e.g. Become an ML Engineer in 6 months",
                height=100,
            )
            hours = st.slider(
                "Available Study Hours / Week",
                1, 40,
                int(saved.get("hours", 10)),
            )
            learning_style = st.selectbox(
                "Preferred Learning Style",
                styles,
                index=styles.index(saved.get("learning_style", "Mixed")),
            )

        interests = st.multiselect(
            "Specific Interests (select all that apply)",
            [
                "Computer Vision", "NLP / LLMs", "Data Engineering", "MLOps",
                "Robotics", "FinTech", "Healthcare AI", "Game Dev",
                "AR/VR", "Blockchain", "Edge AI",
            ],
            default=saved.get("interests", []),
        )

        submitted = st.form_submit_button(
            "💾 Save Profile & Continue", type="primary", use_container_width=True
        )
        if submitted:
            if not name or not goal:
                st.error("Name and Learning Goal are required.")
            else:
                st.session_state["student_profile"] = {
                    "name":           name,
                    "domain":         domain,
                    "goal":           goal,
                    "experience":     experience,
                    "hours":          hours,
                    "learning_style": learning_style,
                    "interests":      interests,
                }
                st.session_state["onboarding_complete"] = True
                # Invalidate cached AI outputs so they regenerate with the new profile
                for k in ["assessment_result", "course_recommendations", "roadmap"]:
                    st.session_state[k] = None
                st.success(
                    f"Profile saved! Welcome, **{name}** 🎉  Proceeding to Skill Assessment…"
                )
                st.session_state["page"] = "assessment"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Page: Skill Assessment
# ─────────────────────────────────────────────────────────────────────────────
def page_assessment() -> None:
    from skills_assessment import render_skill_assessment, render_assessment_results

    profile = st.session_state["student_profile"]
    result  = render_skill_assessment(profile)
    if result:
        st.markdown("---")
        render_assessment_results(result)
        st.markdown("---")
        if st.button(
            "📚 See Course Recommendations →", type="primary", use_container_width=True
        ):
            st.session_state["page"] = "courses"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Page: Course Recommendations
# ─────────────────────────────────────────────────────────────────────────────
def page_courses() -> None:
    from course_recommendations import render_course_recommendations

    profile    = st.session_state["student_profile"]
    assessment = st.session_state.get("assessment_result") or {}
    courses    = render_course_recommendations(profile, assessment)
    if courses:
        st.markdown("---")
        if st.button(
            "🗺️ Generate My Learning Roadmap →", type="primary", use_container_width=True
        ):
            st.session_state["page"] = "roadmap"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Page: Learning Roadmap
# ─────────────────────────────────────────────────────────────────────────────
def page_roadmap() -> None:
    from learning_roadmap import render_learning_roadmap

    profile    = st.session_state["student_profile"]
    assessment = st.session_state.get("assessment_result") or {}
    courses    = st.session_state.get("course_recommendations") or []
    roadmap    = render_learning_roadmap(profile, assessment, courses)
    if roadmap:
        st.markdown("---")
        if st.button(
            "📈 Go to Progress Tracker →", type="primary", use_container_width=True
        ):
            st.session_state["page"] = "progress"
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Page: Progress Tracker
# ─────────────────────────────────────────────────────────────────────────────
def page_progress() -> None:
    from progress_tracker import render_progress_tracker

    profile    = st.session_state["student_profile"]
    assessment = st.session_state.get("assessment_result") or {}
    roadmap    = st.session_state.get("roadmap")
    render_progress_tracker(profile, assessment, roadmap)


# ─────────────────────────────────────────────────────────────────────────────
# Page: AI Assistant Chat
# ─────────────────────────────────────────────────────────────────────────────
def page_chat() -> None:
    import granite_client as gc

    st.markdown("## 🤖 AI Learning Assistant")
    st.markdown(
        "Ask IBM Granite anything about your learning journey, study strategies, or course content."
    )

    if not st.session_state["chat_history"]:
        st.session_state["chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm your AI learning assistant powered by **IBM Granite**. "
                    "I can help you understand concepts, suggest study strategies, explain course topics, "
                    "and keep you motivated. What would you like to explore today? 🚀"
                ),
            }
        ]

    # Render chat history
    for msg in st.session_state["chat_history"]:
        avatar = "🤖" if msg["role"] == "assistant" else "🧑‍🎓"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # User input
    if user_input := st.chat_input("Ask IBM Granite…"):
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_input)

        # Build context-aware prompt
        profile    = st.session_state.get("student_profile", {})
        assessment = st.session_state.get("assessment_result") or {}
        context = (
            f"Student: {profile.get('name','Learner')}, "
            f"Goal: {profile.get('goal','')}, "
            f"Domain: {profile.get('domain','')}, "
            f"Level: {assessment.get('recommended_level','Intermediate')}"
        )
        history_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in st.session_state["chat_history"][-6:]
        )
        prompt = f"""You are a helpful AI learning assistant powered by IBM Granite.

Student context: {context}

Conversation history:
{history_text}

User: {user_input}

Provide a helpful, concise, and encouraging response. If explaining a technical concept, use simple language and examples. Keep response under 300 words."""

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("IBM Granite is thinking…"):
                try:
                    reply = gc.generate(prompt, max_new_tokens=500, temperature=0.75)
                except Exception as exc:
                    reply = f"Sorry, I encountered an error: {exc}"
            st.markdown(reply)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": reply}
            )

    # Sidebar quick-actions
    with st.sidebar:
        st.markdown("---")
        st.markdown("**💡 Quick Questions**")
        quick_qs = [
            "What's the best way to learn ML?",
            "Explain neural networks simply",
            "How do I stay motivated?",
            "What projects should I build?",
        ]
        for q in quick_qs:
            if st.button(q, key=f"quick_{q}", use_container_width=True):
                st.session_state["chat_history"].append({"role": "user", "content": q})
                st.rerun()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    page = _sidebar()

    page_map = {
        "home":       page_home,
        "profile":    page_profile,
        "assessment": page_assessment,
        "courses":    page_courses,
        "roadmap":    page_roadmap,
        "progress":   page_progress,
        "chat":       page_chat,
    }

    handler = page_map.get(page, page_home)
    handler()


if __name__ == "__main__":
    main()
