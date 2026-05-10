"""Nutrition math helpers."""
from __future__ import annotations


def estimated_tdee(weight_kg: float, height_cm: float, age: int = 28,
                   sex: str = "female", activity: str = "moderate") -> float:
    """Mifflin-St Jeor BMR × activity multiplier."""
    if sex == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return bmr * multipliers.get(activity, 1.55)


def protein_target(weight_kg: float, goal: str = "recomposition") -> float:
    """Recommended protein in grams based on goal."""
    multipliers = {
        "recomposition": 2.0,
        "fat_loss": 2.2,
        "maintenance": 1.6,
        "muscle_gain": 2.0,
    }
    return weight_kg * multipliers.get(goal, 2.0)


def calorie_target(tdee: float, goal: str = "recomposition") -> float:
    """Calorie target with appropriate deficit/surplus."""
    offsets = {
        "recomposition": -200,
        "fat_loss": -400,
        "maintenance": 0,
        "muscle_gain": +200,
    }
    return tdee + offsets.get(goal, -200)


def macro_pct(current: float | None, target: float | None) -> float:
    """Returns 0.0–1.0 progress fraction; clamps at 1.0."""
    if not current or not target:
        return 0.0
    return min(current / target, 1.0)
