"""
Tool Catalog Tab UI

Displays all 146 MCP tools grouped by category with live availability
indicators cross-referenced against the active MCP wrapper initialization.
"""

import os
import streamlit as st
import pandas as pd
import theme as _theme

_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tool_catalog.csv")

_CAT_ICONS = {
    "Analysis Tools": "🔬",
    "General Web and Reasoning": "🌐",
    "Targets and Proteins": "🧬",
    "Compounds and Drugs": "💊",
    "Clinical Trials": "🏥",
    "Literature and Preprints": "📄",
    "Safety and FDA": "🛡️",
    "Diseases and Evidence": "🩺",
    "Assays and Bioassays": "⚗️",
    "Networks and Pathways": "🕸️",
    "Knowledge and Ontologies": "📚",
}

# Category display order (most broadly useful first)
_CAT_ORDER = [
    "General Web and Reasoning",
    "Analysis Tools",
    "Compounds and Drugs",
    "Targets and Proteins",
    "Clinical Trials",
    "Diseases and Evidence",
    "Literature and Preprints",
    "Safety and FDA",
    "Assays and Bioassays",
    "Networks and Pathways",
    "Knowledge and Ontologies",
]


@st.cache_data
def _load_catalog() -> pd.DataFrame:
    df = pd.read_csv(_CATALOG_PATH)
    df.columns = ["tool_name", "categories_raw", "description"]
    df["categories"] = df["categories_raw"].apply(
        lambda x: [c.strip() for c in str(x).split(",")]
    )
    return df


def _get_loaded_tools(active_wrappers: dict) -> set:
    loaded: set = set()
    for wrapper in active_wrappers.values():
        for tool in getattr(wrapper, "_tools_cache", []):
            loaded.add(tool.name)
    return loaded


