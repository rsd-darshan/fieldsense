"""SQLite persistence for farms, fields, and prediction history."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Vercel serverless cannot write to the app directory; allow override to /tmp.
DB_PATH = os.environ.get("FIELDSENSE_DB_PATH", os.path.join(APP_DIR, "fieldsense.db"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS farms (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              region TEXT DEFAULT '',
              created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fields (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              farm_id INTEGER NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
              name TEXT NOT NULL,
              n REAL, p REAL, k REAL,
              temperature REAL, humidity REAL, ph REAL, rainfall REAL,
              moisture REAL, soil_type TEXT, crop_type TEXT,
              nitrogen REAL, potassium REAL, phosphorous REAL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS predictions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              field_id INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
              kind TEXT NOT NULL,
              input_json TEXT,
              output_json TEXT NOT NULL,
              health_score INTEGER,
              risk_level TEXT,
              created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_id);
            CREATE INDEX IF NOT EXISTS idx_predictions_field ON predictions(field_id);
            """
        )


def farm_create(name: str, region: str = "") -> int:
    ts = _utc_now()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO farms (name, region, created_at) VALUES (?, ?, ?)",
            (name.strip() or "My farm", region, ts),
        )
        return int(cur.lastrowid)


def farm_list() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, name, region, created_at FROM farms ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def farm_get(farm_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM farms WHERE id = ?", (farm_id,)).fetchone()
        return dict(row) if row else None


def field_create(
    farm_id: int,
    name: str,
    data: Optional[Dict[str, Any]] = None,
) -> int:
    data = data or {}
    ts = _utc_now()

    def g(key: str, default=None):
        v = data.get(key, default)
        return float(v) if v is not None and v != "" else None

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO fields (
              farm_id, name,
              n, p, k, temperature, humidity, ph, rainfall,
              moisture, soil_type, crop_type, nitrogen, potassium, phosphorous,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farm_id,
                name.strip() or "Field",
                g("n"),
                g("p"),
                g("k"),
                g("temperature"),
                g("humidity"),
                g("ph"),
                g("rainfall"),
                g("moisture"),
                data.get("soil_type") or None,
                data.get("crop_type") or None,
                g("nitrogen"),
                g("potassium"),
                g("phosphorous"),
                ts,
                ts,
            ),
        )
        return int(cur.lastrowid)


def field_get(field_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM fields WHERE id = ?", (field_id,)).fetchone()
        return dict(row) if row else None


def field_update(field_id: int, data: Dict[str, Any]) -> None:
    ts = _utc_now()

    def g(key: str):
        v = data.get(key)
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def s_opt(key: str):
        v = data.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return str(v).strip()

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE fields SET
              name = COALESCE(?, name),
              n = ?, p = ?, k = ?, temperature = ?, humidity = ?, ph = ?, rainfall = ?,
              moisture = ?, soil_type = ?, crop_type = ?,
              nitrogen = ?, potassium = ?, phosphorous = ?,
              updated_at = ?
            WHERE id = ?
            """,
            (
                data.get("name"),
                g("n"),
                g("p"),
                g("k"),
                g("temperature"),
                g("humidity"),
                g("ph"),
                g("rainfall"),
                g("moisture"),
                s_opt("soil_type"),
                s_opt("crop_type"),
                g("nitrogen"),
                g("potassium"),
                g("phosphorous"),
                ts,
                field_id,
            ),
        )


def fields_for_farm(farm_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM fields WHERE farm_id = ? ORDER BY name",
            (farm_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def prediction_add(
    field_id: int,
    kind: str,
    output: Dict[str, Any],
    input_payload: Optional[Dict[str, Any]] = None,
    health_score: Optional[int] = None,
    risk_level: Optional[str] = None,
) -> int:
    ts = _utc_now()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO predictions (field_id, kind, input_json, output_json, health_score, risk_level, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                field_id,
                kind,
                json.dumps(input_payload) if input_payload is not None else None,
                json.dumps(output),
                health_score,
                risk_level,
                ts,
            ),
        )
        return int(cur.lastrowid)


def predictions_for_field(field_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM predictions
            WHERE field_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (field_id, limit),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["output"] = json.loads(d["output_json"])
            except json.JSONDecodeError:
                d["output"] = {}
            if d.get("input_json"):
                try:
                    d["input"] = json.loads(d["input_json"])
                except json.JSONDecodeError:
                    d["input"] = {}
            else:
                d["input"] = None
            del d["output_json"]
            if "input_json" in d:
                del d["input_json"]
            out.append(d)
        return out


def latest_prediction(field_id: int, kind: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM predictions
            WHERE field_id = ? AND kind = ?
            ORDER BY datetime(created_at) DESC LIMIT 1
            """,
            (field_id, kind),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["output"] = json.loads(d["output_json"])
        return d


def dashboard_counts() -> Dict[str, int]:
    with get_conn() as conn:
        farms = conn.execute("SELECT COUNT(*) FROM farms").fetchone()[0]
        fields = conn.execute("SELECT COUNT(*) FROM fields").fetchone()[0]
        preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        return {"farms": farms, "fields": fields, "predictions": preds}


def recent_predictions(limit: int = 12) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.field_id, p.kind, p.output_json, p.health_score, p.risk_level, p.created_at,
                   f.name AS field_name, fm.name AS farm_name
            FROM predictions p
            JOIN fields f ON f.id = p.field_id
            JOIN farms fm ON fm.id = f.farm_id
            ORDER BY datetime(p.created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["output"] = json.loads(d["output_json"])
            except json.JSONDecodeError:
                d["output"] = {}
            del d["output_json"]
            out.append(d)
        return out


def seed_reference_if_empty() -> None:
    if dashboard_counts()["farms"] > 0:
        return
    farm_id = farm_create("Northridge Farm", "Reference region")
    field_create(
        farm_id,
        "North quarter",
        {
            "n": 90,
            "p": 42,
            "k": 43,
            "temperature": 22.0,
            "humidity": 65.0,
            "ph": 6.5,
            "rainfall": 120.0,
            "moisture": 42.0,
            "soil_type": "Loamy",
            "crop_type": "Maize",
            "nitrogen": 12.0,
            "potassium": 15.0,
            "phosphorous": 10.0,
        },
    )
