# Professional UI Redesign — EMD Serono Pharma Research Intelligence

**Date:** 2026-04-29
**Branch:** `mb-professional-ui-redesign` (off `rohan_newfeatures`)
**Audience:** Scientists & researchers (primary), business stakeholders (secondary)

## Context

The Streamlit app currently has a functional dark UI with hardcoded CSS in `app.py`'s `_inject_css()`. It works but looks raw — no design tokens, no `.streamlit/config.toml`, no animations, no gradients, and native Streamlit widgets clash with the custom dark CSS. The goal is to elevate it to a professional-grade pharma platform that impresses stakeholders without compromising technical depth.

Additionally, a `ModuleNotFoundError: No module named 'psycopg2'` blocks app startup when `SUPABASE_DB_URL` is set.

## Bug Fix: psycopg2

- Install `psycopg2-binary` via pip (already listed in `requirements.txt` but not installed in active env)
- Add `scikit-learn` to `requirements.txt` (missing dependency for Rohan's `anomaly_detector.py`)

## Design Token System

### New file: `streamlit-app/theme.py`

Centralized module holding all design values and generating CSS for the active theme.

**Palettes:**

| Token | Dark | Light |
|-------|------|-------|
| `bg_primary` | `#080b14` | `#f8fafc` |
| `bg_secondary` | `#0f1420` | `#ffffff` |
| `bg_card` | `#131825` | `#ffffff` |
| `bg_hover` | `#1a2035` | `#f1f5f9` |
| `accent_primary` | `#3a7bd5` | `#2563eb` |
| `accent_gradient` | `linear-gradient(135deg, #3a7bd5, #5b9cf5)` | `linear-gradient(135deg, #2563eb, #3b82f6)` |
| `accent_glow` | `rgba(58,123,213,0.15)` | `rgba(37,99,235,0.1)` |
| `text_primary` | `#e2e8f0` | `#1e293b` |
| `text_secondary` | `#94a3b8` | `#475569` |
| `text_muted` | `#4a5568` | `#94a3b8` |
| `border` | `#1e2535` | `#e2e8f0` |
| `success` | `#34d399` | `#10b981` |
| `warning` | `#f59e0b` | `#d97706` |
| `error` | `#ef4444` | `#dc2626` |

**Animations:**
- `fadeIn` — 0.4s ease, `opacity:0 translateY(8px)` → visible. Used on page load elements.
- `pulseGlow` — 2s infinite, subtle scale/opacity pulse for status indicators.
- `slideIn` — 0.3s ease, `translateX(-10px)` → visible. Used on sidebar chat history items.
- `gradientShift` — 15s infinite, subtle background gradient movement on login page.
- `shimmer` — loading indicator for report generation.

**Typography** (unchanged, IBM Plex Sans/Mono is excellent):
- Headings: IBM Plex Sans 600
- Body: IBM Plex Sans 400
- Mono: IBM Plex Mono 400/500

**Public API:**
- `get_css(theme: str) -> str` — returns full CSS for "dark" or "light"
- `get_login_css(theme: str) -> str` — returns login-specific CSS
- `DARK` / `LIGHT` — palette dataclasses for programmatic access

### New file: `streamlit-app/.streamlit/config.toml`

Native Streamlit theme config so built-in widgets match:

```toml
[theme]
primaryColor = "#3a7bd5"
backgroundColor = "#080b14"
secondaryBackgroundColor = "#0f1420"
textColor = "#e2e8f0"
font = "sans serif"
```

Note: This sets the dark theme as default. Light mode is handled via CSS injection (Streamlit doesn't support runtime theme switching natively).

## Component Designs

### Login Page (`auth.py` + `app.py`)

- Background: Animated gradient (`gradientShift`), dark navy shifting between `#080b14` and `#0d1220`
- Card: Frosted glass (`backdrop-filter: blur(12px)`, `rgba(15,20,32,0.85)` bg, `rgba(58,123,213,0.2)` border)
- Wordmark: "EMD Serono" — IBM Plex Sans 600, `letter-spacing: 0.2em`, hexagon accent with glow
- Subtitle: "Pharma Research Intelligence Platform" in `text_secondary`
- Inputs: Rounded, inner glow on focus (`box-shadow: 0 0 0 2px rgba(58,123,213,0.3)`)
- Button: Gradient bg (`accent_gradient`), hover lift (`translateY(-1px)`, expanded shadow)
- Fade-in: Card appears with `fadeIn` animation (0.6s)

### Sidebar

- Brand: Hexagon with `pulseGlow`, "EMD SERONO" wordmark, "Research Intelligence" subtitle, all with `fadeIn`
- Theme toggle: Sun/moon icon button, top-right corner of sidebar
- Config select: Custom border + focus glow
- LLM status: Gradient pill badge, animated pulse dot for "Ready"
- Chat history: Card-like rows with left accent border (active = gradient blue, hover = bg shift), `slideIn` on render
- New Conversation: Gradient bg button with hover glow
- Dividers: Gradient lines (`linear-gradient(to right, transparent, border_color, transparent)`)
- User section: Clean typography, sign-out with hover state

### Research Tab (Chat)

- User messages: Subtle gradient left-border accent, slightly elevated bg card
- Assistant messages: Clean card with thin border
- Agent reasoning expander: Dark card with blue→teal gradient left-border, styled code blocks
- Chat input: Glow focus state matching accent
- Loading: Pulsing accent dots or gradient shimmer bar (replaces default spinner text)

### Reports Tab

- Drug badge: Gradient pill replacing plain `st.success`
- Report container: Card with subtle shadow, better markdown typography (accent-colored headings, styled tables)
- Hallucination rate: Color-coded gradient pills (green→yellow→red)
- Anomaly alert: Styled warning banner with animated left-border pulse
- Verification expander: Cards per identifier with status icons, color-coded
- Past reports: Card rows with hover lift effect
- Download buttons: Styled with hover gradient

### Tool Metrics Tab

- Summary cards: Gradient top-border accent, subtle shadow, staggered `fadeIn` on load
- Data table: Custom alternating row bg, header gradient
- Bar chart: Matches theme colors

### Governance Tab

- Health indicators: Animated green/red dots with `pulseGlow`, card layout
- Compliance violations: Warning cards with severity coloring
- Audit log: Timeline-style with connected dots (replaces flat list)
- Rate limiting: Metric cards matching overall design

## Files to Modify

| File | Change |
|------|--------|
| `streamlit-app/theme.py` | **NEW** — design tokens, palette, CSS generation |
| `streamlit-app/.streamlit/config.toml` | **NEW** — native Streamlit theme |
| `streamlit-app/app.py` | Replace `_inject_css()` with `theme.get_css()`, add theme toggle, update sidebar HTML |
| `streamlit-app/auth.py` | Upgrade login page styling to frosted glass card |
| `streamlit-app/ui/report_panel.py` | Styled hallucination badges, past report cards, verification cards |
| `streamlit-app/ui/tool_metrics_tab.py` | Metric card styling, table polish |
| `streamlit-app/ui/governance_tab.py` | Timeline audit log, health indicator cards |
| `streamlit-app/requirements.txt` | Add `scikit-learn` |

## Files NOT Modified

- `streamlit-app/context/database.py` — no changes needed
- `streamlit-app/context/db_models.py` — no changes
- `streamlit-app/agent.py` — no changes
- `streamlit-app/utils/hallucination_checker.py` — no changes
- `streamlit-app/utils/anomaly_detector.py` — no changes
- Any MCP server code

## Verification Plan

1. `pip install psycopg2-binary scikit-learn` — confirm no import errors
2. `streamlit run app.py` — app launches without errors
3. Verify login page renders with frosted glass card and gradient background
4. Login → verify sidebar brand, theme toggle, chat history styling
5. Toggle light/dark mode — verify all components switch cleanly
6. Research tab: send a query, verify message bubble styling and agent reasoning display
7. Reports tab: generate a report, verify hallucination badges and verification cards
8. Tool Metrics tab: verify metric cards and table styling
9. Governance tab: verify timeline audit log and health indicators
10. Check that Rohan's hallucination checker and anomaly detection features still work correctly
