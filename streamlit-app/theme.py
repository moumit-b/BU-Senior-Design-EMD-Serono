"""
Design Token System — EMD Serono Pharma Research Intelligence
Centralizes all visual design values and generates themed CSS.

Usage:
    import theme
    st.markdown(theme.get_css(st.session_state.get("theme", "dark")), unsafe_allow_html=True)
    st.markdown(theme.get_login_css(st.session_state.get("theme", "dark")), unsafe_allow_html=True)
"""

from dataclasses import dataclass

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap"
)


@dataclass(frozen=True)
class Palette:
    bg_primary: str
    bg_secondary: str
    bg_card: str
    bg_hover: str
    accent: str
    accent_end: str           # gradient end colour
    accent_glow: str          # rgba glow
    text_primary: str
    text_secondary: str
    text_muted: str
    border: str
    border_subtle: str
    success: str
    warning: str
    error: str
    tab_inactive: str


DARK = Palette(
    bg_primary="#080b14",
    bg_secondary="#0f1420",
    bg_card="#131825",
    bg_hover="#1a2035",
    accent="#3a7bd5",
    accent_end="#5b9cf5",
    accent_glow="rgba(58,123,213,0.15)",
    text_primary="#e2e8f0",
    text_secondary="#94a3b8",
    text_muted="#4a5568",
    border="#1e2535",
    border_subtle="#161d2e",
    success="#34d399",
    warning="#f59e0b",
    error="#ef4444",
    tab_inactive="#4a6080",
)

LIGHT = Palette(
    bg_primary="#f0f4f8",
    bg_secondary="#ffffff",
    bg_card="#ffffff",
    bg_hover="#e8eef5",
    accent="#2563eb",
    accent_end="#3b82f6",
    accent_glow="rgba(37,99,235,0.12)",
    text_primary="#1e293b",
    text_secondary="#475569",
    text_muted="#94a3b8",
    border="#dde5ee",
    border_subtle="#e8eef5",
    success="#059669",
    warning="#d97706",
    error="#dc2626",
    tab_inactive="#64748b",
)

_PALETTES = {"dark": DARK, "light": LIGHT}

# ---------------------------------------------------------------------------
# Animations (theme-independent)
# ---------------------------------------------------------------------------

_KEYFRAMES = """
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0);   }
}
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0);     }
}
@keyframes pulseGlow {
    0%, 100% { opacity: 1; transform: scale(1);    }
    50%       { opacity: 0.7; transform: scale(1.2); }
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%;   }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%;   }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
}
@keyframes borderPulse {
    0%, 100% { border-color: #f59e0b; }
    50%       { border-color: #fcd34d; }
}
"""


# ---------------------------------------------------------------------------
# Main CSS generator
# ---------------------------------------------------------------------------

