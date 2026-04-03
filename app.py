# =============================================================================
# CareerWeave: Multi-Agent Job Orchestrator
# GEN AI APAC Hackathon Entry
#
# Architecture: Single-file Streamlit app with a multi-agent pipeline:
#   Agent 1 (Scout)     → SerpApi scrapes live job listings
#   Agent 2 (Analyst)   → Gemini scores resume ATS match
#   Agent 3 (Architect) → Gemini rewrites resume bullets for the job
#   Agent 4 (Coach)     → Gemini generates targeted interview questions
#
# Author: CareerWeave Team
# Stack: Streamlit · google-generativeai · LangChain · SerpApi · PyPDF2/docx2txt
# =============================================================================

import streamlit as st
import google.generativeai as genai
from langchain.prompts import PromptTemplate
import requests
import json
import re
import io

# ── Optional document parsers (graceful fallback if not installed) ─────────────
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import docx2txt
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# =============================================================================
# PAGE CONFIG — must be the very first Streamlit call
# =============================================================================
st.set_page_config(
    page_title="CareerWeave",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# GLOBAL CSS — dark, editorial, cyber-grid aesthetic
# =============================================================================
st.markdown("""
<style>
/* ── Google Font import ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;600&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #080c10;
    --surface:   #0d1117;
    --border:    #1e2733;
    --accent:    #00e5ff;
    --accent2:   #7c3aed;
    --success:   #22d3a5;
    --warn:      #f59e0b;
    --text:      #e2e8f0;
    --muted:     #64748b;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stFileUploader {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

/* ── Hero header ── */
.hero-wrap {
    background: linear-gradient(135deg, #080c10 0%, #0d1a2e 50%, #0a0f16 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2.4rem 2.8rem 2rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
        repeating-linear-gradient(0deg,   transparent, transparent 39px, #1e273320 39px, #1e273320 40px),
        repeating-linear-gradient(90deg,  transparent, transparent 39px, #1e273320 39px, #1e273320 40px);
    pointer-events: none;
}
.hero-title {
    font-family: var(--font-head);
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.4rem;
    position: relative;
}
.hero-sub {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--muted);
    letter-spacing: 0.05em;
    position: relative;
}
.hero-badge {
    display: inline-block;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
    color: #fff;
    font-family: var(--font-head);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 0.9rem;
}

/* ── Agent status pills ── */
.agent-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.55rem 0.9rem;
    border-radius: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    margin-bottom: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.8rem;
}
.agent-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    animation: pulse 1.2s infinite;
}
@keyframes pulse {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.3; }
}

/* ── Metric cards ── */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    text-align: center;
}
.metric-label {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-family: var(--font-head);
    font-size: 2rem;
    font-weight: 800;
    color: var(--accent);
}

/* ── Section card ── */
.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.section-title {
    font-family: var(--font-head);
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
}

/* ── Job card ── */
.job-card {
    background: linear-gradient(135deg, #0d1117, #0d1a2e);
    border: 1px solid var(--accent);
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.job-title {
    font-family: var(--font-head);
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text);
}
.job-company {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--accent);
    margin: 0.2rem 0 0.6rem;
}
.job-link a {
    color: var(--accent2) !important;
    font-size: 0.78rem;
    text-decoration: none;
}

/* ── Interview Q cards ── */
.iq-card {
    background: var(--bg);
    border-left: 3px solid var(--accent2);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.7rem;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    line-height: 1.6;
}
.iq-num {
    color: var(--accent2);
    font-weight: 600;
    margin-right: 6px;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(90deg, var(--accent2), var(--accent)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: var(--font-head) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.65rem 1.8rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-head) !important;
    color: var(--text) !important;
}

/* ── Progress bar override ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent2), var(--accent)) !important;
}

/* ── Text areas / code ── */
.stTextArea textarea, code, pre {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font-mono) !important;
    border: 1px solid var(--border) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# ── SIDEBAR ──────────────────────────────────────────────────────────────────
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 0.5rem; font-family:"Syne",sans-serif;'>
        <div style='font-size:1.4rem; font-weight:800; color:#00e5ff;'>⚙️ CareerWeave</div>
        <div style='font-size:0.7rem; color:#64748b; letter-spacing:.1em; text-transform:uppercase;'>Settings & Configuration</div>
    </div>
    <hr style='border-color:#1e2733; margin:0.6rem 0 1rem;'/>
    """, unsafe_allow_html=True)

    st.markdown("**🔑 API Keys**")
    gemini_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Get yours at https://aistudio.google.com",
    )
    serp_api_key = st.text_input(
        "SerpApi Key",
        type="password",
        placeholder="Your SerpApi key",
        help="Get yours at https://serpapi.com",
    )

    st.markdown("<hr style='border-color:#1e2733; margin:1rem 0;'/>", unsafe_allow_html=True)
    st.markdown("**📄 Upload Your Resume**")
    uploaded_file = st.file_uploader(
        "PDF or DOCX",
        type=["pdf", "docx"],
        help="Your base resume. CareerWeave will tailor it to the target role.",
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.success(f"✓ `{uploaded_file.name}` loaded", icon="📎")

    st.markdown("<hr style='border-color:#1e2733; margin:1rem 0;'/>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.7rem; color:#64748b; line-height:1.8;'>
        <b style='color:#e2e8f0;'>Pipeline Agents</b><br/>
        🔍 Scout — Job Discovery<br/>
        📊 Analyst — ATS Scoring<br/>
        ✍️ Architect — Resume Tailoring<br/>
        🎯 Coach — Interview Prep
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# ── MAIN LAYOUT ──────────────────────────────────────────────────────────────
# =============================================================================

# Hero header
st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">GEN AI APAC Hackathon · Multi-Agent Pipeline</div>
    <div class="hero-title">🕸️ CareerWeave</div>
    <div style='font-family:"Syne",sans-serif; font-size:1.1rem; font-weight:600; color:#e2e8f0; margin-bottom:0.4rem;'>
        Multi-Agent Job Orchestrator
    </div>
    <div class="hero-sub">
        Weaving your profile, live job data, and interview prep into one seamless autonomous pipeline.
    </div>
</div>
""", unsafe_allow_html=True)

# Target job input
col_input, col_btn = st.columns([3, 1])
with col_input:
    job_query = st.text_input(
        "🎯 Target Role",
        placeholder="e.g.  Cybersecurity Analyst India  |  ML Engineer Bangalore  |  DevSecOps Remote",
        label_visibility="visible",
    )
with col_btn:
    st.markdown("<br/>", unsafe_allow_html=True)
    run_pipeline = st.button("🚀 Deploy CareerWeave Agents")


# =============================================================================
# ── HELPER FUNCTIONS ─────────────────────────────────────────────────────────
# =============================================================================

def extract_resume_text(file) -> str:
    """
    Extract plain text from an uploaded PDF or DOCX file.
    Returns a string, or raises RuntimeError with a friendly message.
    """
    filename = file.name.lower()
    file_bytes = file.read()

    if filename.endswith(".pdf"):
        if not PDF_SUPPORT:
            raise RuntimeError("PyPDF2 is not installed. Run: pip install PyPDF2")
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
        if not text.strip():
            raise RuntimeError("Could not extract text from PDF. Try a text-based PDF.")
        return text

    elif filename.endswith(".docx"):
        if not DOCX_SUPPORT:
            raise RuntimeError("docx2txt is not installed. Run: pip install docx2txt")
        return docx2txt.process(io.BytesIO(file_bytes))

    else:
        raise RuntimeError("Unsupported file type. Please upload a PDF or DOCX.")


def scrape_top_job(query: str, serp_key: str) -> dict:
    """
    Agent 1 — Scout
    Hits the SerpApi /search endpoint with engine=google_jobs.
    Returns a dict with keys: title, company, location, description, link.
    Falls back gracefully if no results found.
    """
    params = {
        "engine":  "google_jobs",
        "q":       query,
        "api_key": serp_key,
        "num":     5,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    jobs = data.get("jobs_results", [])
    if not jobs:
        raise ValueError(
            f"SerpApi returned no jobs for query: '{query}'. "
            "Try a broader search term or check your API key."
        )

    # Pick the first job that has a meaningful description
    for job in jobs:
        desc = job.get("description", "").strip()
        if len(desc) > 100:
            return {
                "title":       job.get("title", "Unknown Title"),
                "company":     job.get("company_name", "Unknown Company"),
                "location":    job.get("location", "Unknown Location"),
                "description": desc[:4000],   # cap to stay within token limits
                "link":        job.get("related_links", [{}])[0].get("link", "#"),
            }

    # Fallback: return first job even with short description
    job = jobs[0]
    return {
        "title":       job.get("title", "Unknown Title"),
        "company":     job.get("company_name", "Unknown Company"),
        "location":    job.get("location", "Unknown Location"),
        "description": job.get("description", "No description available.")[:4000],
        "link":        job.get("related_links", [{}])[0].get("link", "#"),
    }


# ── LangChain PromptTemplate ──────────────────────────────────────────────────
# This is the core prompt that drives Agents 2, 3, and 4 simultaneously.
# We ask Gemini for a single structured JSON response to minimise API calls.
CAREERWEAVE_TEMPLATE = """
You are CareerWeave, an elite career intelligence system. Analyse the candidate's resume against the target job description and return ONLY a single valid JSON object — no markdown fences, no prose, no explanation outside the JSON.

=== CANDIDATE RESUME ===
{resume_text}

=== TARGET JOB DESCRIPTION ===
{job_description}

=== TARGET ROLE ===
{job_title} at {company}

=== INSTRUCTIONS ===
Return a JSON object with EXACTLY these keys:

{{
  "ats_score": <integer 0-100 reflecting keyword and skills match>,
  "match_reasoning": "<2-sentence explanation of the score>",
  "tailored_summary": "<3-sentence professional summary rewritten to exactly match this JD's language and priorities>",
  "tailored_bullets": [
    "<rewritten bullet 1 — quantified, action-verb-led, JD-keyword-rich>",
    "<rewritten bullet 2>",
    "<rewritten bullet 3>",
    "<rewritten bullet 4>",
    "<rewritten bullet 5>"
  ],
  "skills_gap": ["<missing skill 1>", "<missing skill 2>", "<missing skill 3>"],
  "interview_questions": [
    {{
      "question": "<highly specific technical/behavioural question from the JD>",
      "why_asked": "<1-sentence hint on what the interviewer is probing>",
      "answer_tip": "<1-sentence tactical tip>"
    }},
    {{
      "question": "<question 2>",
      "why_asked": "<hint>",
      "answer_tip": "<tip>"
    }},
    {{
      "question": "<question 3>",
      "why_asked": "<hint>",
      "answer_tip": "<tip>"
    }}
  ]
}}

Rules:
- The ats_score must be a plain integer (not a string).
- tailored_bullets must mirror real content from the resume but upgraded with JD vocabulary.
- interview_questions must be grounded in the SPECIFIC technologies, tools, and responsibilities in this exact JD.
- Output ONLY the JSON object. Nothing else.
"""

careerweave_prompt = PromptTemplate(
    input_variables=["resume_text", "job_description", "job_title", "company"],
    template=CAREERWEAVE_TEMPLATE,
)


def run_gemini_pipeline(
    gemini_key: str,
    resume_text: str,
    job: dict,
) -> dict:
    """
    Agents 2, 3, 4 — Analyst · Architect · Coach
    Configures the Gemini client, builds the prompt via LangChain,
    calls the API, and parses the JSON response.
    Returns the parsed dict.
    """
    # Configure the Gemini SDK with the user-supplied key
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-1.5-flash")   # fast + high context

    # Build the full prompt string via LangChain
    full_prompt = careerweave_prompt.format(
        resume_text=resume_text[:6000],       # guard context window
        job_description=job["description"],
        job_title=job["title"],
        company=job["company"],
    )

    # Generation config — low temperature for deterministic JSON output
    generation_config = genai.types.GenerationConfig(
        temperature=0.3,
        max_output_tokens=2048,
    )

    response = model.generate_content(
        full_prompt,
        generation_config=generation_config,
    )

    raw = response.text.strip()

    # ── Robust JSON extraction ────────────────────────────────────────────────
    # Strip markdown code fences if Gemini wraps response in ```json ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        # Attempt to extract JSON object via regex as last resort
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(
                f"Gemini did not return valid JSON.\n"
                f"Parse error: {e}\n"
                f"Raw response (first 500 chars):\n{raw[:500]}"
            )

    return result


# =============================================================================
# ── PIPELINE EXECUTION ────────────────────────────────────────────────────────
# =============================================================================

if run_pipeline:
    # ── Pre-flight validation ─────────────────────────────────────────────────
    errors = []
    if not gemini_api_key:
        errors.append("Gemini API Key is missing from the sidebar.")
    if not serp_api_key:
        errors.append("SerpApi Key is missing from the sidebar.")
    if not uploaded_file:
        errors.append("Please upload your resume (PDF or DOCX) in the sidebar.")
    if not job_query.strip():
        errors.append("Please enter a target job role in the search field above.")

    if errors:
        for e in errors:
            st.error(f"⚠️ {e}")
        st.stop()

    # ── Step 0: Extract resume text ───────────────────────────────────────────
    try:
        resume_text = extract_resume_text(uploaded_file)
    except Exception as e:
        st.error(f"❌ Resume parse failed: {e}")
        st.stop()

    # ── Agent execution with live status updates ───────────────────────────────
    job_data   = None
    ai_results = None

    # Agent 1 — Scout
    st.markdown("""
    <div class="agent-row">
        <div class="agent-dot"></div>
        <span style='color:#00e5ff; font-weight:600;'>Agent 1: Scout</span>
        <span style='color:#64748b;'>— Scanning live job market via SerpApi…</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("🔍 Scouting roles..."):
        try:
            job_data = scrape_top_job(job_query, serp_api_key)
        except Exception as e:
            st.error(f"❌ Scout Agent failed: {e}")
            st.stop()

    # Agent 2 — Analyst
    st.markdown("""
    <div class="agent-row">
        <div class="agent-dot"></div>
        <span style='color:#00e5ff; font-weight:600;'>Agent 2: Analyst</span>
        <span style='color:#64748b;'>— Scoring ATS keyword match with Gemini…</span>
    </div>
    """, unsafe_allow_html=True)

    # Agent 3 — Architect
    st.markdown("""
    <div class="agent-row">
        <div class="agent-dot"></div>
        <span style='color:#00e5ff; font-weight:600;'>Agent 3: Architect</span>
        <span style='color:#64748b;'>— Rewriting resume bullets for target JD…</span>
    </div>
    """, unsafe_allow_html=True)

    # Agent 4 — Coach
    st.markdown("""
    <div class="agent-row">
        <div class="agent-dot"></div>
        <span style='color:#00e5ff; font-weight:600;'>Agent 4: Coach</span>
        <span style='color:#64748b;'>— Generating targeted interview questions…</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("🤖 CareerWeave pipeline running…"):
        try:
            ai_results = run_gemini_pipeline(gemini_api_key, resume_text, job_data)
        except Exception as e:
            st.error(f"❌ Gemini pipeline failed: {e}")
            st.stop()

    # Pipeline complete banner
    st.success("✅ CareerWeave pipeline complete — all agents reporting.")
    st.markdown("<hr style='border-color:#1e2733; margin:1.2rem 0;'/>", unsafe_allow_html=True)

    # ==========================================================================
    # ── RESULTS DISPLAY ────────────────────────────────────────────────────────
    # ==========================================================================

    # ── Row 1: Job card + ATS score ───────────────────────────────────────────
    col_job, col_score = st.columns([3, 2], gap="medium")

    with col_job:
        st.markdown(f"""
        <div class="job-card">
            <div style='font-size:0.7rem; color:#64748b; letter-spacing:.12em; text-transform:uppercase; margin-bottom:0.4rem;'>
                🔍 Top Matched Role
            </div>
            <div class="job-title">{job_data['title']}</div>
            <div class="job-company">⚡ {job_data['company']} · {job_data['location']}</div>
            <div class="job-link">
                <a href="{job_data['link']}" target="_blank">🔗 View Full Listing →</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_score:
        score = int(ai_results.get("ats_score", 0))
        score = max(0, min(100, score))   # clamp to 0-100

        # Colour coding
        if score >= 75:
            score_color = "#22d3a5"
            score_label = "STRONG MATCH"
        elif score >= 50:
            score_color = "#f59e0b"
            score_label = "PARTIAL MATCH"
        else:
            score_color = "#ef4444"
            score_label = "LOW MATCH"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ATS Match Score</div>
            <div class="metric-value" style='color:{score_color};'>{score}%</div>
            <div style='font-family:"Syne",sans-serif; font-size:0.72rem; font-weight:700;
                        color:{score_color}; letter-spacing:.1em; margin-top:0.3rem;'>
                {score_label}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(score / 100)

        reasoning = ai_results.get("match_reasoning", "")
        if reasoning:
            st.caption(reasoning)

    # ── Row 2: Original vs Tailored Resume ───────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    col_orig, col_tail = st.columns(2, gap="medium")

    with col_orig:
        with st.expander("📄 Original Resume (uploaded)", expanded=False):
            st.text_area(
                label="original",
                value=resume_text,
                height=380,
                label_visibility="collapsed",
            )

    with col_tail:
        with st.expander("✨ CareerWeave Tailored Resume", expanded=True):
            tailored_summary  = ai_results.get("tailored_summary", "")
            tailored_bullets  = ai_results.get("tailored_bullets", [])

            tailored_display = "PROFESSIONAL SUMMARY\n" + "─" * 40 + "\n"
            tailored_display += tailored_summary + "\n\n"
            tailored_display += "KEY EXPERIENCE & ACHIEVEMENTS\n" + "─" * 40 + "\n"
            for bullet in tailored_bullets:
                tailored_display += f"• {bullet}\n"

            st.text_area(
                label="tailored",
                value=tailored_display,
                height=380,
                label_visibility="collapsed",
            )

    # ── Skills Gap ────────────────────────────────────────────────────────────
    skills_gap = ai_results.get("skills_gap", [])
    if skills_gap:
        st.markdown("""
        <div class="section-card" style="margin-top:1rem;">
            <div class="section-title">⚠️ Skills Gap — Areas to Develop</div>
        """, unsafe_allow_html=True)
        gap_cols = st.columns(len(skills_gap))
        for i, skill in enumerate(skills_gap):
            with gap_cols[i]:
                st.markdown(f"""
                <div style='background:#1a0a0a; border:1px solid #ef4444;
                            border-radius:8px; padding:0.7rem 1rem; text-align:center;
                            font-family:"Syne",sans-serif; font-size:0.82rem;
                            font-weight:700; color:#ef4444;'>
                    {skill}
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Interview Questions ────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-card">
        <div class="section-title">🎯 Interview Prep — AI-Generated Questions</div>
    """, unsafe_allow_html=True)

    interview_qs = ai_results.get("interview_questions", [])
    for i, q_item in enumerate(interview_qs, 1):
        if isinstance(q_item, dict):
            question   = q_item.get("question", "")
            why_asked  = q_item.get("why_asked", "")
            answer_tip = q_item.get("answer_tip", "")
        else:
            question   = str(q_item)
            why_asked  = ""
            answer_tip = ""

        st.markdown(f"""
        <div class="iq-card">
            <div><span class="iq-num">Q{i}.</span>{question}</div>
            {"<div style='margin-top:0.5rem; color:#64748b; font-size:0.75rem;'>💡 " + why_asked + "</div>" if why_asked else ""}
            {"<div style='margin-top:0.3rem; color:#22d3a5; font-size:0.75rem;'>🎯 " + answer_tip + "</div>" if answer_tip else ""}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; font-family:"JetBrains Mono",monospace;
                font-size:0.7rem; color:#1e2733; padding:1rem 0;'>
        CareerWeave · GEN AI APAC Hackathon · Powered by Gemini + SerpApi + LangChain
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Idle state — show pipeline diagram ────────────────────────────────────
    st.markdown("""
    <div class="section-card" style="margin-top: 0.5rem;">
        <div class="section-title">🤖 How the Pipeline Works</div>
        <div style='display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:1rem; margin-top:0.5rem;'>
            <div style='text-align:center; padding:1rem; background:#080c10; border-radius:8px; border:1px solid #1e2733;'>
                <div style='font-size:1.6rem;'>🔍</div>
                <div style='font-family:"Syne",sans-serif; font-weight:700; font-size:0.8rem; color:#00e5ff; margin:0.4rem 0 0.2rem;'>Agent 1: Scout</div>
                <div style='font-size:0.72rem; color:#64748b;'>Scrapes live jobs via SerpApi Google Jobs engine</div>
            </div>
            <div style='text-align:center; padding:1rem; background:#080c10; border-radius:8px; border:1px solid #1e2733;'>
                <div style='font-size:1.6rem;'>📊</div>
                <div style='font-family:"Syne",sans-serif; font-weight:700; font-size:0.8rem; color:#00e5ff; margin:0.4rem 0 0.2rem;'>Agent 2: Analyst</div>
                <div style='font-size:0.72rem; color:#64748b;'>Scores ATS keyword match 0–100 using Gemini</div>
            </div>
            <div style='text-align:center; padding:1rem; background:#080c10; border-radius:8px; border:1px solid #1e2733;'>
                <div style='font-size:1.6rem;'>✍️</div>
                <div style='font-family:"Syne",sans-serif; font-weight:700; font-size:0.8rem; color:#00e5ff; margin:0.4rem 0 0.2rem;'>Agent 3: Architect</div>
                <div style='font-size:0.72rem; color:#64748b;'>Rewrites resume bullets with JD-matching language</div>
            </div>
            <div style='text-align:center; padding:1rem; background:#080c10; border-radius:8px; border:1px solid #1e2733;'>
                <div style='font-size:1.6rem;'>🎯</div>
                <div style='font-family:"Syne",sans-serif; font-weight:700; font-size:0.8rem; color:#00e5ff; margin:0.4rem 0 0.2rem;'>Agent 4: Coach</div>
                <div style='font-size:0.72rem; color:#64748b;'>Generates 3 role-specific interview questions</div>
            </div>
        </div>
    </div>
    <div style='text-align:center; margin-top:2.5rem; color:#1e2733; font-family:"JetBrains Mono",monospace; font-size:0.75rem;'>
        ← Configure your API keys and upload your resume in the sidebar to begin.
    </div>
    """, unsafe_allow_html=True)
