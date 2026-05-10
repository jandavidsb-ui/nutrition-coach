from __future__ import annotations

import streamlit as st
from datetime import datetime

import config
from services import ai_service, image_service, meal_service, summary_service, exercise_service, user_service
from utils.styles import macro_pills_row

user_id = st.session_state.get("user_id", 1)

if not config.GEMINI_API_KEYS:
    st.error("Add GEMINI_API_KEY_1 to your `.env` file to enable AI analysis.")
    st.stop()

# ── Rating config ──────────────────────────────────────────────────────────────
_RATING = {
    5: {"label": "Excellent",    "emoji": "🌟", "bg": "#D4EAD9", "fg": "#2D6A4F", "bar": "#3A7D5A"},
    4: {"label": "Good",         "emoji": "✅", "bg": "#DBEAFE", "fg": "#1E40AF", "bar": "#3B82F6"},
    3: {"label": "Okay",         "emoji": "🟡", "bg": "#FEF3C7", "fg": "#92400E", "bar": "#F59E0B"},
    2: {"label": "Think Twice",  "emoji": "⚠️", "bg": "#FEE2E2", "fg": "#991B1B", "bar": "#EF4444"},
    1: {"label": "Avoid",        "emoji": "🔴", "bg": "#FEE2E2", "fg": "#7F1D1D", "bar": "#DC2626"},
}

def _reset_check():
    for key in ["fc_result", "fc_image_obj", "fc_image_b64", "fc_media_type", "fc_note"]:
        st.session_state.pop(key, None)

def _meal_type_default() -> str:
    h = datetime.now().hour
    if h < 11:   return "breakfast"
    if h < 15:   return "lunch"
    if h < 21:   return "dinner"
    return "snack"

