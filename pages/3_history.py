from __future__ import annotations

import streamlit as st

from services import summary_service, user_service, ai_service

user_id = st.session_state.get("user_id", 1)
profile = user_service.get_profile(user_id)

st.title("History")

# ── Period selector ───────────────────────────────────────────────────────────
period_map = {"7 days": 7, "14 days": 14, "30 days": 30}
period_label = st.segmented_control(
    "Period", list(period_map.keys()), default="7 days", label_visibility="collapsed"
)
days   = period_map[period_label]
trends = summary_service.get_weekly_trends(days, user_id)

if not trends:
    st.markdown(
        "<div style='text-align:center;padding:3rem;color:#9CA3AF'>"
        "<div style='font-size:2.5rem'>📈</div>"
        "<p style='margin:8px 0 0;font-size:0.9rem'>No data yet — log some meals to see trends.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

cal_target = profile.get("target_calories") or 1550
pro_target = profile.get("target_protein_g") or 110
fib_target = profile.get("target_fiber_g") or 25

n          = len(trends)
avg_cal    = sum(r["total_calories"] or 0 for r in trends) / n
avg_pro    = sum(r["total_protein"]  or 0 for r in trends) / n
avg_fib    = sum(r["total_fiber"]    or 0 for r in trends) / n
days_on_target_cal = sum(1 for r in trends if (r["total_calories"] or 0) <= cal_target * 1.05)
days_on_target_pro = sum(1 for r in trends if (r["total_protein"]  or 0) >= pro_target * 0.8)

# ── Summary cards ─────────────────────────────────────────────────────────────
def _summary_card(label, value, sub, pct, color):
    bar_color = color if pct >= 0.8 else "#E05C5C"
    bar_w     = min(int(pct * 100), 100)
    return (
        f"<div style='background:#fff;border-radius:14px;padding:1rem 1.2rem;"
        f"border:1px solid #E8E5E1;box-shadow:0 1px 4px rgba(0,0,0,0.04)'>"
        f"<div style='font-size:0.7rem;font-weight:600;color:#6B7280;"
        f"text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>{label}</div>"
        f"<div style='font-size:1.5rem;font-weight:700;color:#1A1A1A;"
        f"letter-spacing:-0.02em;line-height:1.2'>{value}</div>"
        f"<div style='font-size:0.75rem;color:#9CA3AF;margin:3px 0 8px'>{sub}</div>"
        f"<div style='background:#F0F0EE;border-radius:99px;height:5px'>"
        f"<div style='background:{bar_color};border-radius:99px;height:5px;width:{bar_w}%'></div>"
        f"</div></div>"
    )

cal_pct = avg_cal / cal_target if cal_target else 0
pro_pct = avg_pro / pro_target if pro_target else 0
fib_pct = avg_fib / fib_target if fib_target else 0

st.markdown(
    "<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:1.5rem'>"
    + _summary_card("Avg calories / day", f"{avg_cal:.0f}",
                    f"target {cal_target:.0f} kcal", cal_pct, "#E05C5C")
    + _summary_card("Avg protein / day",  f"{avg_pro:.0f}g",
                    f"target {pro_target:.0f}g", pro_pct, "#3B82F6")
    + _summary_card("Avg fiber / day",    f"{avg_fib:.1f}g",
                    f"target {fib_target:.0f}g", fib_pct, "#5C8D72")
    + "</div>",
    unsafe_allow_html=True,
)

# Consistency badges
c1, c2 = st.columns(2)
c1.markdown(
    f"<div style='background:#F0F7F3;border-radius:10px;padding:0.7rem 1rem;"
    f"border:1px solid #C8DDD2;text-align:center'>"
    f"<div style='font-size:1.4rem;font-weight:700;color:#3A7D5A'>{days_on_target_cal}/{n}</div>"
    f"<div style='font-size:0.75rem;color:#5C8D72;font-weight:600'>days within calorie target</div>"
    f"</div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div style='background:#EFF6FF;border-radius:10px;padding:0.7rem 1rem;"
    f"border:1px solid #BFDBFE;text-align:center'>"
    f"<div style='font-size:1.4rem;font-weight:700;color:#1D4ED8'>{days_on_target_pro}/{n}</div>"
    f"<div style='font-size:0.75rem;color:#3B82F6;font-weight:600'>days ≥ 80% protein target</div>"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

# ── AI Performance Analysis ───────────────────────────────────────────────────
_cache_key = f"history_analysis_{user_id}_{days}"

def _stars_html(stars: int, label: str) -> str:
    _star_cfg = {
        5: ("#3A7D5A", "#D4EAD9", "#C8DDD2"),
        4: ("#1D4ED8", "#DBEAFE", "#BFDBFE"),
        3: ("#92400E", "#FEF3C7", "#FDE68A"),
        2: ("#B45309", "#FEE2E2", "#FECACA"),
        1: ("#991B1B", "#FEE2E2", "#FECACA"),
    }
    fg, bg, border = _star_cfg.get(stars, _star_cfg[3])
    filled   = "★" * stars + "☆" * (5 - stars)
    return (
        f"<div style='background:{bg};border-radius:14px;padding:1rem 1.2rem;"
        f"border:1px solid {border};margin-bottom:0.75rem'>"
        f"<div style='font-size:0.7rem;font-weight:600;color:{fg};"
        f"text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px'>AI Performance Rating</div>"
        f"<div style='font-size:1.8rem;letter-spacing:3px;color:{fg};line-height:1'>{filled}</div>"
        f"<div style='font-size:1rem;font-weight:700;color:{fg};margin-top:4px'>{label}</div>"
        f"</div>"
    )

with st.expander("AI Analysis", expanded=True):
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        if st.button("Analyse my performance →", type="secondary", use_container_width=True):
            with st.spinner("Analysing…"):
                try:
                    result = ai_service.analyse_history(trends, period_label, profile)
                    st.session_state[_cache_key] = result
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
    with col_info:
        st.caption("Uses 1 AI request · results cached until you change period or user")

    if _cache_key in st.session_state:
        analysis = st.session_state[_cache_key]
        stars    = max(1, min(5, int(analysis.get("stars") or 3)))
        label    = analysis.get("label", "Okay")
        summary  = analysis.get("summary", "")
        tips     = analysis.get("tips", [])

        st.markdown(_stars_html(stars, label), unsafe_allow_html=True)

        if summary:
            st.markdown(
                f"<p style='font-size:0.88rem;color:#374151;line-height:1.6;"
                f"margin:0 0 0.75rem'>{summary}</p>",
                unsafe_allow_html=True,
            )
        if tips:
            for tip in tips:
                st.markdown(
                    f"<div style='background:#fff;border-radius:8px;padding:0.6rem 0.9rem;"
                    f"border:1px solid #E5E7EB;margin-bottom:6px;font-size:0.85rem;color:#1A1A1A'>"
                    f"💡 {tip}</div>",
                    unsafe_allow_html=True,
                )

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
tab_cal, tab_pro, tab_fib = st.tabs(["Calories", "Protein", "Fiber"])

with tab_cal:
    chart_data = {"Date": [r["day"] for r in trends],
                  "Calories": [r["total_calories"] or 0 for r in trends]}
    st.bar_chart(chart_data, x="Date", y="Calories", color="#E05C5C", use_container_width=True)
    st.caption(f"Target: {cal_target:.0f} kcal/day")

with tab_pro:
    chart_data = {"Date": [r["day"] for r in trends],
                  "Protein (g)": [r["total_protein"] or 0 for r in trends]}
    st.bar_chart(chart_data, x="Date", y="Protein (g)", color="#3B82F6", use_container_width=True)
    st.caption(f"Target: {pro_target:.0f} g/day")

with tab_fib:
    chart_data = {"Date": [r["day"] for r in trends],
                  "Fiber (g)": [r["total_fiber"] or 0 for r in trends]}
    st.bar_chart(chart_data, x="Date", y="Fiber (g)", color="#5C8D72", use_container_width=True)
    st.caption(f"Target: {fib_target:.0f} g/day")

st.divider()

# ── Day-by-day comparison table ───────────────────────────────────────────────
st.subheader("Day-by-day breakdown")

def _pct_badge(val, target, reverse=False):
    if not target:
        return ""
    pct = val / target
    if reverse:
        ok = pct <= 1.05
    else:
        ok = pct >= 0.8
    color = "#D4EAD9" if ok else "#FEE2E2"
    fg    = "#3A7D5A" if ok else "#B91C1C"
    return (
        f"<span style='background:{color};color:{fg};border-radius:6px;"
        f"padding:1px 6px;font-size:0.75rem;font-weight:600'>{pct*100:.0f}%</span>"
    )

rows_html = ""
for r in reversed(trends):
    cal_v  = r["total_calories"] or 0
    pro_v  = r["total_protein"]  or 0
    carb_v = r["total_carb"]     or 0
    fat_v  = r["total_fat"]      or 0
    fib_v  = r["total_fiber"]    or 0

    rows_html += (
        f"<tr>"
        f"<td style='padding:10px 12px;font-weight:600;color:#1A1A1A;white-space:nowrap'>{r['day']}</td>"
        f"<td style='padding:10px 12px;text-align:right'>{cal_v:.0f} {_pct_badge(cal_v, cal_target, reverse=True)}</td>"
        f"<td style='padding:10px 12px;text-align:right'>{pro_v:.0f}g {_pct_badge(pro_v, pro_target)}</td>"
        f"<td style='padding:10px 12px;text-align:right;color:#6B7280'>{carb_v:.0f}g</td>"
        f"<td style='padding:10px 12px;text-align:right;color:#6B7280'>{fat_v:.0f}g</td>"
        f"<td style='padding:10px 12px;text-align:right;color:#6B7280'>{fib_v:.1f}g</td>"
        f"<td style='padding:10px 12px;text-align:center;color:#9CA3AF'>{r['meal_count']}</td>"
        f"</tr>"
    )

st.markdown(
    "<div style='overflow-x:auto'>"
    "<table style='width:100%;border-collapse:collapse;font-size:0.875rem'>"
    "<thead>"
    "<tr style='border-bottom:2px solid #E8E5E1'>"
    "<th style='padding:8px 12px;text-align:left;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Date</th>"
    "<th style='padding:8px 12px;text-align:right;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Calories</th>"
    "<th style='padding:8px 12px;text-align:right;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Protein</th>"
    "<th style='padding:8px 12px;text-align:right;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Carbs</th>"
    "<th style='padding:8px 12px;text-align:right;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Fat</th>"
    "<th style='padding:8px 12px;text-align:right;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Fiber</th>"
    "<th style='padding:8px 12px;text-align:center;font-size:0.7rem;font-weight:600;"
    "color:#6B7280;text-transform:uppercase;letter-spacing:0.06em'>Meals</th>"
    "</tr></thead>"
    f"<tbody>{rows_html}</tbody>"
    "</table></div>",
    unsafe_allow_html=True,
)