def get_css(theme: str = "dark") -> str:
    """Return full application CSS for the given theme ('dark' or 'light')."""
    p = _PALETTES.get(theme, DARK)
    is_light = theme == "light"

    gradient = f"linear-gradient(135deg, {p.accent}, {p.accent_end})"
    gradient_subtle = f"linear-gradient(135deg, {p.accent}22, {p.accent_end}11)"
    gradient_divider = (
        f"linear-gradient(to right, transparent, {p.border}, transparent)"
    )

    return f"""
<style>
@import url('{FONT_IMPORT}');
{_KEYFRAMES}

/* ── Global ──────────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: {p.bg_primary};
    color: {p.text_primary};
}}
[data-testid="stAppViewContainer"] > .main {{
    background-color: {p.bg_primary};
}}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {p.bg_secondary};
    border-right: 1px solid {p.border};
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: {p.text_primary};
}}
[data-testid="stSidebarContent"] {{
    padding-top: 1.4rem;
}}

/* Sidebar brand */
.sidebar-brand {{
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    background: {gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.15rem;
    animation: fadeIn 0.5s ease forwards;
}}
.sidebar-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: {p.text_primary};
    margin-bottom: 0.25rem;
    line-height: 1.3;
    animation: fadeIn 0.6s ease forwards;
}}
.sidebar-subtitle {{
    font-size: 0.72rem;
    color: {p.text_muted};
    margin-bottom: 1.2rem;
    letter-spacing: 0.03em;
    animation: fadeIn 0.7s ease forwards;
}}

/* Sidebar icon glow */
.sidebar-icon {{
    display: inline-block;
    font-size: 1.5rem;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 0 8px {p.accent}88);
    animation: pulseGlow 3s ease-in-out infinite;
}}

/* LLM status badge */
.llm-status {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.76rem;
    color: {p.text_secondary};
    padding: 5px 10px;
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-radius: 20px;
    margin-top: 0.3rem;
}}
.llm-status .dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
    animation: pulseGlow 2s ease-in-out infinite;
}}
.llm-status .dot.ok  {{ background: {p.success}; box-shadow: 0 0 6px {p.success}88; }}
.llm-status .dot.err {{ background: {p.error};   box-shadow: 0 0 6px {p.error}88; }}

/* Sidebar history label */
.hist-label {{
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {p.text_muted};
    margin: 0.7rem 0 0.4rem;
}}

/* Session items in sidebar */
.session-item {{
    border-left: 2px solid transparent;
    padding-left: 6px;
    transition: border-color 0.2s, background 0.2s;
    border-radius: 0 4px 4px 0;
    animation: slideIn 0.3s ease forwards;
}}
.session-item:hover {{
    border-left-color: {p.accent};
    background: {p.accent_glow};
}}
.session-item.active {{
    border-left: 2px solid;
    border-image: {gradient} 1;
}}

/* Gradient divider */
.gradient-divider {{
    height: 1px;
    background: {gradient_divider};
    margin: 0.8rem 0;
    border: none;
}}

/* ── Main area ───────────────────────────────────────────────────────────── */
.main .block-container {{
    padding-top: 1.6rem;
    max-width: 1320px;
}}

/* Page header */
.page-header {{
    display: flex;
    align-items: baseline;
    gap: 0.9rem;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid {p.border};
    padding-bottom: 1rem;
    animation: fadeIn 0.4s ease forwards;
}}
.page-header h1 {{
    font-size: 1.4rem;
    font-weight: 600;
    background: {gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -0.01em;
}}
.page-header .sub {{
    font-size: 0.78rem;
    color: {p.text_muted};
    font-weight: 400;
}}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: transparent;
    gap: 0;
    border-bottom: 1px solid {p.border};
    margin-bottom: 1.2rem;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.83rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: {p.tab_inactive};
    padding: 0.55rem 1.2rem;
    border-bottom: 2px solid transparent;
    background: transparent;
    border-radius: 0;
    transition: color 0.2s, border-color 0.2s, background 0.2s;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {p.accent_end} !important;
    border-bottom: 2px solid {p.accent} !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
    color: {p.accent_end} !important;
    background: {p.accent_glow} !important;
}}

/* ── Chat messages ───────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {{
    border-radius: 8px;
    padding: 0.4rem 0.2rem;
    margin-bottom: 0.3rem;
    transition: background 0.2s;
    animation: fadeIn 0.35s ease forwards;
}}
[data-testid="stChatMessage"][data-testid*="user"] {{
    background: {p.accent_glow};
    border-left: 3px solid {p.accent};
    padding-left: 0.8rem;
}}
[data-testid="stChatMessage"][data-testid*="assistant"] {{
    background: {p.bg_card};
    border: 1px solid {p.border_subtle};
    border-left: 3px solid {p.accent_end};
    padding-left: 0.8rem;
}}

/* Chat input */
[data-testid="stChatInput"] {{
    border-color: {p.border} !important;
    background: {p.bg_card} !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: {p.accent} !important;
    box-shadow: 0 0 0 2px {p.accent_glow} !important;
}}

/* ── Metrics ─────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-top: 3px solid;
    border-image: {gradient} 1;
    border-radius: 0 0 8px 8px;
    padding: 0.9rem 1rem;
    box-shadow: 0 2px 8px {p.accent_glow};
    animation: fadeIn 0.4s ease forwards;
    transition: transform 0.2s, box-shadow 0.2s;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px {p.accent_glow};
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.7rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {p.text_muted} !important;
    font-weight: 600;
}}
[data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.5rem !important;
    color: {p.text_primary} !important;
}}

/* ── Expanders ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {p.border} !important;
    border-radius: 8px !important;
    background: {p.bg_card} !important;
    transition: border-color 0.2s;
}}
[data-testid="stExpander"]:hover {{
    border-color: {p.accent}66 !important;
}}
[data-testid="stExpander"] summary {{
    font-size: 0.82rem !important;
    color: {p.text_secondary} !important;
    font-weight: 500 !important;
}}

/* Agent reasoning expander — blue→teal gradient left border */
.reasoning-expander {{
    border-left: 3px solid !important;
    border-image: linear-gradient(to bottom, {p.accent}, {p.success}) 1 !important;
    background: {p.bg_card} !important;
    border-radius: 0 8px 8px 0 !important;
}}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {{
    background: {gradient} !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 500;
    letter-spacing: 0.03em;
    border-radius: 6px !important;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
    box-shadow: 0 2px 8px {p.accent}44;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 18px {p.accent}66 !important;
    opacity: 0.92;
}}
[data-testid="stButton"] button[kind="primary"]:active {{
    transform: translateY(0);
}}
[data-testid="stButton"] button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid {p.border} !important;
    color: {p.text_secondary} !important;
    border-radius: 6px !important;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
}}
[data-testid="stButton"] button[kind="secondary"]:hover {{
    border-color: {p.accent} !important;
    color: {p.accent_end} !important;
    background: {p.accent_glow} !important;
}}

/* ── Inputs & Selects ────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] textarea {{
    background: {p.bg_card} !important;
    border-color: {p.border} !important;
    color: {p.text_primary} !important;
    border-radius: 6px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextInput"] textarea:focus {{
    border-color: {p.accent} !important;
    box-shadow: 0 0 0 2px {p.accent_glow} !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background: {p.bg_card} !important;
    border-color: {p.border} !important;
    color: {p.text_primary} !important;
    border-radius: 6px !important;
}}
[data-testid="stSelectbox"] label {{
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {p.text_muted} !important;
    font-weight: 600;
}}

/* ── Alerts ──────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 8px;
    font-size: 0.85rem;
    border-left-width: 4px !important;
}}

/* Anomaly alert banner — pulsing border */
.anomaly-alert {{
    border: 1px solid {p.warning};
    border-left: 4px solid {p.warning};
    border-radius: 8px;
    background: {p.warning}18;
    padding: 0.8rem 1rem;
    animation: borderPulse 2s ease-in-out infinite;
}}

/* ── Drug / Hallucination badges ─────────────────────────────────────────── */
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}}
.badge-drug {{
    background: {gradient};
    color: #ffffff;
    box-shadow: 0 2px 8px {p.accent}44;
}}
.badge-success {{
    background: {p.success}22;
    color: {p.success};
    border: 1px solid {p.success}44;
}}
.badge-warning {{
    background: {p.warning}22;
    color: {p.warning};
    border: 1px solid {p.warning}44;
}}
.badge-error {{
    background: {p.error}22;
    color: {p.error};
    border: 1px solid {p.error}44;
}}

/* ── Report container ────────────────────────────────────────────────────── */
.report-card {{
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-radius: 10px;
    box-shadow: 0 4px 16px {p.accent_glow};
    padding: 1.2rem 1.4rem;
}}
.report-card h1, .report-card h2, .report-card h3 {{
    background: {gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.report-card table {{
    border-collapse: collapse;
    width: 100%;
}}
.report-card th {{
    background: {p.accent}22;
    border-bottom: 2px solid {p.accent};
    font-size: 0.8rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.5rem 0.8rem;
    color: {p.text_secondary};
}}
.report-card td {{
    border-bottom: 1px solid {p.border_subtle};
    padding: 0.45rem 0.8rem;
    font-size: 0.88rem;
}}
.report-card tr:hover td {{
    background: {p.bg_hover};
}}

/* ── Verification cards ──────────────────────────────────────────────────── */
.verify-card {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.6rem 0.8rem;
    margin: 0.3rem 0;
    border-radius: 6px;
    border: 1px solid {p.border};
    background: {p.bg_card};
    font-size: 0.83rem;
    animation: fadeIn 0.3s ease forwards;
    transition: transform 0.15s;
}}
.verify-card:hover {{
    transform: translateX(3px);
}}
.verify-ok  {{ border-left: 3px solid {p.success}; }}
.verify-warn {{ border-left: 3px solid {p.warning}; }}
.verify-err  {{ border-left: 3px solid {p.error};   }}
.verify-icon {{ font-size: 1rem; flex-shrink: 0; margin-top: 1px; }}

/* ── Past report cards ───────────────────────────────────────────────────── */
.report-row {{
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    transition: transform 0.15s, border-color 0.2s, box-shadow 0.2s;
    animation: fadeIn 0.35s ease forwards;
}}
.report-row:hover {{
    transform: translateY(-2px);
    border-color: {p.accent}66;
    box-shadow: 0 4px 14px {p.accent_glow};
}}

/* ── Governance timeline ─────────────────────────────────────────────────── */
.timeline {{
    position: relative;
    padding-left: 20px;
}}
.timeline::before {{
    content: '';
    position: absolute;
    left: 6px;
    top: 0;
    bottom: 0;
    width: 1px;
    background: {gradient_divider};
}}
.timeline-item {{
    position: relative;
    padding: 0.5rem 0.8rem 0.5rem 1rem;
    margin: 0.3rem 0;
    border-radius: 0 6px 6px 0;
    background: {p.bg_card};
    border: 1px solid {p.border_subtle};
    border-left: none;
    font-size: 0.82rem;
    color: {p.text_secondary};
    transition: background 0.15s;
    animation: slideIn 0.3s ease forwards;
}}
.timeline-item:hover {{
    background: {p.bg_hover};
}}
.timeline-dot {{
    position: absolute;
    left: -17px;
    top: 50%;
    transform: translateY(-50%);
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: {p.accent};
    box-shadow: 0 0 6px {p.accent}88;
    flex-shrink: 0;
}}
.timeline-dot.ok  {{ background: {p.success}; box-shadow: 0 0 6px {p.success}88; }}
.timeline-dot.err {{ background: {p.error};   box-shadow: 0 0 6px {p.error}88; }}

/* Health indicator cards */
.health-card {{
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-radius: 8px;
    padding: 0.7rem 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0.3rem 0;
    transition: border-color 0.2s;
    animation: fadeIn 0.4s ease forwards;
}}
.health-card.healthy {{ border-left: 3px solid {p.success}; }}
.health-card.unhealthy {{ border-left: 3px solid {p.error}; }}
.health-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    animation: pulseGlow 2s ease-in-out infinite;
}}
.health-dot.ok  {{ background: {p.success}; box-shadow: 0 0 8px {p.success}88; }}
.health-dot.err {{ background: {p.error};   box-shadow: 0 0 8px {p.error}88; }}

/* ── Shimmer loading indicator ───────────────────────────────────────────── */
.shimmer {{
    background: linear-gradient(
        90deg,
        {p.bg_card} 25%,
        {p.accent_glow} 50%,
        {p.bg_card} 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: 4px;
    height: 6px;
    margin: 0.5rem 0;
}}

/* ── Dataframe / tables ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {p.border};
    border-radius: 8px;
    overflow: hidden;
}}

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {p.bg_primary}; }}
::-webkit-scrollbar-thumb {{ background: {p.border}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {p.accent}88; }}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {{ border-color: {p.border} !important; }}

/* ── Download buttons ────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button {{
    background: {p.bg_card} !important;
    border: 1px solid {p.border} !important;
    color: {p.text_secondary} !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
}}
[data-testid="stDownloadButton"] button:hover {{
    border-color: {p.accent} !important;
    color: {p.accent_end} !important;
    background: {p.accent_glow} !important;
}}

/* ── Staggered animation helpers ─────────────────────────────────────────── */
.anim-d1 {{ animation-delay: 0.05s; }}
.anim-d2 {{ animation-delay: 0.10s; }}
.anim-d3 {{ animation-delay: 0.15s; }}
.anim-d4 {{ animation-delay: 0.20s; }}
.anim-d5 {{ animation-delay: 0.25s; }}

/* ── Theme toggle button ─────────────────────────────────────────────────── */
.theme-toggle {{
    background: {p.bg_card};
    border: 1px solid {p.border};
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 0.8rem;
    color: {p.text_secondary};
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
}}
.theme-toggle:hover {{
    border-color: {p.accent};
    background: {p.accent_glow};
}}

/* ── Hide Streamlit branding ─────────────────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
"""


