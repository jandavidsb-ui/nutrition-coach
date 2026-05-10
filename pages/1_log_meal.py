from __future__ import annotations

import streamlit as st

import config
from services import ai_service, image_service, meal_service, user_service
from utils.styles import step_indicator, macro_pills_row

user_id = st.session_state.get("user_id", 1)

if not config.GEMINI_API_KEYS:
    st.error("Add GEMINI_API_KEY_1 to your `.env` file to enable AI analysis.")
    st.stop()

def _reset():
    for key in ["meal_id", "image_obj", "image_b64", "media_type",
                 "identified", "nutrition_result", "step",
                 "is_homemade", "percent_eaten", "is_shared", "user_notes",
                 "coaching_message"]:
        st.session_state.pop(key, None)

if "step" not in st.session_state:
    st.session_state.step = "upload"

step_num = {"upload": 1, "clarify": 2, "confirm": 3}.get(st.session_state.step, 1)


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Log a Meal")
step_indicator(step_num)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Upload
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == "upload":

    col_type, _ = st.columns([1, 2])
    meal_type = col_type.selectbox(
        "Meal type",
        ["breakfast", "lunch", "dinner", "snack"],
        index=1,
        label_visibility="visible",
    )

    uploaded = st.file_uploader(
        "Drop a photo here or click to upload",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="visible",
    )

    user_notes = st.text_area(
        "Notes (optional)",
        placeholder="e.g. light oil, extra tofu, skipped the rice…",
        height=72,
    )

    if uploaded:
        try:
            image = image_service.validate_image(uploaded)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        st.image(image, use_container_width=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if st.button("Analyse meal →", type="primary", use_container_width=True):
            meal_id = meal_service.create_meal_stub(meal_type, user_id)
            b64, mtype = image_service.encode_image_base64(image)
            st.session_state.update({
                "meal_id": meal_id, "meal_type": meal_type,
                "image_obj": image, "image_b64": b64,
                "media_type": mtype, "user_notes": user_notes,
            })
            with st.spinner("Identifying dishes…"):
                profile = user_service.get_profile(user_id)
                try:
                    result = ai_service.analyze_image(b64, mtype, profile)
                    st.session_state.identified = result
                    st.session_state.step = "clarify"
                    st.rerun()
                except Exception as e:
                    meal_service.delete_meal(meal_id)
                    st.error(f"AI analysis failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Clarification
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "clarify":
    identified = st.session_state.identified
    items = identified.get("items", [])
    caption = identified.get("raw_caption", "")

    # What AI sees
    st.markdown(
        f"<div style='background:#F0F7F3;border-radius:12px;padding:1rem 1.2rem;"
        f"border:1px solid #C8DDD2;margin-bottom:1rem'>"
        f"<p style='font-size:0.75rem;font-weight:600;color:#5C8D72;"
        f"text-transform:uppercase;letter-spacing:0.06em;margin:0 0 6px'>What I see</p>"
        f"<p style='margin:0;font-size:0.95rem;color:#1A1A1A'>{caption}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if items:
        for item in items:
            qty = item.get("quantity_desc", "")
            qty_html = f'  <span style="color:#6B7280">— {qty}</span>' if qty else ""
            st.markdown(
                f"<p style='margin:2px 0;font-size:0.9rem'>• <b>{item['name']}</b>{qty_html}</p>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.subheader("3 quick questions")

    with st.form("clarify_form"):
        homemade_choice = st.radio(
            "Was this homemade or from a restaurant?",
            ["Homemade 🏠", "Restaurant / takeaway 🏪", "Not sure"],
            horizontal=True,
        )
        shared_choice = st.radio(
            "Sharing with others?",
            ["Just me", "Shared", "Not sure"],
            horizontal=True,
        )

        st.markdown(
            "<div style='margin-top:1rem'>"
            "<p style='font-size:0.85rem;font-weight:600;color:#1A1A1A;margin-bottom:4px'>"
            "How much of each dish did you eat?</p>"
            "<p style='font-size:0.78rem;color:#6B7280;margin-bottom:12px'>"
            "Adjust each slider to match how much you actually had.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        item_percent_inputs = {}
        pct_options = [0, 25, 50, 75, 100]
        for item in items:
            name = item["name"]
            qty  = item.get("quantity_desc", "")
            label = f"{name}" + (f" ({qty})" if qty else "")
            val = st.select_slider(
                label,
                options=pct_options,
                value=100,
                format_func=lambda x: f"{x}%",
                key=f"pct_{name}",
            )
            item_percent_inputs[name] = val / 100

        submitted = st.form_submit_button("Estimate nutrition →", type="primary", use_container_width=True)

    if submitted:
        is_homemade = {"Homemade 🏠": True, "Restaurant / takeaway 🏪": False}.get(homemade_choice)
        is_shared   = {"Just me": False, "Shared": True}.get(shared_choice)
        st.session_state.is_homemade   = is_homemade
        st.session_state.is_shared     = is_shared
        st.session_state.item_percents = item_percent_inputs

        with st.spinner("Estimating nutrition…"):
            profile = user_service.get_profile(user_id)
            try:
                result = ai_service.estimate_nutrition(
                    st.session_state.image_b64, st.session_state.media_type,
                    items, is_homemade, item_percent_inputs, is_shared,
                    st.session_state.get("user_notes", ""), profile,
                )
                st.session_state.nutrition_result = result
                st.session_state.step = "confirm"
                st.rerun()
            except Exception as e:
                st.error(f"Estimation failed: {e}")

    if st.button("← Start over"):
        meal_service.delete_meal(st.session_state.meal_id)
        _reset()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Confirm
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == "confirm":
    result     = st.session_state.nutrition_result
    totals     = result.get("totals", {})
    items      = result.get("items", [])
    confidence = result.get("confidence", "medium")
    notes      = result.get("notes", "")
    protein_flag = result.get("protein_flag", False)

    # Confidence badge
    conf_cfg = {
        "high":   ("#D4EAD9", "#3A7D5A", "● High confidence"),
        "medium": ("#FEF3C7", "#B45309", "● Medium confidence"),
        "low":    ("#FEE2E2", "#B91C1C", "● Low confidence"),
    }
    bg, fg, label = conf_cfg.get(confidence, conf_cfg["medium"])
    st.markdown(
        f"<span style='background:{bg};color:{fg};border-radius:99px;"
        f"padding:4px 12px;font-size:0.78rem;font-weight:600'>{label}</span>",
        unsafe_allow_html=True,
    )

    if notes:
        st.caption(f"ℹ️ {notes}")

    if protein_flag:
        st.warning("⚠️ Protein is low for this meal. Consider adding chicken, tofu, eggs, or Greek yogurt.")

    # Low-confidence follow-up
    if confidence == "low":
        with st.expander("🔍 Help AI get a better estimate", expanded=True):
            with st.form("followup_form"):
                extra_detail = st.text_area(
                    "Describe the dishes or quantities in more detail:",
                    placeholder="e.g. the soup has chicken, no noodles; rice is about 150g…",
                    height=90,
                )
                if st.form_submit_button("Re-estimate →", type="primary"):
                    if extra_detail.strip():
                        combined = (st.session_state.get("user_notes", "") + " " + extra_detail).strip()
                        with st.spinner("Re-estimating…"):
                            profile = user_service.get_profile(user_id)
                            try:
                                new_result = ai_service.estimate_nutrition(
                                    st.session_state.image_b64, st.session_state.media_type,
                                    st.session_state.identified.get("items", []),
                                    st.session_state.get("is_homemade"),
                                    st.session_state.get("item_percents", {}),
                                    st.session_state.get("is_shared"),
                                    combined, profile,
                                )
                                st.session_state.nutrition_result = new_result
                                st.session_state.user_notes = combined
                                st.rerun()
                            except Exception as e:
                                st.error(f"Re-estimation failed: {e}")

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
    st.subheader("Estimated nutrition")
    macro_pills_row(totals)

    # Breakdown
    with st.expander("Meal breakdown & AI notes"):
        caption = st.session_state.identified.get("raw_caption", "")
        if caption:
            st.markdown(f"**Identified:** {caption}")
        if notes:
            st.markdown(f"**Assumptions:** {notes}")
        if items:
            st.markdown("---")
            for item in items:
                st.markdown(
                    f"**{item.get('name','')}** ({item.get('quantity_desc','')})  \n"
                    f"`{item.get('calories') or 0:.0f} kcal` · "
                    f"`{item.get('protein_g') or 0:.1f}g P` · "
                    f"`{item.get('carb_g') or 0:.1f}g C` · "
                    f"`{item.get('fat_g') or 0:.1f}g F`"
                )

    # Manual edit
    with st.expander("Edit numbers manually"):
        with st.form("manual_edit"):
            c1, c2 = st.columns(2)
            mc    = c1.number_input("Calories (kcal)", value=float(totals.get("calories") or 0), step=10.0)
            mp    = c2.number_input("Protein (g)",     value=float(totals.get("protein_g") or 0), step=1.0)
            c3, c4 = st.columns(2)
            mcarb = c3.number_input("Carbs (g)",  value=float(totals.get("carb_g") or 0), step=1.0)
            mf    = c4.number_input("Fat (g)",    value=float(totals.get("fat_g") or 0), step=1.0)
            c5, c6 = st.columns(2)
            mfib  = c5.number_input("Fiber (g)",   value=float(totals.get("fiber_g") or 0), step=0.5)
            msod  = c6.number_input("Sodium (mg)", value=float(totals.get("sodium_mg") or 0), step=10.0)
            if st.form_submit_button("Apply edits"):
                result["totals"].update({
                    "calories": mc, "protein_g": mp, "carb_g": mcarb,
                    "fat_g": mf, "fiber_g": mfib, "sodium_mg": msod,
                })
                st.session_state.nutrition_result = result
                st.rerun()

    st.divider()
    col_save, col_back = st.columns([3, 1])
    with col_save:
        if st.button("Save meal ✓", type="primary", use_container_width=True):
            meal_id    = st.session_state.meal_id
            image_path = image_service.persist_image(st.session_state.image_obj, meal_id)
            nutrition_totals = {**totals, "confidence": confidence, "estimate_notes": notes}
            meal_service.save_confirmed_meal(
                meal_id=meal_id, image_path=image_path,
                is_homemade=st.session_state.get("is_homemade"),
                percent_eaten=st.session_state.get("percent_eaten", 1.0),
                is_shared=st.session_state.get("is_shared"),
                raw_description=st.session_state.identified.get("raw_caption", ""),
                ai_notes=notes, nutrition_totals=nutrition_totals, items=items,
            )
            st.success("Meal saved! Head to Today →")
            _reset()
            st.rerun()

    with col_back:
        if st.button("← Redo", use_container_width=True):
            st.session_state.step = "clarify"
            st.rerun()
