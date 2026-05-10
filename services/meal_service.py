from __future__ import annotations

from db.connection import get_connection


def create_meal_stub(meal_type: str | None = None, user_id: int = 1) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO meals (meal_type, confirmed, user_id) VALUES (%s, 0, %s) RETURNING id",
            (meal_type, user_id),
        )
        conn.commit()
        return cur.fetchone()["id"]


def save_confirmed_meal(
    meal_id: int,
    image_path: str,
    is_homemade: bool | None,
    percent_eaten: float,
    is_shared: bool | None,
    raw_description: str,
    ai_notes: str,
    nutrition_totals: dict,
    items: list[dict],
) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE meals SET
                image_path      = %s,
                is_homemade     = %s,
                percent_eaten   = %s,
                is_shared       = %s,
                raw_description = %s,
                ai_notes        = %s,
                confirmed       = 1
               WHERE id = %s""",
            (
                image_path,
                int(is_homemade) if is_homemade is not None else None,
                percent_eaten,
                int(is_shared) if is_shared is not None else None,
                raw_description,
                ai_notes,
                meal_id,
            ),
        )

        conn.execute(
            """INSERT INTO meal_nutrition
               (meal_id, calories, protein_g, carb_g, fat_g, fiber_g,
                sodium_mg, sugar_g, confidence, estimate_notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (meal_id) DO UPDATE SET
                 calories       = EXCLUDED.calories,
                 protein_g      = EXCLUDED.protein_g,
                 carb_g         = EXCLUDED.carb_g,
                 fat_g          = EXCLUDED.fat_g,
                 fiber_g        = EXCLUDED.fiber_g,
                 sodium_mg      = EXCLUDED.sodium_mg,
                 sugar_g        = EXCLUDED.sugar_g,
                 confidence     = EXCLUDED.confidence,
                 estimate_notes = EXCLUDED.estimate_notes""",
            (
                meal_id,
                nutrition_totals.get("calories"),
                nutrition_totals.get("protein_g"),
                nutrition_totals.get("carb_g"),
                nutrition_totals.get("fat_g"),
                nutrition_totals.get("fiber_g"),
                nutrition_totals.get("sodium_mg"),
                nutrition_totals.get("sugar_g"),
                nutrition_totals.get("confidence"),
                nutrition_totals.get("estimate_notes"),
            ),
        )

        for i, item in enumerate(items):
            conn.execute(
                """INSERT INTO meal_items
                   (meal_id, item_name, quantity_desc, calories, protein_g,
                    carb_g, fat_g, fiber_g, sodium_mg, sort_order)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    meal_id,
                    item.get("name", ""),
                    item.get("quantity_desc"),
                    item.get("calories"),
                    item.get("protein_g"),
                    item.get("carb_g"),
                    item.get("fat_g"),
                    item.get("fiber_g"),
                    item.get("sodium_mg"),
                    i,
                ),
            )

        conn.commit()


def get_meals_for_date(date_str: str, user_id: int = 1) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT m.*, mn.calories, mn.protein_g, mn.carb_g, mn.fat_g,
                      mn.fiber_g, mn.sodium_mg, mn.sugar_g, mn.confidence
               FROM meals m
               LEFT JOIN meal_nutrition mn ON mn.meal_id = m.id
               WHERE m.logged_at::date = %s AND m.confirmed = 1 AND m.user_id = %s
               ORDER BY m.logged_at""",
            (date_str, user_id),
        ).fetchall()
        return rows


def get_meal_items(meal_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM meal_items WHERE meal_id = %s ORDER BY sort_order",
            (meal_id,),
        ).fetchall()
        return rows


def delete_meal(meal_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM meals WHERE id = %s", (meal_id,))
        conn.commit()


def update_meal_nutrition(meal_id: int, nutrition: dict) -> None:
    if not nutrition:
        return
    cols = ", ".join(f"{k} = %s" for k in nutrition)
    values = list(nutrition.values()) + [meal_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE meal_nutrition SET {cols} WHERE meal_id = %s", values)
        conn.commit()


def delete_unconfirmed_stubs(user_id: int = 1) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM meals WHERE confirmed = 0 AND user_id = %s", (user_id,))
        conn.commit()
