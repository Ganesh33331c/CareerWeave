"""
components.py — CareerWeave Custom HTML Components
===================================================
Reusable HTML/CSS snippets injected into the Streamlit app via
st.markdown(..., unsafe_allow_html=True).

Usage in app.py:
    from components import (
        render_hero,
        render_agent_status,
        render_job_card,
        render_ats_score,
        render_interview_question,
        render_skill_gap_pill,
        render_pipeline_idle,
        render_footer,
    )
"""


def render_hero() -> str:
    """
    Full hero header with grid background, gradient title, and badge.
    Returns raw HTML string for st.markdown().
    """
    return """
    <div style="
        background: linear-gradient(135deg, #080c10 0%, #0d1a2e 50%, #0a0f16 100%);
        border: 1px solid #1e2733;
        border-radius: 14px;
        padding: 2.6rem 3rem 2.2rem;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
    ">
        <!-- Grid texture -->
        <div style="
            position:absolute; inset:0; pointer-events:none;
            background:
                repeating-linear-gradient(0deg, transparent, transparent 39px, #1e273318 39px, #1e273318 40px),
                repeating-linear-gradient(90deg, transparent, transparent 39px, #1e273318 39px, #1e273318 40px);
        "></div>

        <!-- Hackathon badge -->
        <div style="
            display:inline-block;
            background: linear-gradient(90deg, #6d28d9, #00e5ff);
            color:#fff;
            font-family:'Syne',sans-serif;
            font-size:0.62rem; font-weight:700;
            letter-spacing:0.14em; text-transform:uppercase;
            padding:3px 12px; border-radius:20px;
            margin-bottom:1rem; position:relative;
        ">GEN AI APAC Hackathon · Multi-Agent Pipeline</div>

        <!-- Title -->
        <div style="
            font-family:'Syne',sans-serif;
            font-size:clamp(2.2rem, 5vw, 3rem);
            font-weight:800; letter-spacing:-1.5px;
            background:linear-gradient(90deg, #00e5ff, #6d28d9);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin-bottom:0.4rem; position:relative;
        ">🕸️ CareerWeave</div>

        <!-- Subtitle -->
        <div style="
            font-family:'Syne',sans-serif;
            font-size:1.05rem; font-weight:600;
            color:#dde6f0; margin-bottom:0.35rem; position:relative;
        ">Multi-Agent Job Orchestrator</div>

        <!-- Tagline -->
        <div style="
            font-family:'Fragment Mono',monospace;
            font-size:0.8rem; color:#4a6278;
            letter-spacing:0.04em; position:relative;
        ">
            Weaving your profile, live job data, and interview prep into one seamless pipeline.
        </div>
    </div>
    """


def render_agent_status(agent_num: int, name: str, description: str, active: bool = True) -> str:
    """
    Animated agent status row shown during pipeline execution.
    
    Args:
        agent_num:   1–4
        name:        Agent name, e.g. "Scout"
        description: What it's doing, e.g. "Scanning live job market via SerpApi…"
        active:      If True, shows pulsing cyan dot. If False, shows green checkmark.
    """
    if active:
        indicator = """
        <div style="
            width:8px; height:8px; border-radius:50%;
            background:#00e5ff; box-shadow:0 0 8px #00e5ff;
            animation:cwPulse 1.2s infinite; flex-shrink:0;
        "></div>
        <style>
            @keyframes cwPulse { 0%,100%{opacity:1} 50%{opacity:0.2} }
        </style>
        """
        name_color = "#00e5ff"
    else:
        indicator = '<div style="color:#22d3a5; font-size:1rem; flex-shrink:0;">✓</div>'
        name_color = "#22d3a5"

    return f"""
    <div style="
        display:flex; align-items:center; gap:10px;
        padding:0.6rem 1rem; border-radius:8px;
        background:#0d1117; border:1px solid #1e2733;
        margin-bottom:0.5rem;
        font-family:'Fragment Mono',monospace; font-size:0.8rem;
    ">
        {indicator}
        <span style="color:{name_color}; font-weight:600;">Agent {agent_num}: {name}</span>
        <span style="color:#4a6278;">— {description}</span>
    </div>
    """


