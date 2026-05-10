import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Secrets: st.secrets (cloud) → os.getenv (local .env) ─────────────────────
def _secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

# ── Paths (local fallback only) ───────────────────────────────────────────────
ROOT_DIR    = Path(__file__).parent
UPLOADS_DIR = ROOT_DIR / "uploads"
SCHEMA_PATH = ROOT_DIR / "db" / "schema.sql"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = _secret("DATABASE_URL")

# ── Supabase Storage ──────────────────────────────────────────────────────────
SUPABASE_URL = _secret("SUPABASE_URL")
SUPABASE_KEY = _secret("SUPABASE_KEY")
SUPABASE_BUCKET = "meal-images"

# ── AI ────────────────────────────────────────────────────────────────────────
GEMINI_API_KEYS = [
    k for k in [
        _secret("GEMINI_API_KEY_1"),
        _secret("GEMINI_API_KEY_2"),
        _secret("GEMINI_API_KEY_3"),
    ] if k and not k.startswith("ใส่")
]
GEMINI_MODEL = "gemini-2.5-flash"

# ── Coaching thresholds ───────────────────────────────────────────────────────
PROTEIN_FLAG_G          = 20
DESSERT_SUGAR_THRESHOLD_G = 20
MAX_IMAGE_MB            = 10
ALLOWED_IMAGE_TYPES     = {"image/jpeg", "image/png", "image/webp"}
