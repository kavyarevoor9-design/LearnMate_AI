"""
IBM Granite AI Client — wraps watsonx.ai REST API calls for all platform agents.
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

WATSONX_API_KEY   = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2")

# --------------------------------------------------------------------------- #
#  Authentication                                                              #
# --------------------------------------------------------------------------- #
_iam_token_cache: dict = {}

def _get_iam_token() -> str:
    """Fetch (or return cached) IBM IAM bearer token."""
    if _iam_token_cache.get("token"):
        return _iam_token_cache["token"]

    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WATSONX_API_KEY,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    _iam_token_cache["token"] = token
    return token


def invalidate_token() -> None:
    """Clear cached IAM token (call on 401 to force refresh)."""
    _iam_token_cache.clear()


# --------------------------------------------------------------------------- #
#  Core generation call                                                        #
# --------------------------------------------------------------------------- #
def generate(
    prompt: str,
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    stop_sequences: list[str] | None = None,
) -> str:
    """
    Call IBM Granite via the watsonx.ai /generation endpoint.
    Returns the generated text string.
    Raises RuntimeError on HTTP / API errors.
    """
    if (not WATSONX_API_KEY or WATSONX_API_KEY == "your_ibm_watsonx_api_key_here"
            or not WATSONX_PROJECT_ID or WATSONX_PROJECT_ID == "your_watsonx_project_id_here"):
        return _mock_response(prompt)

    try:
        token = _get_iam_token()
    except Exception:
        # API key invalid — fall back to demo mode silently
        return _mock_response(prompt)
    url   = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"

    params = {
        "max_new_tokens":    max_new_tokens  or int(os.getenv("GRANITE_MAX_NEW_TOKENS", 1024)),
        "temperature":       temperature     or float(os.getenv("GRANITE_TEMPERATURE", 0.7)),
        "top_p":             top_p           or float(os.getenv("GRANITE_TOP_P", 0.9)),
        "top_k":             top_k           or int(os.getenv("GRANITE_TOP_K", 50)),
        "repetition_penalty": float(os.getenv("GRANITE_REPETITION_PENALTY", 1.1)),
    }
    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    payload = {
        "model_id":   GRANITE_MODEL_ID,
        "project_id": WATSONX_PROJECT_ID,
        "input":      prompt,
        "parameters": params,
    }

    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            json=payload,
            timeout=60,
        )
        if resp.status_code == 401:
            invalidate_token()
            token = _get_iam_token()
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type":  "application/json",
                    "Accept":        "application/json",
                },
                json=payload,
                timeout=60,
            )
        resp.raise_for_status()
        data = resp.json()
        return data["results"][0]["generated_text"].strip()
    except requests.RequestException as exc:
        raise RuntimeError(f"Granite API error: {exc}") from exc


# --------------------------------------------------------------------------- #
#  Demo / offline mock (used when no real API key is configured)               #
# --------------------------------------------------------------------------- #
def _mock_response(prompt: str) -> str:
    """Return deterministic demo text so the UI is fully explorable offline."""
    if "assess" in prompt.lower() or "skill" in prompt.lower():
        return json.dumps({
            "proficiency_scores": {"Python": 65, "Machine Learning": 40, "SQL": 70, "Statistics": 55, "Deep Learning": 25},
            "strengths": ["Python fundamentals", "SQL queries", "Data manipulation"],
            "gaps": ["Neural networks", "Model deployment", "Advanced statistics"],
            "recommended_level": "Intermediate"
        })
    if "roadmap" in prompt.lower():
        return json.dumps({
            "title": "Your Personalised AI/ML Roadmap",
            "duration_weeks": 16,
            "phases": [
                {"phase": 1, "title": "Foundations", "weeks": "1-4", "topics": ["Python advanced", "Pandas & NumPy", "Data visualisation"]},
                {"phase": 2, "title": "Core ML",     "weeks": "5-9", "topics": ["Scikit-learn", "Supervised learning", "Model evaluation"]},
                {"phase": 3, "title": "Deep Learning","weeks": "10-13","topics": ["TensorFlow / PyTorch", "CNNs & RNNs", "Transfer learning"]},
                {"phase": 4, "title": "Deployment",  "weeks": "14-16","topics": ["MLflow", "FastAPI", "Docker & cloud deploy"]},
            ]
        })
    if "course" in prompt.lower() or "recommend" in prompt.lower():
        return json.dumps({"courses": [
            {"title": "Machine Learning Specialisation", "provider": "Coursera (Andrew Ng)", "level": "Intermediate", "duration": "3 months", "match_score": 95},
            {"title": "Deep Learning with PyTorch",      "provider": "fast.ai",              "level": "Intermediate", "duration": "7 weeks",  "match_score": 88},
            {"title": "SQL for Data Science",            "provider": "DataCamp",             "level": "Beginner",     "duration": "4 hours",  "match_score": 82},
            {"title": "Statistics for ML",               "provider": "Khan Academy",         "level": "Beginner",     "duration": "6 weeks",  "match_score": 78},
        ]})
    if "progress" in prompt.lower() or "insight" in prompt.lower():
        return "You're making excellent progress! Your Python skills have improved by 20% this week. Focus next on completing the Neural Networks module — it's the last major gap before you reach your goal. Tip: Try the hands-on Kaggle notebooks for immediate practice."
    return "I'm your AI learning assistant powered by IBM Granite. How can I help you today?"
