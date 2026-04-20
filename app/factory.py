"""Application factory — composes Flask, sklearn artifacts, and persistence."""
from __future__ import annotations

import csv
import os
import pickle
import sys
from pathlib import Path
from typing import Optional

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from sklearn.preprocessing import LabelEncoder

import config as app_config
import database as db
from api_routes import api_bp
from errors import register_error_handlers
from ml_compat import patch_legacy_sklearn


def _fertilizer_catalog(root: Path) -> list[str]:
    """Distinct fertilizer names from the public dataset (for friendly UI labels)."""
    p = root / "data" / "raw" / "fertilizer_dataset.csv"
    if not p.is_file():
        return []
    names: set[str] = set()
    try:
        with p.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            col = None
            for h in reader.fieldnames or []:
                if h and "Fertilizer" in h:
                    col = h
                    break
            if not col:
                return []
            for row in reader:
                v = (row.get(col) or "").strip()
                if v:
                    names.add(v)
    except OSError:
        return []
    return sorted(names)


def _ensure_repo_paths(app_dir: Path) -> None:
    """Put `src/` (fieldsense package) and `app/` on sys.path for Vercel and `cd app` runs."""
    root = app_dir.parent
    for p in (root / "src", app_dir):
        s = str(p.resolve())
        if s not in sys.path:
            sys.path.insert(0, s)


def create_app() -> Flask:
    app_dir = Path(__file__).resolve().parent
    _ensure_repo_paths(app_dir)

    from fieldsense.utils.logging import get_logger

    log = get_logger("fieldsense")

    APP_DIR = str(app_dir)
    TEMPLATE_DIR = os.path.join(APP_DIR, "templates")
    STATIC_DIR = os.path.join(APP_DIR, "static")
    UPLOAD_DIR = os.environ.get("FIELDSENSE_UPLOAD_DIR") or os.path.join(APP_DIR, "uploads")
    ALLOWED_UPLOAD_EXT = {".jpg", ".jpeg", ".png", ".webp"}

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    flask_app = Flask(__name__, template_folder=TEMPLATE_DIR)
    flask_app.config.from_object(app_config.Config)
    flask_app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    flask_app.config["UPLOAD_DIR"] = UPLOAD_DIR
    flask_app.config["ALLOWED_UPLOAD_EXT"] = ALLOWED_UPLOAD_EXT

    crop_path = os.path.join(APP_DIR, "stored_model.pkl")
    fert_path = os.path.join(APP_DIR, "stored_model_fr.pkl")
    try:
        with open(crop_path, "rb") as f_crop:
            crop_model = pickle.load(f_crop)
        with open(fert_path, "rb") as f_fert:
            fertilizer_model = pickle.load(f_fert)
    except Exception:
        log.exception("failed to load sklearn artifacts from %s", APP_DIR)
        raise

    patch_legacy_sklearn(crop_model)
    patch_legacy_sklearn(fertilizer_model)

    flask_app.config["CROP_MODEL"] = crop_model
    flask_app.config["FERT_MODEL"] = fertilizer_model

    soil_type_encoder = LabelEncoder()
    crop_type_encoder = LabelEncoder()
    soil_types = ["Sandy", "Loamy", "Black", "Red", "Clayey"]
    crop_types = [
        "Maize",
        "Sugarcane",
        "Cotton",
        "Tobacco",
        "Paddy",
        "Barley",
        "Wheat",
        "Millets",
        "Oil seeds",
        "Pulses",
        "Ground Nuts",
    ]
    soil_type_encoder.fit(soil_types)
    crop_type_encoder.fit(crop_types)
    flask_app.config["SOIL_ENC"] = soil_type_encoder
    flask_app.config["CROP_ENC"] = crop_type_encoder

    flask_app.register_blueprint(api_bp)

    @flask_app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    _LEGACY_PATHS = frozenset(
        {f"/week{i}.html" for i in range(1, 7)}
        | {
            "/model1.html",
            "/model2.html",
            "/model3.html",
            "/page.html",
            "/page2.html",
            "/leaf.html",
            "/index.html",
            "/dashboard",
            "/welcome.html",
            "/about.html",
            "/author.html",
            "/research.html",
            "/models/crop",
            "/models/fertilizer",
            "/models/leaf",
        }
    )

    @flask_app.before_request
    def _redirect_obsolete_paths():
        p = request.path
        if p in _LEGACY_PATHS or p.startswith("/field/"):
            return redirect(url_for("home"), code=302)

    db.init_db()
    db.seed_reference_if_empty()

    def first_field_id() -> Optional[int]:
        farms = sorted(db.farm_list(), key=lambda x: x["id"])
        for fm in farms:
            flds = db.fields_for_farm(fm["id"])
            if flds:
                return int(flds[0]["id"])
        return None

    def _prediction_summary(kind: str, output: dict) -> str:
        out = output or {}
        if kind == "crop":
            return str(out.get("label") or "—")
        if kind == "fertilizer":
            return str(out.get("label") or "—")
        if kind == "disease":
            return str(out.get("prediction") or "—")
        if kind == "unified":
            intel = out.get("intelligence") or {}
            hs = intel.get("health_score")
            if hs is not None:
                return f"Rollup · health {hs}"
            return "Rollup"
        return "—"

    @flask_app.route("/assets/<path:fn>")
    def serve_assets(fn):
        if ".." in fn or fn.startswith("/"):
            abort(404)
        return send_from_directory(STATIC_DIR, fn)

    @flask_app.route("/")
    def home():
        return render_template("minimal_home.html", nav="home")

    @flask_app.route("/model1")
    def model1():
        db.seed_reference_if_empty()
        fid = first_field_id()
        if fid is None:
            abort(503)
        return render_template("model1.html", nav="m1", field_id=fid)

    @flask_app.route("/model2")
    def model2():
        db.seed_reference_if_empty()
        fid = first_field_id()
        if fid is None:
            abort(503)
        fert_catalog = _fertilizer_catalog(app_dir.parent)
        return render_template(
            "model2.html",
            nav="m2",
            field_id=fid,
            soil_types=soil_types,
            crop_types=crop_types,
            fertilizer_catalog=fert_catalog,
        )

    @flask_app.route("/model3")
    def model3():
        db.seed_reference_if_empty()
        fid = first_field_id()
        if fid is None:
            abort(503)
        return render_template("model3.html", nav="m3", field_id=fid)

    @flask_app.route("/history")
    def history():
        db.seed_reference_if_empty()
        raw = db.recent_predictions(100)
        rows = [
            {
                **p,
                "kind_label": {
                    "crop": "Crop",
                    "fertilizer": "Fertilizer",
                    "disease": "Leaf",
                    "unified": "Rollup",
                }.get(p.get("kind") or "", p.get("kind") or "—"),
                "summary": _prediction_summary(p.get("kind") or "", p.get("output") or {}),
            }
            for p in raw
        ]
        fid = first_field_id()
        return render_template("minimal_history.html", nav="hist", rows=rows, field_id=fid)

    @flask_app.route("/uploads/<filename>")
    def serve_upload(filename):
        if filename != os.path.basename(filename) or ".." in filename:
            abort(404)
        base = os.path.realpath(UPLOAD_DIR)
        full = os.path.realpath(os.path.join(UPLOAD_DIR, filename))
        if not full.startswith(base + os.sep):
            abort(404)
        if not os.path.isfile(full):
            abort(404)
        return send_from_directory(UPLOAD_DIR, filename)

    register_error_handlers(flask_app)
    return flask_app
