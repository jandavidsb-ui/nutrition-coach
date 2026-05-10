from __future__ import annotations

import streamlit as st
from datetime import date

from services import summary_service, meal_service, user_service, exercise_service, ai_service
from services.summary_service import compute_coaching_note
from components.macro_chart import macro_summary_row
from components.meal_card import meal_card

user_id = st.session_state.get("user_id", 1)
profile = user_service.get_profile(user_id)

st.title("Today")

selected_date = st.date_input("", value=date.today(), max_value=date.today(),
                               label_visibility="collapsed")
date_str = selected_date.isoformat()

summary          = summary_service.get_daily_summary(date_str, user_id)
exercise_summary = exercise_service.get_daily_exercise_summary(date_str, user_id)

cal_target = profile.get("target_calories") or 1550
eaten      = summary.get("total_calories") or 0
burned     = exercise_summary["total_burned"]
net_cal    = eaten - burned
cal_left   = cal_target - net_cal

gaps = summary_service.get_macro_gaps(date_str, profile, user_id)
pro_rem = gaps["protein_remaining"]
fib_rem = gaps["fiber_remaining"]

# ── Top metric cards ──────────────────────────────────────────────────────────
st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)


def _metric_card(label, value, sub, color):
    return (
        f"<div style='background:#fff;border-radius:14px;padding:1rem 1.2rem;"
        f"border:1px solid #E8E5E1;box-shadow:0 1px 4px rgba(0,0,0,0.04);flex:1'>"
        f"<div style='font-size:0.7rem;font-weight:600;color:#6B7280;"
        f"text-transform:uppercase;letter-spacing:0.06em'>{label}</div>"
        f"<div style='font-size:1.65rem;font-weight:700;color:{color};"
        f"letter-spacing:-0.02em;line-height:1.2'>{value}</div>"
        f"<div style='font-size:0.75rem;color:#9CA3AF;margin-top:2px'>{sub}</div>"
        f"</div>"
    )


cal_color = "#E05C5C" if cal_left < 0 else "#1A1A1A"
pro_color = "#E05C5C" if pro_rem < 50 and selected_date == date.today() else "#1A1A1A"

burned_sub = f"eaten {eaten:.0f} − burned {burned:.0f}" if burned > 0 else "kcal remaining"

cards_html = (
    "<div style='display:flex;gap:10px;margin-bottom:1.5rem'>"
    + _metric_card("Calories left",  f"{cal_left:.0f}", burned_sub, cal_color)
    + _metric_card("Protein left",   f"{pro_rem:.0f}g", "your #1 priority", pro_color)
    + _metric_card("Fiber left",     f"{fib_rem:.0f}g", "aim for 25g+", "#1A1A1A")
    + "</div>"
)
st.markdown(cards_html, unsafe_allow_html=True)

# ── Progress ──────────────────────────────────────────────────────────────────
st.subheader("Progress")
macro_summary_row(summary, profile)

st.divider()

# ── AI Coaching note ──────────────────────────────────────────────────────────
meal_count = summary.get("meal_count") or 0
has_data   = meal_count > 0 or exercise_summary["count"] > 0

if "coaching_message" not in st.session_state or st.session_state.coaching_message is None:
    if has_data:
        with st.spinner("Getting coaching insight…"):
            try:
                st.session_state.coaching_message = ai_service.generate_coaching_message(
                    summary, exercise_summary, profile, net_cal
                )
            except Exception:
                st.session_state.coaching_message = compute_coaching_note(summary, profile)
    else:
        st.session_state.coaching_message = (
            "Start logging your meals — even a rough photo is better than nothing."
        )

note = st.session_state.coaching_message
st.markdown(
    "<div style='background:#F0F7F3;border-radius:12px;padding:0.9rem 1.1rem;"
    "border-left:4px solid #5C8D72;margin-bottom:1rem'>"
    "<span style='font-size:0.75rem;font-weight:700;color:#5C8D72;"
    "text-transform:uppercase;letter-spacing:0.06em'>Coach</span>"
    f"<p style='margin:4px 0 0;font-size:0.9rem;color:#1A1A1A'>{note}</p></div>",
    unsafe_allow_html=True,
)

st.divider()

# ── Exercise logging ──────────────────────────────────────────────────────────
with st.expander("Log exercise", expanded=False):
    with st.form("exercise_form"):
        desc = st.text_area(
            "What did you do today?",
            placeholder="e.g. walked incline treadmill 1 hour, 30 min yoga, 45 min weight training",
            height=72,
        )
        c_desc, c_cal = st.columns([3, 2])
        manual_cal = c_cal.number_input(
            "Or enter calories manually (0 = use AI)",
            min_value=0, step=10, value=0,
        )
        ex_submitted = st.form_submit_button("Add exercise →", type="primary", use_container_width=True)

    if ex_submitted and desc.strip():
        if manual_cal > 0:
            exercise_service.log_exercise(user_id, date_str, desc, float(manual_cal), ai_estimated=False)
            st.session_state.coaching_message = None
            st.rerun()
        else:
            with st.spinner("Estimating calories burned…"):
                try:
                    result    = ai_service.estimate_exercise_calories(desc, profile)
                    burned_ai = float(result["calories_burned"])
                    ex_notes  = result.get("notes", "")
                    exercise_service.log_exercise(user_id, date_str, desc, burned_ai, ai_estimated=True)
                    st.session_state.coaching_message = None
                    if ex_notes:
                        st.caption(f"ℹ️ {ex_notes}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Estimation failed: {e}")

# Exercise list
exercises = exercise_service.get_exercises_for_date(date_str, user_id)
if exercises:
    st.subheader("Exercise")
    for ex in exercises:
        col_ex, col_del = st.columns([5, 1])
        tag = " *(AI estimate)*" if ex["ai_estimated"] else ""
        col_ex.markdown(
            f"**{ex['description']}** — **{ex['calories_burned']:.0f} kcal** burned{tag}"
        )
        if col_del.button("✕", key=f"del_ex_{ex['id']}"):
            exercise_service.delete_exercise(ex["id"])
            st.session_state.coaching_message = None
            st.rerun()

st.divider()

# ── Meal timeline ─────────────────────────────────────────────────────────────
st.subheader("Meals")
meals = meal_service.get_meals_for_date(date_str, user_id)

if not meals:
    st.markdown(
        "<div style='text-align:center;padding:2.5rem;color:#9CA3AF'>"
        "<div style='font-size:2.5rem'>🍽️</div>"
        "<p style='margin:8px 0 0;font-size:0.9rem'>No meals logged yet</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_log_meal.py", label="Log your first meal →", icon="📷")
else:
    def handle_delete(meal_id: int):
        meal_service.delete_meal(meal_id)
        st.session_state.coaching_message = None
        st.rerun()

    for m in meals:
        meal_card(m, on_delete=handle_delete)
