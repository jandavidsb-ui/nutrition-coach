from __future__ import annotations

import psycopg2
import psycopg2.extras

import config


class _Cursor:
    """Thin wrapper so service code can call .fetchall() / .fetchone() / .fetchone()[key]."""

    def __init__(self, cur: psycopg2.extensions.cursor) -> None:
        self._cur = cur

    def fetchall(self) -> list[dict]:
        rows = self._cur.fetchall()
        return [dict(r) for r in rows] if rows else []

    def fetchone(self) -> dict | None:
        row = self._cur.fetchone()
        return dict(row) if row else None

    def __iter__(self):
        for row in self._cur:
            yield dict(row)


class _Conn:
    """Context-manager wrapper around a psycopg2 connection.

    Exposes the same .execute() / .commit() interface used by all services.
    """

    def __init__(self, pg_conn: psycopg2.extensions.connection) -> None:
        self._conn = pg_conn

    def execute(self, sql: str, params: tuple = ()) -> _Cursor:
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return _Cursor(cur)

    def executemany(self, sql: str, seq) -> None:
        cur = self._conn.cursor()
        cur.executemany(sql, seq)

    def commit(self) -> None:
        self._conn.commit()

    def __enter__(self) -> "_Conn":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type:
            self._conn.rollback()
        self._conn.close()
        return False


def get_connection() -> _Conn:
    url = config.DATABASE_URL
    # Ensure SSL is required for cloud deployments (Supabase needs this)
    if "sslmode" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    pg_conn = psycopg2.connect(url)
    return _Conn(pg_conn)


def init_db() -> None:
    """Create all tables (idempotent) and seed default users."""
    schema = config.SCHEMA_PATH.read_text()
    with get_connection() as conn:
        # psycopg2 doesn't have executescript; run each statement individually
        for stmt in schema.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
