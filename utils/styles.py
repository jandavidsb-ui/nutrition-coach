import streamlit as st


def inject_css() -> None:
    st.markdown("""
<style>
/* ── Base ────────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Main container ──────────────────────────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 780px;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #EEECEA;
    border-right: 1px solid #E0DDD9;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* ── Page title ──────────────────────────────────────────────────────────── */
h1 {
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #1A1A1A !important;
    margin-bottom: 0.25rem !important;
}

h2 {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #1A1A1A !important;
    margin-top: 1.5rem !important;
}

h3 {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
}

/* ── Metric cards ────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1rem 1.2rem !important;
    border: 1px solid #E8E5E1;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    color: #6B7280 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #1A1A1A !important;
    letter-spacing: -0.02em;
}

/* ── Primary button ──────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background: #5C8D72 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 2px 6px rgba(92, 141, 114, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: #4A7A60 !important;
    box-shadow: 0 4px 10px rgba(92, 141, 114, 0.35) !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary button ────────────────────────────────────────────────────── */
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: #3D3D3D !important;
    border: 1px solid #D8D5D1 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}

.stButton > button[kind="secondary"]:hover {
    border-color: #5C8D72 !important;
    color: #5C8D72 !important;
}

/* ── Progress bar ────────────────────────────────────────────────────────── */
.stProgress > div > div {
    border-radius: 99px;
    height: 8px !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #5C8D72, #7AB893) !important;
    border-radius: 99px !important;
}

/* ── Info box ────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 4px !important;
    font-size: 0.9rem !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E8E5E1 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── Select box & inputs ─────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stTextArea"] > div > div {
    border-radius: 10px !important;
    border-color: #D8D5D1 !important;
}

/* ── Radio buttons ───────────────────────────────────────────────────────── */
[data-testid="stRadio"] > div {
    gap: 0.5rem;
}

/* ── File uploader ───────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border-radius: 14px !important;
}

[data-testid="stFileUploader"] > div {
    border-radius: 14px !important;
    border: 2px dashed #C8C5C0 !important;
    background: #FAFAF8 !important;
    transition: border-color 0.2s;
}

[data-testid="stFileUploader"] > div:hover {
    border-color: #5C8D72 !important;
}

/* ── Divider ─────────────────────────────────────────────────────────────── */
hr {
    border-color: #E8E5E1 !important;
    margin: 1.5rem 0 !important;
}

/* ── Dataframe ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid #E8E5E1 !important;
}

/* ── Containers with border ──────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    border-radius: 14px !important;
    border: 1px solid #E8E5E1 !important;
    padding: 1rem !important;
    background: #FFFFFF;
}

/* ── Caption ─────────────────────────────────────────────────────────────── */
.stCaption {
    color: #6B7280 !important;
    font-size: 0.8rem !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] {
    color: #5C8D72 !important;
}

/* ── Sidebar user switcher ───────────────────────────────────────────────── */
.user-switcher {
    display: flex;
    gap: 8px;
    margin-bottom: 0.5rem;
}

.user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.15s;
}

/* ── Step indicator ──────────────────────────────────────────────────────── */
.step-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 1.5rem;
}

.step-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
}

.step-dot.active {
    background: #5C8D72;
    color: white;
}

.step-dot.done {
    background: #D4EAD9;
    color: #5C8D72;
}

.step-dot.pending {
    background: #EEECEA;
    color: #9CA3AF;
}

.step-line {
    flex: 1;
    height: 2px;
    background: #E8E5E1;
}

.step-line.done {
    background: #5C8D72;
}
</style>
""", unsafe_allow_html=True)


def step_indicator(current: int) -> None:
    """Show 3-step progress indicator for log meal flow."""
    steps = ["Upload", "Questions", "Confirm"]
    dots = []
    lines = []
    for i, label in enumerate(steps, 1):
        if i < current:
            cls = "done"
            icon = "✓"
        elif i == current:
            cls = "active"
            icon = str(i)
        else:
            cls = "pending"
            icon = str(i)
        dots.append(f'<div class="step-dot {cls}">{icon}</div><span style="font-size:0.75rem;color:#6B7280;font-weight:500">{label}</span>')
        if i < len(steps):
            line_cls = "done" if i < current else ""
            lines.append(f'<div class="step-line {line_cls}"></div>')

    parts = []
    for i, dot in enumerate(dots):
        parts.append(dot)
        if i < len(lines):
            parts.append(lines[i])

    html = f'<div class="step-indicator">{"".join(parts)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def macro_pill(label: str, value: str, color: str) -> str:
    return f"""
    <div style="background:{color}15;border:1px solid {color}30;border-radius:10px;
                padding:0.75rem 1rem;text-align:center;flex:1">
        <div style="font-size:0.7rem;font-weight:600;color:{color};text-transform:uppercase;
                    letter-spacing:0.05em;margin-bottom:2px">{label}</div>
        <div style="font-size:1.2rem;font-weight:700;color:#1A1A1A">{value}</div>
    </div>"""


def macro_pills_row(totals: dict) -> None:
    pills = [
        macro_pill("Calories", f"{totals.get('calories') or 0:.0f}", "#E05C5C"),
        macro_pill("Protein",  f"{totals.get('protein_g') or 0:.1f}g", "#3B82F6"),
        macro_pill("Carbs",    f"{totals.get('carb_g') or 0:.1f}g", "#F59E0B"),
        macro_pill("Fat",      f"{totals.get('fat_g') or 0:.1f}g", "#8B5CF6"),
        macro_pill("Fiber",    f"{totals.get('fiber_g') or 0:.1f}g", "#5C8D72"),
    ]
    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap">{"".join(pills)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
