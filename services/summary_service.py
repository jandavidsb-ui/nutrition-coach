from datetime import date, timedelta

import config
from db.connection import get_connection


def get_daily_summary(date_str: str, user_id: int = 1) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT
                COUNT(m.id)        AS meal_count,
                SUM(mn.calories)   AS total_calories,
                SUM(mn.protein_g)  AS total_protein,
                SUM(mn.carb_g)     AS total_carb,
                SUM(mn.fat_g)      AS total_fat,
                SUM(mn.fiber_g)    AS total_fiber,
                SUM(mn.sodium_mg)  AS total_sodium,
                SUM(mn.sugar_g)    AS total_sugar
               FROM meals m
               JOIN meal_nutrition mn ON mn.meal_id = m.id
               WHERE m.logged_at::date = %s AND m.confirmed = 1 AND m.user_id = %s""",
            (date_str, user_id),
        ).fetchone()
        return row if row else {}


def get_weekly_trends(days: int = 7, user_id: int = 1) -> list[dict]:
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT
                m.logged_at::date  AS day,
                SUM(mn.calories)   AS total_calories,
                SUM(mn.protein_g)  AS total_protein,
                SUM(mn.carb_g)     AS total_carb,
                SUM(mn.fat_g)      AS total_fat,
                SUM(mn.fiber_g)    AS total_fiber,
                COUNT(m.id)        AS meal_count
               FROM meals m
               JOIN meal_nutrition mn ON mn.meal_id = m.id
               WHERE m.confirmed = 1 AND m.logged_at::date >= %s AND m.user_id = %s
               GROUP BY m.logged_at::date
               ORDER BY day ASC""",
            (start, user_id),
        ).fetchall()
        # Convert date objects to ISO strings for consistent downstream use
        for r in rows:
            if hasattr(r.get("day"), "isoformat"):
                r["day"] = r["day"].isoformat()
        return rows


def get_macro_gaps(date_str: str, profile: dict, user_id: int = 1) -> dict:
    summary = get_daily_summary(date_str, user_id)
    return {
        "calories_remaining": (profile.get("target_calories") or 1550) - (summary.get("total_calories") or 0),
        "protein_remaining":  (profile.get("target_protein_g") or 110) - (summary.get("total_protein") or 0),
        "fiber_remaining":    (profile.get("target_fiber_g") or 25)  - (summary.get("total_fiber") or 0),
        "summary": summary,
    }


def compute_coaching_note(summary: dict, profile: dict) -> str:
    cal_target = profile.get("target_calories") or 1550
    pro_target = profile.get("target_protein_g") or 110
    fib_target = profile.get("target_fiber_g") or 25

    total_cal   = summary.get("total_calories") or 0
    total_pro   = summary.get("total_protein") or 0
    total_fib   = summary.get("total_fiber") or 0
    total_sugar = summary.get("total_sugar") or 0
    meal_count  = summary.get("meal_count") or 0

    from datetime import datetime
    hour = datetime.now().hour

    if meal_count == 0:
        return "Start logging your meals — even a rough photo is better than nothing."

    pro_pct = total_pro / pro_target if pro_target else 0
    fib_pct = total_fib / fib_target if fib_target else 0
    cal_remaining = cal_target - total_cal

    if total_sugar > config.DESSERT_SUGAR_THRESHOLD_G:
        pro_remaining = max(0, pro_target - total_pro)
        return (
            f"You've had {total_sugar:.0f}g sugar today. "
            f"You still need {pro_remaining:.0f}g protein — keep your next meal high-protein "
            f"and skip the extra sweets."
        )

    if hour >= 18 and pro_pct < 0.8:
        pro_gap = pro_target - total_pro
        return (
            f"It's evening and you're at {total_pro:.0f}g protein ({pro_pct:.0%} of target). "
            f"Aim for {pro_gap:.0f}g more — think chicken, tofu, eggs, or Greek yogurt."
        )

    if hour >= 15 and fib_pct < 0.6:
        fib_gap = fib_target - total_fib
        return (
            f"Fiber is low at {total_fib:.0f}g ({fib_pct:.0%} of target). "
            f"Add {fib_gap:.0f}g more — vegetables, beans, or fruit work well at dinner."
        )

    if total_cal > cal_target * 1.05:
        over = total_cal - cal_target
        return (
            f"You're {over:.0f} kcal over your target today. "
            "Keep dinner light — vegetables, lean protein, and no heavy sauces."
        )

    if pro_pct >= 0.7 and total_cal < cal_target * 0.85:
        pro_gap = pro_target - total_pro
        return (
            f"Good pacing — {cal_remaining:.0f} kcal and {pro_gap:.0f}g protein remaining. "
            "A balanced dinner will land you right on target."
        )

    pro_gap = max(0, pro_target - total_pro)
    return f"You need {pro_gap:.0f}g more protein today. Prioritise protein at your next meal."
