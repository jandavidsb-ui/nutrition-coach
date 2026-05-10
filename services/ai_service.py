from __future__ import annotations

import base64
import json
import re

from google import genai
from google.genai import types

import config

_key_index = 0
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client, _key_index
    if _client is None:
        if not config.GEMINI_API_KEYS:
            raise ValueError("No GEMINI_API_KEY set in .env")
        _client = genai.Client(api_key=config.GEMINI_API_KEYS[_key_index])
    return _client


def _rotate_key() -> bool:
    """Switch to the next API key. Returns True if a new key is available."""
    global _client, _key_index
    _key_index += 1
    if _key_index >= len(config.GEMINI_API_KEYS):
        return False
    _client = genai.Client(api_key=config.GEMINI_API_KEYS[_key_index])
    return True


def _generate(model: str, contents: list) -> "types.GenerateContentResponse":
    """Call generate_content with automatic key rotation on quota errors."""
    while True:
        try:
            return _get_client().models.generate_content(model=model, contents=contents)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if _rotate_key():
                    continue
            raise


def _build_system_prompt(user_profile: dict) -> str:
    return f"""You are a precise nutrition analyst and supportive coach for a specific person.

USER PROFILE:
- Female, {user_profile.get('height_cm', 163)} cm, ~{user_profile.get('weight_kg', 54)} kg
- Goal: body recomposition (lean, sustainable fat loss while preserving muscle)
- Daily targets: {user_profile.get('target_calories', 1550)} kcal | {user_profile.get('target_protein_g', 110)}g protein | {user_profile.get('target_fiber_g', 25)}g fiber
- Training: weight training 2×/week, daily walking/cardio
- Cuisine: mostly homemade Thai, Vietnamese, and Asian food
- Known challenge: dessert cravings after meals

ESTIMATION RULES:
1. Homemade meals: reduce estimated oil/fat by ~25-30% and sodium by ~30% vs restaurant.
2. Apply percent_eaten multiplier to ALL macros before returning totals.
3. If is_shared is true, already assume the user's portion is one person's share.
4. Flag protein_flag=true when protein < 20g for breakfast, lunch, or dinner.
5. Prioritize accuracy on protein. When in doubt, estimate slightly lower on calories.
6. For Thai/Vietnamese dishes: use authentic home-cooking portion sizes.

COACHING TONE: analytical, direct, non-toxic. Support progress, not perfection."""


def _parse_json_response(raw: str) -> dict:
    match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON in AI response: {raw[:200]}")


def _image_part(image_b64: str, media_type: str) -> types.Part:
    return types.Part.from_bytes(
        data=base64.b64decode(image_b64),
        mime_type=media_type,
    )


def estimate_exercise_calories(description: str, user_profile: dict) -> dict:
    """Estimate calories burned from a plain-text activity description."""

    prompt = (
        _build_system_prompt(user_profile) + "\n\n"
        f'The user did the following activity today: "{description}"\n\n'
        "Estimate the calories burned. Consider the user's weight and the activity intensity.\n"
        "Respond with JSON only:\n```json\n"
        '{"calories_burned": 250, "notes": "brief one-line explanation"}\n```'
    )
    response = _generate(
        model=config.GEMINI_MODEL,
        contents=[prompt],
    )
    result = _parse_json_response(response.text)
    result.setdefault("calories_burned", 0)
    result.setdefault("notes", "")
    return result


def generate_coaching_message(
    food_summary: dict,
    exercise_summary: dict,
    profile: dict,
    net_calories: float,
) -> str:
    """Generate a short AI coaching message for the day."""

    cal_target = profile.get("target_calories") or 1550
    pro_target = profile.get("target_protein_g") or 110
    prompt = (
        _build_system_prompt(profile) + "\n\n"
        "Today's data:\n"
        f"- Calories eaten: {food_summary.get('total_calories') or 0:.0f} kcal\n"
        f"- Protein eaten: {food_summary.get('total_protein') or 0:.0f}g (target: {pro_target}g)\n"
        f"- Calories burned from exercise: {exercise_summary.get('total_burned') or 0:.0f} kcal\n"
        f"- Net calories: {net_calories:.0f} kcal (target: {cal_target} kcal)\n"
        f"- Meals logged: {food_summary.get('meal_count') or 0}\n"
        f"- Exercise sessions: {exercise_summary.get('count') or 0}\n\n"
        "Write ONE short coaching message (1-2 sentences max). Be direct and specific. "
        "Acknowledge exercise if done. Flag if protein is low or net calories are way off. "
        "Tone: supportive but honest. Respond with plain text only — no JSON, no bullets."
    )
    response = _generate(
        model=config.GEMINI_MODEL,
        contents=[prompt],
    )
    return response.text.strip()