def render_job_card(title: str, company: str, location: str, link: str) -> str:
    """
    Highlighted job result card with cyan border and company details.
    """
    # Truncate long titles
    title_display   = title[:70]   + "…" if len(title) > 70   else title
    company_display = company[:50] + "…" if len(company) > 50 else company

    return f"""
    <div style="
        background: linear-gradient(135deg, #0d1117, #0d1a2e);
        border: 1px solid #00e5ff;
        border-radius: 12px;
        padding: 1.4rem 1.8rem;
        margin-bottom: 1rem;
    ">
        <div style="font-size:0.68rem; color:#4a6278; letter-spacing:.12em; text-transform:uppercase; margin-bottom:0.4rem;">
            🔍 Top Matched Role
        </div>
        <div style="font-family:'Syne',sans-serif; font-size:1.25rem; font-weight:700; color:#dde6f0; margin-bottom:0.25rem;">
            {title_display}
        </div>
        <div style="font-family:'Fragment Mono',monospace; font-size:0.82rem; color:#00e5ff; margin-bottom:0.6rem;">
            ⚡ {company_display} · {location}
        </div>
        <div>
            <a href="{link}" target="_blank"
               style="color:#6d28d9; font-family:'Fragment Mono',monospace; font-size:0.75rem; text-decoration:none;">
                🔗 View Full Listing →
            </a>
        </div>
    </div>
    """


def render_ats_score(score: int, reasoning: str = "") -> str:
    """
    ATS score display with colour-coded tier label and reasoning text.
    Uses st.progress() separately for the actual bar.
    """
    score = max(0, min(100, int(score)))

    if score >= 75:
        color = "#22d3a5"
        tier  = "STRONG MATCH"
        bg    = "rgba(34,211,165,0.07)"
        brd   = "rgba(34,211,165,0.25)"
    elif score >= 50:
        color = "#f59e0b"
        tier  = "PARTIAL MATCH"
        bg    = "rgba(245,158,11,0.07)"
        brd   = "rgba(245,158,11,0.25)"
    else:
        color = "#ef4444"
        tier  = "LOW MATCH"
        bg    = "rgba(239,68,68,0.07)"
        brd   = "rgba(239,68,68,0.25)"

    reasoning_html = f"""
    <div style="font-family:'Fragment Mono',monospace; font-size:0.72rem;
                color:#4a6278; margin-top:0.8rem; line-height:1.7;">
        {reasoning}
    </div>
    """ if reasoning else ""

    return f"""
    <div style="
        background: #0d1117; border: 1px solid #1e2733;
        border-radius: 12px; padding: 1.4rem 1.6rem; text-align:center;
    ">
        <div style="font-family:'Fragment Mono',monospace; font-size:0.68rem;
                    color:#4a6278; letter-spacing:.12em; text-transform:uppercase;
                    margin-bottom:0.5rem;">
            ATS Match Score
        </div>
        <div style="font-family:'Syne',sans-serif; font-size:2.4rem;
                    font-weight:800; color:{color}; line-height:1;">
            {score}%
        </div>
        <div style="
            display:inline-block;
            margin-top:0.5rem; padding:2px 10px; border-radius:20px;
            background:{bg}; border:1px solid {brd};
            font-family:'Syne',sans-serif; font-size:0.68rem; font-weight:700;
            letter-spacing:.1em; color:{color};
        ">
            {tier}
        </div>
        {reasoning_html}
    </div>
    """


def render_interview_question(num: int, question: str, why_asked: str = "", answer_tip: str = "") -> str:
    """
    Interview question card with violet left border, hint, and tip.
    """
    why_html = f"""
    <div style="margin-top:0.55rem; font-size:0.73rem; color:#4a6278; line-height:1.6;">
        💡 <em>{why_asked}</em>
    </div>
    """ if why_asked else ""

    tip_html = f"""
    <div style="margin-top:0.35rem; font-size:0.73rem; color:#22d3a5; line-height:1.6;">
        🎯 {answer_tip}
    </div>
    """ if answer_tip else ""

    return f"""
    <div style="
        background: #03080f;
        border-left: 3px solid #6d28d9;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.3rem;
        margin-bottom: 0.8rem;
        font-family: 'Fragment Mono', monospace;
        font-size: 0.82rem;
        line-height: 1.7;
    ">
        <div>
            <span style="color:#6d28d9; font-weight:600; margin-right:6px;">Q{num}.</span>
            {question}
        </div>
        {why_html}
        {tip_html}
    </div>
    """


