import streamlit as st
import config


def meal_card(meal: dict, on_delete=None):
    logged_at = meal.get("logged_at", "")
    # logged_at may be a datetime object (from psycopg2) or a string
    if hasattr(logged_at, "strftime"):
        time_str = logged_at.strftime("%H:%M")
    else:
        time_str = str(logged_at)[11:16] if len(str(logged_at)) >= 16 else ""

    meal_type = (meal.get("meal_type") or "meal").title()
    calories  = meal.get("calories") or 0
    protein   = meal.get("protein_g") or 0
    carbs     = meal.get("carb_g") or 0
    fat       = meal.get("fat_g") or 0

    with st.container(border=True):
        img_col, info_col = st.columns([1, 3])

        with img_col:
            image_path = meal.get("image_path")
            if image_path:
                if image_path.startswith("http"):
                    st.image(image_path, use_container_width=True)
                else:
                    full_path = config.ROOT_DIR / image_path
                    if full_path.exists():
                        st.image(str(full_path), use_container_width=True)
                    else:
                        st.markdown("📷")
            else:
                st.markdown("📷")

        with info_col:
            st.markdown(f"**{time_str} · {meal_type}**")
            description = meal.get("raw_description", "")
            if description:
                st.caption(description)
            st.markdown(
                f"`{calories:.0f} kcal` &nbsp; `{protein:.1f}g protein` &nbsp; "
                f"`{carbs:.1f}g carbs` &nbsp; `{fat:.1f}g fat`"
            )
            if meal.get("is_homemade") == 1:
                st.caption("🏠 Homemade")
            if meal.get("percent_eaten") and meal["percent_eaten"] < 1.0:
                st.caption(f"Ate {int(meal['percent_eaten'] * 100)}% of the dish")

        if on_delete:
            if st.button("Delete", key=f"del_{meal['id']}"):
                on_delete(meal["id"])
