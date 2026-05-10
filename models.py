from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class NutritionTotals:
    calories: float | None = None
    protein_g: float | None = None
    carb_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    confidence: str = "medium"
    estimate_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carb_g": self.carb_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g,
            "sodium_mg": self.sodium_mg,
            "sugar_g": self.sugar_g,
            "confidence": self.confidence,
            "estimate_notes": self.estimate_notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> NutritionTotals:
        return cls(
            calories=d.get("calories"),
            protein_g=d.get("protein_g"),
            carb_g=d.get("carb_g"),
            fat_g=d.get("fat_g"),
            fiber_g=d.get("fiber_g"),
            sodium_mg=d.get("sodium_mg"),
            sugar_g=d.get("sugar_g"),
            confidence=d.get("confidence", "medium"),
            estimate_notes=d.get("notes", d.get("estimate_notes", "")),
        )


@dataclass
class MealItem:
    name: str
    quantity_desc: str = ""
    calories: float | None = None
    protein_g: float | None = None
    carb_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "quantity_desc": self.quantity_desc,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carb_g": self.carb_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g,
            "sodium_mg": self.sodium_mg,
        }


@dataclass
class AIAnalysisResult:
    """Output from the two-step AI pipeline."""
    items: list[MealItem] = field(default_factory=list)
    totals: NutritionTotals = field(default_factory=NutritionTotals)
    raw_caption: str = ""
    protein_flag: bool = False
    needs_followup: bool = False

    @classmethod
    def from_estimate_dict(cls, d: dict) -> AIAnalysisResult:
        items = [
            MealItem(
                name=i.get("name", ""),
                quantity_desc=i.get("quantity_desc", ""),
                calories=i.get("calories"),
                protein_g=i.get("protein_g"),
                carb_g=i.get("carb_g"),
                fat_g=i.get("fat_g"),
                fiber_g=i.get("fiber_g"),
                sodium_mg=i.get("sodium_mg"),
            )
            for i in d.get("items", [])
        ]
        totals = NutritionTotals.from_dict(d.get("totals", {}))
        totals.confidence = d.get("confidence", "medium")
        totals.estimate_notes = d.get("notes", "")
        return cls(
            items=items,
            totals=totals,
            raw_caption=d.get("raw_caption", ""),
            protein_flag=d.get("protein_flag", False),
            needs_followup=d.get("confidence", "medium") == "low",
        )


@dataclass
class UserProfile:
    id: int = 1
    name: str = "User"
    sex: str = "female"
    height_cm: float = 163.0
    weight_kg: float = 54.0
    goal: str = "recomposition"
    target_calories: float = 1550.0
    target_protein_g: float = 110.0
    target_fiber_g: float = 25.0
    target_fat_g: float = 52.0
    target_carb_g: float = 160.0

    @classmethod
    def from_dict(cls, d: dict) -> UserProfile:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
