"""Database layer for ArcValet.

All SQLite logic is centralized here.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parent / "arcvalet.db"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _normalize_plate(plate: str) -> str:
    return "".join((plate or "").strip().upper().split())


def init_db() -> None:
    """Create tables and seed spots exactly once when empty."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spots (
                spot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                spot_type TEXT NOT NULL CHECK(spot_type IN ('standard', 'quick_exit', 'luxury', 'bike', 'ev')),
                status TEXT NOT NULL CHECK(status IN ('available', 'occupied')),
                hourly_rate REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                spot_id INTEGER NOT NULL,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                total_amount REAL,
                status TEXT NOT NULL CHECK(status IN ('active', 'completed')),
                FOREIGN KEY (spot_id) REFERENCES spots(spot_id)
            )
            """
        )

        existing_spots = conn.execute("SELECT COUNT(*) AS count FROM spots").fetchone()["count"]
        if existing_spots == 0:
            seed_rows = []
            seed_rows.extend([("standard", "available", 30.0)] * 5)
            seed_rows.extend([("quick_exit", "available", 60.0)] * 3)
            seed_rows.extend([("luxury", "available", 150.0)] * 2)
            seed_rows.extend([("bike", "available", 8.0)] * 5)
            seed_rows.extend([("ev", "available", 40.0)] * 2)

            conn.executemany(
                "INSERT INTO spots (spot_type, status, hourly_rate) VALUES (?, ?, ?)",
                seed_rows,
            )


def get_available_spot(spot_type: str) -> dict[str, Any] | None:
    """Return the best available spot of the requested type (lowest spot_id)."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT spot_id, spot_type, status, hourly_rate
            FROM spots
            WHERE spot_type = ? AND status = 'available'
            ORDER BY spot_id ASC
            LIMIT 1
            """,
            (spot_type,),
        ).fetchone()
    return dict(row) if row else None


def create_session(plate: str, vehicle_type: str, spot_id: int) -> int:
    """Insert an active session and mark the spot occupied in one transaction."""
    normalized_plate = _normalize_plate(plate)
    entry_time = datetime.now().strftime(TIME_FORMAT)

    with _connect() as conn:
        conn.execute("BEGIN")

        active_existing = conn.execute(
            "SELECT session_id FROM sessions WHERE plate_number = ? AND status = 'active'",
            (normalized_plate,),
        ).fetchone()
        if active_existing:
            raise ValueError("This vehicle already has an active session.")

        spot = conn.execute(
            "SELECT status FROM spots WHERE spot_id = ?",
            (spot_id,),
        ).fetchone()
        if not spot:
            raise ValueError("Selected spot was not found.")
        if spot["status"] != "available":
            raise ValueError("Selected spot is no longer available.")

        cursor = conn.execute(
            """
            INSERT INTO sessions (plate_number, vehicle_type, spot_id, entry_time, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (normalized_plate, vehicle_type, spot_id, entry_time),
        )
        conn.execute(
            "UPDATE spots SET status = 'occupied' WHERE spot_id = ?",
            (spot_id,),
        )

        return int(cursor.lastrowid)


def get_active_session(plate: str) -> dict[str, Any] | None:
    """Return the active session row by plate (normalized)."""
    normalized_plate = _normalize_plate(plate)
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                se.session_id,
                se.plate_number,
                se.vehicle_type,
                se.spot_id,
                se.entry_time,
                se.exit_time,
                se.total_amount,
                se.status,
                sp.spot_type,
                sp.hourly_rate
            FROM sessions AS se
            JOIN spots AS sp ON sp.spot_id = se.spot_id
            WHERE se.plate_number = ?
              AND se.status = 'active'
            ORDER BY se.entry_time DESC
            LIMIT 1
            """,
            (normalized_plate,),
        ).fetchone()
    return dict(row) if row else None


def complete_session(session_id: int, spot_id: int, total: float) -> bool:
    """Mark session as completed and free the spot. Returns True on success."""
    exit_time = datetime.now().strftime(TIME_FORMAT)

    with _connect() as conn:
        conn.execute("BEGIN")

        updated = conn.execute(
            """
            UPDATE sessions
            SET exit_time = ?, total_amount = ?, status = 'completed'
            WHERE session_id = ? AND status = 'active'
            """,
            (exit_time, float(total), session_id),
        )
        if updated.rowcount == 0:
            conn.rollback()
            return False

        conn.execute(
            "UPDATE spots SET status = 'available' WHERE spot_id = ?",
            (spot_id,),
        )
        return True


def get_all_sessions(status: str) -> list[dict[str, Any]]:
    """Return all sessions filtered by status ('active' or 'completed')."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                se.session_id,
                se.plate_number,
                se.vehicle_type,
                se.spot_id,
                se.entry_time,
                se.exit_time,
                se.total_amount,
                se.status,
                sp.spot_type,
                sp.hourly_rate
            FROM sessions AS se
            JOIN spots AS sp ON sp.spot_id = se.spot_id
            WHERE se.status = ?
            ORDER BY se.entry_time DESC
            """,
            (status,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_today_revenue() -> float:
    """Return sum of today's completed session amounts."""
    today = date.today().isoformat()
    with _connect() as conn:
        value = conn.execute(
            """
            SELECT COALESCE(SUM(total_amount), 0)
            FROM sessions
            WHERE status = 'completed'
              AND DATE(exit_time) = ?
            """,
            (today,),
        ).fetchone()[0]
    return float(value or 0.0)


def get_spot_overview() -> dict[str, int]:
    """Return total, occupied, and available spot counts."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM spots").fetchone()[0]
        occupied = conn.execute("SELECT COUNT(*) FROM spots WHERE status = 'occupied'").fetchone()[0]
    return {
        "total": int(total),
        "occupied": int(occupied),
        "available": int(total - occupied),
    }


def normalize_plate(plate: str) -> str:
    """Public helper for consistent plate normalization."""
    return _normalize_plate(plate)
