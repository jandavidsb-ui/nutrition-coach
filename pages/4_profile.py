from __future__ import annotations

import streamlit as st
from datetime import date

from services import user_service

user_id = st.session_state.get("user_id", 1)
profile = user_service.get_profile(user_id)

st.title(f"Profile — {profile.get('name', 'User')}")

st.subheader("Personal info")
with st.form("profile_form"):
    name   = st.text_input("Name", value=profile.get("name", ""))
    c1, c2, c3 = st.columns(3)
    height = c1.number_input("Height (cm)", value=float(profile.get("height_cm") or 163), step=0.5)
    weight = c2.number_input("Weight (kg)",  value=float(profile.get("weight_kg") or 60),  step=0.1)
    age    = c3.number_input("Age",           value=int(profile.get("age") or 25), step=1, min_value=10, max_value=100)

    st.subheader("Daily targets")
    c4, c5, c6 = st.columns(3)
    cal_target = c4.number_input("Calories (kcal)", value=float(profile.get("target_calories") or 1550), step=50.0)
    pro_target = c5.number_input("Protein (g)",     value=float(profile.get("target_protein_g") or 110), step=5.0)
    fib_target = c6.number_input("Fiber (g)",       value=float(profile.get("target_fiber_g") or 25),   step=1.0)

    c7, c8 = st.columns(2)
    fat_target  = c7.number_input("Fat (g)",   value=float(profile.get("target_fat_g") or 60),  step=5.0)
    carb_target = c8.number_input("Carbs (g)", value=float(profile.get("target_carb_g") or 180), step=5.0)

    saved = st.form_submit_button("Save profile", type="primary")

if saved:
    user_service.update_profile({
        "name":             name,
        "height_cm":        height,
        "weight_kg":        weight,
        "age":              int(age),
        "target_calories":  cal_target,
        "target_protein_g": pro_target,
        "target_fiber_g":   fib_target,
        "target_fat_g":     fat_target,
        "target_carb_g":    carb_target,
    }, user_id=user_id)
    st.success("Profile saved.")
    st.rerun()

# ── TDEE Calculator ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Recommended calorie target")

age_val    = int(profile.get("age") or 25)
weight_val = float(profile.get("weight_kg") or 60)
height_val = float(profile.get("height_cm") or 163)
sex_val    = profile.get("sex", "female")

if sex_val == "female":
    bmr = 10 * weight_val + 6.25 * height_val - 5 * age_val - 161
else:
    bmr = 10 * weight_val + 6.25 * height_val - 5 * age_val + 5

tdee      = bmr * 1.375
suggested_cal  = round(tdee - 200, -1)
suggested_pro  = round(weight_val * 1.8)          # 1.8 g/kg for recomposition
suggested_fat  = round((suggested_cal * 0.25) / 9) # 25% of calories → grams
suggested_carb = round((suggested_cal - suggested_pro * 4 - suggested_fat * 9) / 4)

st.markdown(
    "<div style='background:#F0F7F3;border-radius:12px;padding:1rem 1.2rem;"
    "border:1px solid #C8DDD2;margin-bottom:0.75rem'>"
    "<p style='margin:0 0 6px;font-size:0.8rem;font-weight:600;color:#5C8D72;"
    "text-transform:uppercase;letter-spacing:0.06em'>Mifflin-St Jeor estimate</p>"
    "<p style='margin:0 0 8px;font-size:0.95rem;color:#1A1A1A'>"
    f"BMR <b>{bmr:.0f} kcal</b> &nbsp;·&nbsp; "
    f"TDEE <b>{tdee:.0f} kcal</b> &nbsp;·&nbsp; "
    f"Suggested <b>{suggested_cal:.0f} kcal</b> "
    "<span style='color:#6B7280;font-size:0.8rem'>(TDEE − 200)</span>"
    "</p>"
    "<p style='margin:0;font-size:0.85rem;color:#4B5563'>"
    f"Protein <b>{suggested_pro:.0f}g</b> &nbsp;·&nbsp; "
    f"Fat <b>{suggested_fat:.0f}g</b> &nbsp;·&nbsp; "
    f"Carbs <b>{suggested_carb:.0f}g</b> &nbsp;·&nbsp; "
    "Fiber <b>25g</b>"
    "</p></div>",
    unsafe_allow_html=True,
)

if st.button("Apply all suggestions →", type="secondary"):
    user_service.update_profile({
        "target_calories":  suggested_cal,
        "target_protein_g": suggested_pro,
        "target_fat_g":     suggested_fat,
        "target_carb_g":    suggested_carb,
        "target_fiber_g":   25,
    }, user_id=user_id)
    st.success(
        f"Targets updated: {suggested_cal:.0f} kcal · "
        f"{suggested_pro:.0f}g protein · {suggested_fat:.0f}g fat · {suggested_carb:.0f}g carbs"
    )
    st.rerun()

# ── Log weight ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Log weight")
with st.form("weight_form"):
    w_date  = st.date_input("Date", value=date.today(), max_value=date.today())
    w_kg    = st.number_input("Weight (kg)", value=float(profile.get("weight_kg") or 60), step=0.1)
    w_notes = st.text_input("Notes (optional)", placeholder="e.g. after workout, fasted")
    w_saved = st.form_submit_button("Log weight")

if w_saved:
    user_service.log_weight(w_kg, w_date.isoformat(), w_notes, user_id=user_id)
    st.success(f"Logged {w_kg} kg on {w_date}.")

weight_history = user_service.get_weight_log(30, user_id=user_id)
if weight_history:
    st.divider()
    st.subheader("Recent weight")
    st.dataframe(
        [{"Date": r["logged_date"], "Weight (kg)": r["weight_kg"], "Notes": r["notes"] or ""}
         for r in weight_history],
        use_container_width=True,
        hide_index=True,
    )
