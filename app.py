import streamlit as st
from db.connection import init_db
from services.user_service import get_all_users
from utils.styles import inject_css

st.set_page_config(
    page_title="NutriCoach",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_db()

# ── User switcher ─────────────────────────────────────────────────────────────
users    = get_all_users()
names    = [u["name"] for u in users]
id_map   = {u["name"]: u["id"] for u in users}
colors   = ["#5C8D72", "#5B8DEF", "#E05C5C", "#F59E0B"]

if "active_user" not in st.session_state:
    st.session_state.active_user = names[0]

with st.sidebar:
    st.markdown(
        "<p style='font-size:0.7rem;font-weight:600;color:#9CA3AF;"
        "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Who's logging?</p>",
        unsafe_allow_html=True,
    )

    avatar_html = '<div style="display:flex;gap:8px;margin-bottom:1rem">'
    for i, name in enumerate(names):
        color = colors[i % len(colors)]
        initial = name[0].upper()
        is_active = name == st.session_state.active_user
        border = f"3px solid {color}" if is_active else "3px solid transparent"
        opacity = "1" if is_active else "0.4"
        avatar_html += (
            f'<div style="width:40px;height:40px;border-radius:50%;background:{color}20;'
            f'border:{border};display:flex;align-items:center;justify-content:center;'
            f'font-weight:700;font-size:1rem;color:{color};opacity:{opacity}">{initial}</div>'
        )
    avatar_html += "</div>"
    st.markdown(avatar_html, unsafe_allow_html=True)

    selected = st.radio(
        "user",
        names,
        index=names.index(st.session_state.active_user),
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected != st.session_state.active_user:
        st.session_state.active_user = selected
        keys_to_clear = [k for k in st.session_state if k.startswith("history_analysis_")]
        keys_to_clear += ["meal_id", "image_obj", "image_b64", "media_type",
                          "identified", "nutrition_result", "step",
                          "is_homemade", "percent_eaten", "is_shared", "user_notes",
                          "coaching_message",
                          "fc_result", "fc_image_obj", "fc_image_b64", "fc_media_type", "fc_note"]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
        st.rerun()

    st.session_state.user_id = id_map[st.session_state.active_user]
    st.divider()

# ── Navigation ────────────────────────────────────────────────────────────────
pages = {
    "Log Meal": [
        st.Page("pages/1_log_meal.py", title="Log Meal", icon="📷"),
        st.Page("pages/5_food_check.py", title="Should I eat this?", icon="🤔"),
    ],
    "Insights": [
        st.Page("pages/2_daily_summary.py", title="Today", icon="📊"),
        st.Page("pages/3_history.py", title="History", icon="📈"),
    ],
    "Settings": [
        st.Page("pages/4_profile.py", title="My Profile", icon="👤"),
    ],
}

pg = st.navigation(pages)
pg.run()