def get_login_css(theme: str = "dark") -> str:
    """Return login-page-specific CSS for the given theme."""
    p = _PALETTES.get(theme, DARK)
    gradient = f"linear-gradient(135deg, {p.accent}, {p.accent_end})"

    if theme == "dark":
        bg_gradient = f"linear-gradient(135deg, #060912 0%, #0a1020 30%, #080b18 60%, #060a14 100%)"
        card_bg = "rgba(13,18,32,0.88)"
        card_border = f"rgba(58,123,213,0.22)"
    else:
        bg_gradient = f"linear-gradient(135deg, #dde8f5 0%, #eef4fd 40%, #e4edf9 70%, #d8e6f4 100%)"
        card_bg = "rgba(255,255,255,0.92)"
        card_border = f"rgba(37,99,235,0.2)"

    return f"""
<style>
@import url('{FONT_IMPORT}');
@keyframes gradientShift {{
    0%   {{ background-position: 0% 50%;   }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%;   }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to   {{ opacity: 1; transform: translateY(0);    }}
}}
@keyframes floatIcon {{
    0%, 100% {{ transform: translateY(0); }}
    50%       {{ transform: translateY(-4px); }}
}}

[data-testid="stAppViewContainer"] {{
    background: {bg_gradient};
    background-size: 300% 300%;
    animation: gradientShift 18s ease infinite;
    font-family: 'IBM Plex Sans', sans-serif;
}}
[data-testid="stAppViewContainer"] > .main {{
    background: transparent;
}}

.login-card {{
    max-width: 440px;
    margin: 60px auto 0;
    padding: 2.8rem 2.4rem;
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 16px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 24px 64px rgba(0,0,0,0.35), 0 0 0 1px {card_border};
    animation: fadeInUp 0.7s cubic-bezier(0.22,1,0.36,1) forwards;
}}
.login-icon {{
    font-size: 2.4rem;
    display: block;
    text-align: center;
    margin-bottom: 0.6rem;
    filter: drop-shadow(0 0 12px {p.accent}99);
    animation: floatIcon 3s ease-in-out infinite;
}}
.login-brand {{
    text-align: center;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    background: {gradient};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
}}
.login-title {{
    text-align: center;
    font-size: 1.5rem;
    font-weight: 700;
    color: {p.text_primary};
    margin: 0 0 0.2rem;
    letter-spacing: -0.02em;
}}
.login-subtitle {{
    text-align: center;
    font-size: 0.82rem;
    color: {p.text_muted};
    margin-bottom: 2rem;
}}
.login-divider {{
    height: 1px;
    background: linear-gradient(to right, transparent, {p.border}, transparent);
    margin: 1.4rem 0;
}}
.login-footer {{
    text-align: center;
    font-size: 0.72rem;
    color: {p.text_muted};
    margin-top: 1.4rem;
    letter-spacing: 0.04em;
}}

/* Input fields */
[data-testid="stTextInput"] input {{
    background: {"rgba(8,11,20,0.6)" if theme == "dark" else "rgba(248,250,252,0.9)"} !important;
    border-color: {p.border} !important;
    color: {p.text_primary} !important;
    border-radius: 8px !important;
    padding: 0.65rem 0.9rem !important;
    font-size: 0.92rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {p.accent} !important;
    box-shadow: 0 0 0 3px {p.accent_glow} !important;
}}

/* Sign In button */
[data-testid="stButton"] button[kind="primary"] {{
    background: linear-gradient(135deg, {p.accent} 0%, {p.accent_end} 100%) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    border-radius: 8px !important;
    padding: 0.7rem !important;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s !important;
    box-shadow: 0 4px 14px {p.accent}55 !important;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px {p.accent}88 !important;
    opacity: 0.93 !important;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stSidebar"] {{ display: none !important; }}
</style>
"""
