import streamlit as st


def _ring_svg(pct: float, color: str, size: int = 60) -> str:
    r = 24
    circ = 2 * 3.14159 * r
    fill = min(pct, 1.0) * circ
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 60 60">'
        f'<circle cx="30" cy="30" r="{r}" fill="none" stroke="#E8E5E1" stroke-width="6"/>'
        f'<circle cx="30" cy="30" r="{r}" fill="none" stroke="{color}" stroke-width="6"'
        f' stroke-dasharray="{fill:.1f} {circ:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 30 30)"/>'
        f'</svg>'
    )


def macro_progress(label: str, current: float, target: float,
                   unit: str = "g", color: str = "#5C8D72", is_primary: bool = False):
    if not target:
        return
    pct = min(current / target, 1.0)
    remaining = max(target - current, 0)

    if pct >= 1.0:
        status_color = "#5C8D72"
        status = "Goal reached ✓"
    elif pct >= 0.75:
        status_color = "#F59E0B"
        status = f"{remaining:.0f}{unit} left"
    else:
        status_color = "#9CA3AF"
        status = f"{remaining:.0f}{unit} left"

    weight = "700" if is_primary else "500"
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>"
        f"{_ring_svg(pct, color, 48)}"
        f"<div>"
        f"<div style='font-size:0.85rem;font-weight:{weight};color:#1A1A1A'>{label}</div>"
        f"<div style='font-size:0.8rem;color:#6B7280'>"
        f"{current:.0f} / {target:.0f}{unit} "
        f"<span style='color:{status_color};font-weight:500'>· {status}</span></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    st.progress(pct)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def macro_summary_row(summary: dict, profile: dict):
    cal_target = profile.get("target_calories") or 1550
    pro_target = profile.get("target_protein_g") or 110
    fib_target = profile.get("target_fiber_g") or 25
    carb_target = profile.get("target_carb_g") or 160
    fat_target  = profile.get("target_fat_g") or 52

    total_cal  = summary.get("total_calories") or 0
    total_pro  = summary.get("total_protein") or 0
    total_fib  = summary.get("total_fiber") or 0
    total_carb = summary.get("total_carb") or 0
    total_fat  = summary.get("total_fat") or 0

    macro_progress("Calories", total_cal,  cal_target, unit=" kcal", color="#E05C5C")
    macro_progress("Protein",  total_pro,  pro_target, unit="g", color="#3B82F6", is_primary=True)
    macro_progress("Fiber",    total_fib,  fib_target, unit="g", color="#5C8D72")

    with st.expander("Carbs & Fat"):
        macro_progress("Carbs", total_carb, carb_target, unit="g", color="#F59E0B")
        macro_progress("Fat",   total_fat,  fat_target,  unit="g", color="#8B5CF6")