def _render_tool_card(tool: pd.Series, loaded_tools: set, p: _theme.Palette) -> None:
    is_avail = tool["tool_name"] in loaded_tools
    dot_cls = "ok" if is_avail else "off"
    status_text = "Available" if is_avail else "Not Loaded"
    status_color = p.success if is_avail else p.text_muted

    cat_badges = "".join(
        f"<span class='cat-badge'>{cat}</span>"
        for cat in tool["categories"]
    )

    st.markdown(
        f"<div class='tool-card'>"
        f"  <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem'>"
        f"    <span class='tool-name'>{tool['tool_name']}</span>"
        f"    <span class='tool-avail-row' style='flex-shrink:0'>"
        f"      <span class='avail-dot-inline {dot_cls}'></span>"
        f"      <span style='font-size:0.72rem;color:{status_color};white-space:nowrap'>{status_text}</span>"
        f"    </span>"
        f"  </div>"
        f"  <p class='tool-desc'>{tool['description']}</p>"
        f"  <div style='display:flex;flex-wrap:wrap;gap:2px'>{cat_badges}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_tool_catalog(active_wrappers: dict) -> None:
    """Render the Tool Catalog tab content."""
    p = _theme._PALETTES.get(st.session_state.get("theme", "dark"), _theme.DARK)
    gradient = f"linear-gradient(135deg, {p.accent}, {p.accent_end})"

    # Load data
    try:
        df = _load_catalog()
    except Exception as e:
        st.error(f"Could not load tool catalog: {e}")
        return

    loaded_tools = _get_loaded_tools(active_wrappers)

    total = len(df)
    available = sum(1 for name in df["tool_name"] if name in loaded_tools)
    avail_pct = round(available / total * 100) if total else 0

    all_cats_raw = sorted({cat for cats in df["categories"] for cat in cats})
    # Order by preferred order, then alphabetically for unknowns
    all_cats = [c for c in _CAT_ORDER if c in all_cats_raw] + \
               [c for c in all_cats_raw if c not in _CAT_ORDER]

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown(
        f"<h3 style='font-size:1rem;font-weight:600;color:{p.text_secondary};"
        f"letter-spacing:0.04em;margin-bottom:0.3rem'>MCP Tool Catalog</h3>"
        f"<p style='font-size:0.8rem;color:{p.text_muted};margin-bottom:1rem'>"
        f"Browse all available research tools. Live availability reflects the current "
        f"MCP server initialization state.</p>",
        unsafe_allow_html=True,
    )

    # ── Summary metrics ───────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Tools", total)
    with c2:
        st.metric("Categories", len(all_cats))
    with c3:
        st.metric("Available Now", available)
    with c4:
        st.metric("Coverage", f"{avail_pct}%")

    st.markdown("<div class='gradient-divider'></div>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────
    col_search, col_cats, col_avail = st.columns([3, 2, 1])
    with col_search:
        search = st.text_input(
            "Search",
            placeholder="Filter by name or description…",
            key="catalog_search",
            label_visibility="collapsed",
        )
    with col_cats:
        selected_cats = st.multiselect(
            "Category",
            options=all_cats,
            key="catalog_cats",
            placeholder="All categories",
            label_visibility="collapsed",
        )
    with col_avail:
        avail_only = st.toggle("Available only", key="catalog_avail_only")

    # Apply filters
    filtered = df.copy()
    if search:
        mask = (
            filtered["tool_name"].str.contains(search, case=False, na=False)
            | filtered["description"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if selected_cats:
        filtered = filtered[
            filtered["categories"].apply(lambda cats: any(c in selected_cats for c in cats))
        ]
    if avail_only:
        filtered = filtered[filtered["tool_name"].isin(loaded_tools)]

    if filtered.empty:
        st.info("No tools match your current filters.")
        return

    # Filtered availability count
    filt_avail = sum(1 for name in filtered["tool_name"] if name in loaded_tools)
    st.markdown(
        f"<p style='font-size:0.78rem;color:{p.text_muted};margin-bottom:0.8rem'>"
        f"Showing <strong style='color:{p.text_secondary}'>{len(filtered)}</strong> tools · "
        f"<strong style='color:{p.success}'>{filt_avail}</strong> available</p>",
        unsafe_allow_html=True,
    )

    # ── Category sections ─────────────────────────────────────────────────
    cats_to_render = selected_cats if selected_cats else all_cats

    for cat in cats_to_render:
        cat_tools = filtered[
            filtered["categories"].apply(lambda cats: cat in cats)
        ].reset_index(drop=True)

        if cat_tools.empty:
            continue

        avail_in_cat = sum(1 for name in cat_tools["tool_name"] if name in loaded_tools)
        icon = _CAT_ICONS.get(cat, "🔧")
        avail_color = p.success if avail_in_cat == len(cat_tools) else (
            p.warning if avail_in_cat > 0 else p.text_muted
        )

        # Expander label includes availability ratio
        label = (
            f"{icon}  {cat} "
            f"— {len(cat_tools)} tools"
        )

        # Expand first category by default, rest collapsed
        default_open = (cat == cats_to_render[0]) and not search and not selected_cats

        with st.expander(label, expanded=default_open):
            # Availability bar across top of expander
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:0.6rem;"
                f"margin-bottom:0.8rem;padding-bottom:0.6rem;"
                f"border-bottom:1px solid {p.border_subtle}'>"
                f"  <span style='font-size:0.75rem;color:{p.text_muted}'>"
                f"    <strong style='color:{avail_color}'>{avail_in_cat}</strong>"
                f"    &nbsp;/&nbsp;{len(cat_tools)} tools available"
                f"  </span>"
                f"  <div style='flex:1;height:3px;border-radius:2px;"
                f"    background:{p.border};overflow:hidden'>"
                f"    <div style='height:100%;width:{round(avail_in_cat/len(cat_tools)*100)}%;"
                f"      background:{avail_color};border-radius:2px;'></div>"
                f"  </div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Render tools in 2-column grid
            for row_start in range(0, len(cat_tools), 2):
                row_tools = cat_tools.iloc[row_start : row_start + 2]
                cols = st.columns(2)
                for col_idx, (_, tool_row) in enumerate(row_tools.iterrows()):
                    with cols[col_idx]:
                        _render_tool_card(tool_row, loaded_tools, p)
