"""Display and formatting helpers used across pages."""
from __future__ import annotations

from datetime import datetime


def format_kcal(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f} kcal"


def format_g(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f} g"


def format_mg(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f} mg"


def format_time(iso_str: str) -> str:
    """Extract HH:MM from an ISO datetime string."""
    try:
        return iso_str[11:16]
    except Exception:
        return ""


def format_date_display(date_str: str) -> str:
    """'2026-05-09' → 'Friday, 9 May 2026'"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A, %-d %B %Y")
    except Exception:
        return date_str


def pct_bar_color(pct: float) -> str:
    """Return a CSS color based on how close to target."""
    if pct >= 1.0:
        return "#2ECC71"   # green — hit target
    if pct >= 0.75:
        return "#F39C12"   # amber — almost there
    return "#E74C3C"       # red — well below