st.title("Should I eat this?")
st.caption("Upload a photo and let AI rate it based on what you've already had today.")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Upload & analyse
# ─────────────────────────────────────────────────────────────────────────────
if "fc_result" not in st.session_state:
    uploaded = st.file_uploader(
        "Drop a photo here or click to upload",
        type=["jpg", "jpeg", "png", "webp"],
    )
    user_note = st.text_area(
        "What is this? (optional)",
        placeholder="e.g. mango sticky rice, pad kra pao with egg, protein shake…",
        height=72,
    )

    if uploaded:
        try:
            image = image_service.validate_image(uploaded)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        st.image(image, use_container_width=True)

        if st.button("Analyse →", type="primary", use_container_width=True):
            profile  = user_service.get_profile(user_id)
            date_str = datetime.now().date().isoformat()
            food_sum = summary_service.get_daily_summary(date_str, user_id)
            ex_sum   = exercise_service.get_daily_exercise_summary(date_str, user_id)

            b64, mtype = image_service.encode_image_base64(image)

            with st.spinner("Analysing…"):
                try:
                    result = ai_service.check_food(b64, mtype, user_note, food_sum, ex_sum, profile)
                    st.session_state.fc_result     = result
                    st.session_state.fc_image_obj  = image
                    st.session_state.fc_image_b64  = b64
                    st.session_state.fc_media_type = mtype
                    st.session_state.fc_note       = user_note
                    st.rerun()
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Show result + decision buttons
# ─────────────────────────────────────────────────────────────────────────────
else:
    result              = st.session_state.fc_result
    rating              = max(1, min(5, int(result.get("rating") or 3)))
    cfg                 = _RATING[rating]
    label               = result.get("rating_label") or cfg["label"]
    food_name           = result.get("food_name", "This food")
    reasoning           = result.get("reasoning", "")
    nutrition           = result.get("nutrition_estimate", {})
    ex_sug              = result.get("exercise_suggestions", [])
    suggested_pct       = int(result.get("suggested_percent") or 100)
    suggested_pct_reason = result.get("suggested_percent_reason", "")

    col_img, col_info = st.columns([1, 1])

    with col_img:
        st.image(st.session_state.fc_image_obj, use_container_width=True)

    with col_info:
        # Rating badge + bar
        filled   = "●" * rating + "○" * (5 - rating)
        st.markdown(
            f"<div style='background:{cfg['bg']};border-radius:14px;padding:1.1rem 1.3rem;"
            f"border:1px solid {cfg['bar']}40'>"
            f"<div style='font-size:0.7rem;font-weight:600;color:{cfg['fg']};"
            f"text-transform:uppercase;letter-spacing:0.07em;margin-bottom:6px'>AI Rating</div>"
            f"<div style='font-size:2rem;letter-spacing:4px;color:{cfg['bar']};margin-bottom:4px'>"
            f"{filled}</div>"
            f"<div style='font-size:1.15rem;font-weight:700;color:{cfg['fg']}'>"
            f"{cfg['emoji']} {label}</div>"
            f"<div style='font-size:0.8rem;font-weight:600;color:{cfg['fg']}80;margin-top:2px'>"
            f"{food_name}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        if reasoning:
            st.markdown(
                f"<div style='font-size:0.88rem;color:#374151;line-height:1.55'>{reasoning}</div>",
                unsafe_allow_html=True,
            )

    # Suggested portion
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    pct_color = "#3A7D5A" if suggested_pct >= 75 else "#B45309" if suggested_pct >= 50 else "#B91C1C"
    st.markdown(
        f"<div style='background:#F9FAFB;border-radius:10px;padding:0.75rem 1rem;"
        f"border:1px solid #E5E7EB;margin-bottom:0.5rem'>"
        f"<span style='font-size:0.75rem;font-weight:600;color:#6B7280;"
        f"text-transform:uppercase;letter-spacing:0.06em'>Recommended portion</span><br>"
        f"<span style='font-size:1.3rem;font-weight:700;color:{pct_color}'>{suggested_pct}%</span>"
        + (f"<span style='font-size:0.8rem;color:#6B7280;margin-left:8px'>{suggested_pct_reason}</span>"
           if suggested_pct_reason else "")
        + "</div>",
        unsafe_allow_html=True,
    )

    # Nutrition estimate (full portion)
    if nutrition:
        st.caption("Estimated nutrition for full portion (100%)")
        macro_pills_row(nutrition)

    # Exercise suggestions (only when rating ≤ 2 + no exercise logged)
    if ex_sug:
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#FFF7ED;border-radius:12px;padding:0.9rem 1.1rem;"
            "border-left:4px solid #F59E0B;margin-bottom:0.5rem'>"
            "<div style='font-size:0.75rem;font-weight:700;color:#B45309;"
            "text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px'>"
            "💪 Compensate with exercise</div>",
            unsafe_allow_html=True,
        )
        for ex in ex_sug:
            name     = ex.get("name", "")
            duration = ex.get("duration", "")
            kcal     = ex.get("calories_burned", "")
            st.markdown(
                f"<div style='font-size:0.88rem;color:#374151;margin-bottom:4px'>"
                f"• <b>{name}</b>"
                + (f" — {duration}" if duration else "")
                + (f" (~{kcal} kcal)" if kcal else "")
                + "</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Decision ──────────────────────────────────────────────────────────────
    st.subheader("Your decision")

    col_mt, col_pct = st.columns(2)
    meal_types  = ["breakfast", "lunch", "dinner", "snack"]
    default_idx = meal_types.index(_meal_type_default())
    meal_type   = col_mt.selectbox("Meal type", meal_types, index=default_idx)

    pct_options  = [25, 50, 75, 100]
    default_pct  = suggested_pct if suggested_pct in pct_options else 100
    actual_pct   = col_pct.select_slider(
        "How much will you eat?",
        options=pct_options,
        value=default_pct,
        format_func=lambda x: f"{x}%",
    )
    fraction = actual_pct / 100

    # Show scaled nutrition preview
    if nutrition and actual_pct != 100:
        scaled = {k: (v or 0) * fraction for k, v in nutrition.items()}
        st.caption(f"Nutrition at {actual_pct}%")
        macro_pills_row(scaled)

    col_yes, col_no = st.columns([3, 1])

    with col_yes:
        if st.button("Yes, I'll eat it — log this meal ✓", type="primary", use_container_width=True):
            date_str   = datetime.now().date().isoformat()
            meal_id    = meal_service.create_meal_stub(meal_type, user_id)
            image_path = image_service.persist_image(st.session_state.fc_image_obj, meal_id)

            nutrition_totals = {
                "calories":  (nutrition.get("calories") or 0) * fraction,
                "protein_g": (nutrition.get("protein_g") or 0) * fraction,
                "carb_g":    (nutrition.get("carb_g") or 0) * fraction,
                "fat_g":     (nutrition.get("fat_g") or 0) * fraction,
                "fiber_g":   (nutrition.get("fiber_g") or 0) * fraction,
                "sodium_mg": (nutrition.get("sodium_mg") or 0) * fraction,
                "sugar_g":   (nutrition.get("sugar_g") or 0) * fraction,
                "confidence": "medium",
                "estimate_notes": reasoning,
            }
            meal_service.save_confirmed_meal(
                meal_id=meal_id,
                image_path=image_path,
                is_homemade=None,
                percent_eaten=fraction,
                is_shared=False,
                raw_description=food_name + (f" — {st.session_state.fc_note}" if st.session_state.fc_note else ""),
                ai_notes=reasoning,
                nutrition_totals=nutrition_totals,
                items=[],
            )
            st.session_state.coaching_message = None
            _reset_check()
            st.success("Meal logged! Head to Today to see your update.")
            st.rerun()

    with col_no:
        if st.button("No, skip it", use_container_width=True):
            _reset_check()
            st.rerun()