def analyze_image(image_b64: str, media_type: str, user_profile: dict) -> dict:
    """Call 1: Identify dishes."""

    prompt = (
        _build_system_prompt(user_profile) + "\n\n"
        "Identify all the dishes and foods visible in this photo. "
        "Be specific about preparation method (stir-fried, steamed, grilled, etc.). "
        "Respond with JSON only:\n"
        "```json\n"
        '{"items": [{"name": "...", "quantity_desc": "e.g. 1 bowl, half plate"}], '
        '"raw_caption": "one sentence describing the overall meal"}\n'
        "```"
    )
    response = _generate(
        model=config.GEMINI_MODEL,
        contents=[_image_part(image_b64, media_type), prompt],
    )
    return _parse_json_response(response.text)


def estimate_nutrition(
    image_b64: str,
    media_type: str,
    identified_items: list[dict],
    is_homemade: bool | None,
    item_percents: dict[str, float],
    is_shared: bool | None,
    extra_notes: str,
    user_profile: dict,
) -> dict:
    """Call 2: Full nutrition estimate with per-item consumption percentages."""


    homemade_str = "yes" if is_homemade else ("no (restaurant)" if is_homemade is False else "unknown")
    shared_str   = "yes" if is_shared else ("no" if is_shared is False else "unknown")

    item_lines = []
    for item in identified_items:
        name = item["name"]
        pct  = int(item_percents.get(name, 1.0) * 100)
        item_lines.append(f"  - {name}: ate {pct}% of this dish")

    context = (
        f"- Homemade: {homemade_str}\n"
        f"- Shared meal: {shared_str}\n"
        f"- Per-dish consumption:\n" + "\n".join(item_lines)
    )
    if extra_notes:
        context += f"\n- Additional notes: {extra_notes}"

    schema = """{
  "items": [{"name":"","quantity_desc":"","calories":0,"protein_g":0,"carb_g":0,"fat_g":0,"fiber_g":0,"sodium_mg":0}],
  "totals": {"calories":0,"protein_g":0,"carb_g":0,"fat_g":0,"fiber_g":0,"sodium_mg":0,"sugar_g":0},
  "confidence": "high|medium|low",
  "notes": "assumptions made",
  "protein_flag": false
}"""

    prompt = (
        _build_system_prompt(user_profile) + "\n\n"
        "Estimate nutrition for this meal. Each dish has its own consumption percentage — "
        "apply it individually before summing totals:\n\n"
        + context + "\n\n"
        "IMPORTANT:\n"
        "- Apply each dish's percentage to THAT dish's macros individually.\n"
        "- Totals = sum of all adjusted per-dish values.\n"
        + ("- Homemade: reduce fat/sodium by ~25-30% vs restaurant.\n" if is_homemade else "")
        + "- Set protein_flag=true if total protein < 20g for a main meal.\n\n"
        f"Respond with JSON only:\n```json\n{schema}\n```"
    )

    response = _generate(
        model=config.GEMINI_MODEL,
        contents=[_image_part(image_b64, media_type), prompt],
    )
    result = _parse_json_response(response.text)
    result.setdefault("totals", {})
    result.setdefault("items", [])
    result.setdefault("confidence", "medium")
    result.setdefault("notes", "")
    result.setdefault("protein_flag", False)
    return result


