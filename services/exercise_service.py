from __future__ import annotations

from db.connection import get_connection


def log_exercise(
    user_id: int,
    date_str: str,
    description: str,
    calories_burned: float,
    ai_estimated: bool = True,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO exercise_log (user_id, logged_date, description, calories_burned, ai_estimated)"
            " VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user_id, date_str, description, calories_burned, 1 if ai_estimated else 0),
        )
        conn.commit()
        return cur.fetchone()["id"]


def get_exercises_for_date(date_str: str, user_id: int = 1) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM exercise_log WHERE logged_date = %s AND user_id = %s ORDER BY created_at",
            (date_str, user_id),
        ).fetchall()
        return rows


def delete_exercise(exercise_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM exercise_log WHERE id = %s", (exercise_id,))
        conn.commit()


def get_daily_exercise_summary(date_str: str, user_id: int = 1) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count, SUM(calories_burned) AS total_burned"
            " FROM exercise_log WHERE logged_date = %s AND user_id = %s",
            (date_str, user_id),
        ).fetchone()
        return {
            "count": row["count"] or 0 if row else 0,
            "total_burned": row["total_burned"] or 0.0 if row else 0.0,
        }