def render_skill_gap_pill(skill: str) -> str:
    """
    Red skill gap pill for the skills gap section.
    """
    return f"""
    <div style="
        background:#1a0a0a; border:1px solid #ef4444;
        border-radius:8px; padding:0.65rem 1rem; text-align:center;
        font-family:'Syne',sans-serif; font-size:0.8rem; font-weight:700;
        color:#ef4444;
    ">
        ⚠️ {skill}
    </div>
    """


def render_pipeline_idle() -> str:
    """
    Four-panel idle state showing the pipeline diagram before the user runs it.
    Displayed when no results are available yet.
    """
    agents = [
        ("🔍", "Scout",     "Scrapes live jobs via SerpApi Google Jobs engine"),
        ("📊", "Analyst",   "Scores ATS keyword match 0–100 using Gemini"),
        ("✍️", "Architect", "Rewrites resume bullets with JD-matching language"),
        ("🎯", "Coach",     "Generates 3 role-specific interview questions"),
    ]

    cards_html = ""
    for icon, name, desc in agents:
        cards_html += f"""
        <div style="
            text-align:center; padding:1.2rem 0.8rem;
            background:#03080f; border-radius:10px;
            border:1px solid #1e2733;
        ">
            <div style="font-size:1.6rem; margin-bottom:0.5rem;">{icon}</div>
            <div style="font-family:'Syne',sans-serif; font-weight:700;
                        font-size:0.82rem; color:#00e5ff; margin-bottom:0.3rem;">
                {name}
            </div>
            <div style="font-family:'Fragment Mono',monospace; font-size:0.7rem; color:#4a6278; line-height:1.6;">
                {desc}
            </div>
        </div>
        """

    return f"""
    <div style="
        background:#0d1117; border:1px solid #1e2733;
        border-radius:12px; padding:1.8rem 2rem; margin-top:0.5rem;
    ">
        <div style="
            font-family:'Fragment Mono',monospace; font-size:0.68rem;
            letter-spacing:.18em; text-transform:uppercase;
            color:#00e5ff; margin-bottom:1.2rem;
        ">🤖 Pipeline Architecture</div>

        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:1rem;">
            {cards_html}
        </div>
    </div>

    <div style="
        text-align:center; margin-top:2.4rem;
        color:#1e2733; font-family:'Fragment Mono',monospace; font-size:0.73rem;
    ">
        ← Configure API keys and upload your resume in the sidebar, then click Deploy.
    </div>
    """


def render_section_header(title: str, accent: bool = True) -> str:
    """
    Consistent section header with cyan top bar.
    """
    border = "border-top: 2px solid #00e5ff;" if accent else ""
    return f"""
    <div style="
        font-family:'Fragment Mono',monospace; font-size:0.68rem;
        letter-spacing:.18em; text-transform:uppercase;
        color:#00e5ff; padding-top:0.8rem;
        margin-bottom:0.8rem; {border}
        padding-bottom:0.6rem; border-bottom:1px solid #1e2733;
    ">
        {title}
    </div>
    """


def render_footer() -> str:
    """
    Subtle footer for the bottom of the Streamlit app.
    """
    return """
    <div style="
        text-align:center;
        font-family:'Fragment Mono',monospace;
        font-size:0.68rem; color:#1e2733;
        padding:1.5rem 0 0.5rem;
        border-top:1px solid #1e2733;
        margin-top:1.5rem;
    ">
        CareerWeave · GEN AI APAC Hackathon · Powered by Gemini + SerpApi + LangChain + Cloud Run
    </div>
    """