def check_food(
    image_b64: str,
    media_type: str,
    user_note: str,
    food_summary: dict,
    exercise_summary: dict,
    profile: dict,
) -> dict:
    """Analyse a food photo and rate whether the user should eat it today."""


    cal_target  = profile.get("target_calories") or 1550
    pro_target  = profile.get("target_protein_g") or 110
    eaten_cal   = food_summary.get("total_calories") or 0
    eaten_pro   = food_summary.get("total_protein") or 0
    burned_cal  = exercise_summary.get("total_burned") or 0
    net_cal     = eaten_cal - burned_cal
    cal_left    = cal_target - net_cal
    meal_count  = food_summary.get("meal_count") or 0
    ex_count    = exercise_summary.get("count") or 0

    context = (
        f"TODAY'S CONTEXT:\n"
        f"- Calories eaten so far: {eaten_cal:.0f} kcal\n"
        f"- Calories burned (exercise): {burned_cal:.0f} kcal\n"
        f"- Net calories: {net_cal:.0f} kcal (budget remaining: {cal_left:.0f} kcal)\n"
        f"- Protein eaten: {eaten_pro:.0f}g / {pro_target}g target\n"
        f"- Meals logged today: {meal_count}\n"
        f"- Exercise sessions today: {ex_count}\n"
    )
    if user_note:
        context += f"- User note about this food: {user_note}\n"

    schema = """{
  "food_name": "brief name of the food in the image",
  "rating": 3,
  "rating_label": "Okay",
  "reasoning": "2-3 sentences explaining the rating in context of today's data",
  "suggested_percent": 100,
  "suggested_percent_reason": "one short sentence why this portion is recommended",
  "nutrition_estimate": {
    "calories": 0, "protein_g": 0, "carb_g": 0, "fat_g": 0, "fiber_g": 0
  },
  "exercise_suggestions": []
}"""

    prompt = (
        _build_system_prompt(profile) + "\n\n"
        + context + "\n"
        "TASK: The user is considering eating the food in this photo. "
        "Rate whether they should eat it RIGHT NOW based on their remaining budget and goals.\n\n"
        "RATING SCALE (pick exactly one):\n"
        "  5 = Excellent — fits perfectly, highly recommended\n"
        "  4 = Good — solid choice for your goals\n"
        "  3 = Okay — fine, won't hurt, not ideal\n"
        "  2 = Think Twice — consider a better alternative\n"
        "  1 = Avoid — doesn't fit your budget or goals today\n\n"
        "RULES:\n"
        "- Use rating_label matching the number: Excellent/Good/Okay/Think Twice/Avoid\n"
        "- Keep reasoning direct and specific to today's data (2-3 sentences max)\n"
        "- suggested_percent: recommend what % of the FULL portion shown the user should eat "
        "(e.g. 50 if the portion is too large for their remaining budget, 100 if it fits fine). "
        "Must be one of: 25, 50, 75, 100\n"
        "- suggested_percent_reason: one short sentence explaining the portion recommendation\n"
        "- If rating <= 2 AND exercise sessions today == 0: suggest exactly 2 exercises "
        "the user could do to compensate, e.g. [{\"name\": \"Brisk walk\", \"duration\": \"30 min\", "
        "\"calories_burned\": 150}]. Otherwise leave exercise_suggestions as empty array []\n"
        "- nutrition_estimate = nutrition for the FULL 100% portion shown in the image\n\n"
        f"Respond with JSON only:\n```json\n{schema}\n```"
    )

    response = _generate(
        model=config.GEMINI_MODEL,
        contents=[_image_part(image_b64, media_type), prompt],
    )
    result = _parse_json_response(response.text)
    result.setdefault("food_name", "This food")
    result.setdefault("rating", 3)
    result.setdefault("rating_label", "Okay")
    result.setdefault("reasoning", "")
    result.setdefault("suggested_percent", 100)
    result.setdefault("suggested_percent_reason", "")
    result.setdefault("nutrition_estimate", {})
    result.setdefault("exercise_suggestions", [])
    return result


def analyse_history(trends: list[dict], period: str, profile: dict) -> dict:
    """Rate the user's nutrition performance over a period and give advice."""
    client = _get_client()  # noqa: F841 — used via _generate
    cal_target = profile.get("target_calories") or 1550
    pro_target = profile.get("target_protein_g") or 110
    fib_target = profile.get("target_fiber_g") or 25

    n = len(trends)
    if n == 0:
        return {"stars": 0, "label": "No data", "summary": "", "tips": []}

    avg_cal  = sum(r.get("total_calories") or 0 for r in trends) / n
    avg_pro  = sum(r.get("total_protein")  or 0 for r in trends) / n
    avg_fib  = sum(r.get("total_fiber")    or 0 for r in trends) / n
    days_logged = sum(1 for r in trends if (r.get("meal_count") or 0) > 0)

    rows = "\n".join(
        f"  {r['day']}: {r.get('total_calories') or 0:.0f} kcal, "
        f"{r.get('total_protein') or 0:.0f}g protein, "
        f"{r.get('total_fiber') or 0:.1f}g fiber, "
        f"{r.get('meal_count') or 0} meals"
        for r in trends
    )

    schema = """{
  "stars": 4,
  "label": "Good",
  "summary": "2-3 sentence overall assessment",
  "tips": ["specific tip 1", "specific tip 2"]
}"""

    prompt = (
        _build_system_prompt(profile) + "\n\n"
        f"TASK: Evaluate this user's nutrition performance for the past {period}.\n\n"
        f"TARGETS: {cal_target:.0f} kcal | {pro_target:.0f}g protein | {fib_target:.0f}g fiber\n\n"
        f"DATA ({n} days, {days_logged} days with meals logged):\n{rows}\n\n"
        f"AVERAGES: {avg_cal:.0f} kcal | {avg_pro:.0f}g protein | {avg_fib:.1f}g fiber\n\n"
        "STAR RATING SCALE:\n"
        "  5 = Excellent — consistently hit all targets\n"
        "  4 = Good — mostly on track, minor gaps\n"
        "  3 = Okay — some good days, inconsistent\n"
        "  2 = Needs work — regularly missing key targets\n"
        "  1 = Poor — significantly off track most days\n\n"
        "RULES:\n"
        "- Be honest but constructive\n"
        "- summary: 2-3 sentences referencing actual numbers\n"
        "- tips: exactly 2 specific, actionable tips based on the data\n"
        "- label: one word matching the stars (Excellent/Good/Okay/Needs work/Poor)\n\n"
        f"Respond with JSON only:\n```json\n{schema}\n```"
    )

    response = _generate(model=config.GEMINI_MODEL, contents=[prompt])
    result = _parse_json_response(response.text)
    result.setdefault("stars", 3)
    result.setdefault("label", "Okay")
    result.setdefault("summary", "")
    result.setdefault("tips", [])
    return result
