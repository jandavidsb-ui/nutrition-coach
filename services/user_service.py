from datetime import date

from db.connection import get_connection


def get_all_users() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name FROM user_profile ORDER BY id").fetchall()
        return rows


def get_profile(user_id: int = 1) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM user_profile WHERE id = %s", (user_id,)).fetchone()
        return row if row else {}


def update_profile(fields: dict, user_id: int = 1) -> None:
    if not fields:
        return
    fields["updated_at"] = date.today().isoformat()
    cols = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values())
    with get_connection() as conn:
        conn.execute(f"UPDATE user_profile SET {cols} WHERE id = %s", values + [user_id])
        conn.commit()


def log_weight(weight_kg: float, date_str: str, notes: str = "", user_id: int = 1) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO weight_log (logged_date, weight_kg, notes, user_id)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (logged_date, user_id) DO UPDATE SET
                 weight_kg = EXCLUDED.weight_kg,
                 notes     = EXCLUDED.notes""",
            (date_str, weight_kg, notes, user_id),
        )
        conn.commit()


def get_weight_log(days: int = 30, user_id: int = 1) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT logged_date, weight_kg, notes
               FROM weight_log
               WHERE user_id = %s
               ORDER BY logged_date DESC
               LIMIT %s""",
            (user_id, days),
        ).fetchall()
        # Convert date objects to strings
        for r in rows:
            if hasattr(r.get("logged_date"), "isoformat"):
                r["logged_date"] = r["logged_date"].isoformat()
        return rows
