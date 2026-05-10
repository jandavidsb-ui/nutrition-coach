-- PostgreSQL schema for NutriCoach (Supabase)
-- All tables use CREATE TABLE IF NOT EXISTS so this is safe to re-run.

CREATE TABLE IF NOT EXISTS user_profile (
    id               SERIAL PRIMARY KEY,
    name             TEXT    NOT NULL DEFAULT 'User',
    sex              TEXT    NOT NULL DEFAULT 'female',
    height_cm        REAL    NOT NULL DEFAULT 163.0,
    weight_kg        REAL,
    age              INTEGER,
    goal             TEXT    NOT NULL DEFAULT 'recomposition',
    target_calories  REAL    NOT NULL DEFAULT 1550.0,
    target_protein_g REAL    NOT NULL DEFAULT 110.0,
    target_fiber_g   REAL    NOT NULL DEFAULT 25.0,
    target_fat_g     REAL,
    target_carb_g    REAL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meals (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL DEFAULT 1,
    logged_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meal_type        TEXT,
    image_path       TEXT,
    is_homemade      INTEGER,
    percent_eaten    REAL,
    is_shared        INTEGER,
    raw_description  TEXT,
    ai_notes         TEXT,
    confirmed        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS meal_nutrition (
    id             SERIAL PRIMARY KEY,
    meal_id        INTEGER NOT NULL UNIQUE REFERENCES meals(id) ON DELETE CASCADE,
    calories       REAL,
    protein_g      REAL,
    carb_g         REAL,
    fat_g          REAL,
    fiber_g        REAL,
    sodium_mg      REAL,
    sugar_g        REAL,
    confidence     TEXT,
    estimate_notes TEXT
);

CREATE TABLE IF NOT EXISTS meal_items (
    id            SERIAL PRIMARY KEY,
    meal_id       INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    item_name     TEXT NOT NULL,
    quantity_desc TEXT,
    calories      REAL,
    protein_g     REAL,
    carb_g        REAL,
    fat_g         REAL,
    fiber_g       REAL,
    sodium_mg     REAL,
    sort_order    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS weight_log (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL DEFAULT 1,
    logged_date DATE NOT NULL,
    weight_kg   REAL NOT NULL,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(logged_date, user_id)
);

CREATE TABLE IF NOT EXISTS exercise_log (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL DEFAULT 1,
    logged_date     DATE NOT NULL,
    description     TEXT NOT NULL,
    calories_burned REAL NOT NULL,
    ai_estimated    INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meals_logged_at   ON meals(logged_at);
CREATE INDEX IF NOT EXISTS idx_meals_user        ON meals(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_items_meal   ON meal_items(meal_id);
CREATE INDEX IF NOT EXISTS idx_exercise_date     ON exercise_log(logged_date, user_id);

-- Seed users (idempotent)
INSERT INTO user_profile
    (id, name, sex, height_cm, weight_kg, goal,
     target_calories, target_protein_g, target_fiber_g, target_fat_g, target_carb_g)
VALUES
    (1, 'Jan',   'female', 163.0, 54.0, 'recomposition', 1550.0, 110.0, 25.0, 52.0, 160.0),
    (2, 'David', 'male',   178.0, 80.0, 'recomposition', 2000.0, 140.0, 25.0, 67.0, 200.0)
ON CONFLICT DO NOTHING;
