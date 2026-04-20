"""JSON API for research dashboard, telemetry, and ML operations."""
from __future__ import annotations

import os
import uuid
import math
import json
from typing import Any, Dict, Optional

import csv
import io

from flask import Blueprint, Response, abort, current_app, jsonify, request
from werkzeug.utils import secure_filename

from __version__ import STAGE, VERSION

import database as db
from ml_ops import CROP_FEATURE_KEYS, run_crop_predict, run_fertilizer_predict
from services.alerts import compute_alerts
from services.intelligence import compute_unified

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.after_request
def _api_version_headers(response: Response):
    response.headers["X-FieldSense-Version"] = VERSION
    response.headers["X-FieldSense-Stage"] = STAGE
    return response


def _crop_scalar(field: Dict[str, Any], body: Dict[str, Any], key: str) -> float:
    """DB + forms use n/p/k for storage; sklearn expects N, P, K as nitrogen, phosphorus, potassium feature names."""
    aliases = (key,)
    if key == "N":
        aliases = ("N", "n")
    elif key == "P":
        aliases = ("P", "p")
    elif key == "K":
        aliases = ("K", "k")
    for a in aliases:
        if a in body and body[a] is not None and str(body[a]).strip() != "":
            return _to_float(body[a], key)
    for a in aliases:
        if field.get(a) is not None:
            return _to_float(field[a], key)
    raise ValueError(f"Missing {key}")


def _to_float(value: Any, key: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {key}: numeric value required") from exc
    if not math.isfinite(out):
        raise ValueError(f"Invalid {key}: finite numeric value required")
    return out


def _validate_range(value: float, key: str, *, min_value: float, max_value: float) -> None:
    if value < min_value or value > max_value:
        raise ValueError(f"Invalid {key}: expected {min_value:g} to {max_value:g}")


def _crop_features_from_field_and_body(field: Dict[str, Any], body: Dict[str, Any]) -> list[float]:
    merged = {k: _crop_scalar(field, body, k) for k in CROP_FEATURE_KEYS}
    _validate_range(merged["N"], "N", min_value=0, max_value=300)
    _validate_range(merged["P"], "P", min_value=0, max_value=300)
    _validate_range(merged["K"], "K", min_value=0, max_value=300)
    _validate_range(merged["temperature"], "temperature", min_value=-20, max_value=60)
    _validate_range(merged["humidity"], "humidity", min_value=0, max_value=100)
    _validate_range(merged["ph"], "ph", min_value=0, max_value=14)
    _validate_range(merged["rainfall"], "rainfall", min_value=0, max_value=5000)
    return [merged[k] for k in CROP_FEATURE_KEYS]


def _fert_payload_from_field_and_body(field: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "temperature",
        "humidity",
        "moisture",
        "soil_type",
        "crop_type",
        "nitrogen",
        "potassium",
        "phosphorous",
    ]
    out: Dict[str, Any] = {}
    for k in keys:
        if k in body and body[k] is not None and str(body[k]).strip() != "":
            out[k] = body[k]
        elif field.get(k) is not None:
            out[k] = field[k]
        else:
            raise ValueError(f"Missing {k}")
    return out


def _normalize_label(value: Any, key: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Missing {key}")
    return text


@api_bp.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "fieldsense-api",
            "version": VERSION,
            "stage": STAGE,
        }
    )


@api_bp.route("/engine")
def engine_info():
    return jsonify(
        {
            "name": "FieldSense Intelligence Engine",
            "version": VERSION,
            "stage": STAGE,
            "models": ["crop_sklearn", "fertilizer_sklearn", "leaf_onnx"],
            "aggregation": "heuristic_health_score",
        }
    )


@api_bp.route("/farms", methods=["GET", "POST"])
def farms():
    if request.method == "GET":
        return jsonify({"farms": db.farm_list()})
    data = request.get_json(force=True, silent=True) or {}
    fid = db.farm_create(name=data.get("name", "My farm"), region=data.get("region", ""))
    return jsonify({"id": fid}), 201


@api_bp.route("/farms/<int:farm_id>/fields", methods=["GET"])
def farm_fields(farm_id: int):
    return jsonify({"fields": db.fields_for_farm(farm_id)})


@api_bp.route("/fields", methods=["POST"])
def create_field():
    data = request.get_json(force=True, silent=True) or {}
    farm_id = data.get("farm_id")
    if not farm_id:
        return jsonify({"error": "farm_id required"}), 400
    name = data.get("name", "Field")
    payload = {k: data.get(k) for k in data if k not in ("farm_id", "name")}
    fid = db.field_create(int(farm_id), name, payload)
    return jsonify({"id": fid}), 201


@api_bp.route("/fields/<int:field_id>", methods=["GET", "PATCH"])
def field_one(field_id: int):
    row = db.field_get(field_id)
    if not row:
        abort(404)
    if request.method == "GET":
        preds = db.predictions_for_field(field_id, limit=50)
        return jsonify({"field": row, "predictions": preds})
    data = request.get_json(force=True, silent=True) or {}
    db.field_update(field_id, data)
    return jsonify({"field": db.field_get(field_id)})


@api_bp.route("/fields/<int:field_id>/predict/crop", methods=["POST"])
def predict_crop_api(field_id: int):
    field = db.field_get(field_id)
    if not field:
        abort(404)
    body = request.get_json(force=True, silent=True) or {}
    crop_model = current_app.config["CROP_MODEL"]
    try:
        feats = _crop_features_from_field_and_body(field, body)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    label = run_crop_predict(crop_model, feats)
    inp = {k: feats[i] for i, k in enumerate(CROP_FEATURE_KEYS)}
    eng = compute_unified(field, crop_label=label)
    out = {"label": label, "features_used": inp, "intelligence": eng}
    db.prediction_add(
        field_id,
        "crop",
        out,
        input_payload=inp,
        health_score=eng["health_score"],
        risk_level=eng["risk_level"],
    )
    uni = compute_unified(
        field,
        crop_label=label,
        fertilizer_label=_latest_label(field_id, "fertilizer"),
        disease_label=_latest_label(field_id, "disease"),
    )
    db.prediction_add(
        field_id,
        "unified",
        {"intelligence": uni},
        input_payload={"trigger": "crop"},
        health_score=uni["health_score"],
        risk_level=uni["risk_level"],
    )
    return jsonify(out)


def _latest_label(field_id: int, kind: str) -> Optional[str]:
    p = db.latest_prediction(field_id, kind)
    if not p:
        return None
    o = p.get("output") or {}
    if kind in ("crop", "fertilizer"):
        return o.get("label")
    if kind == "disease":
        return o.get("prediction")
    return None


@api_bp.route("/fields/<int:field_id>/predict/fertilizer", methods=["POST"])
def predict_fert_api(field_id: int):
    field = db.field_get(field_id)
    if not field:
        abort(404)
    body = request.get_json(force=True, silent=True) or {}
    fert_model = current_app.config["FERT_MODEL"]
    soil_enc = current_app.config["SOIL_ENC"]
    crop_enc = current_app.config["CROP_ENC"]
    try:
        payload = _fert_payload_from_field_and_body(field, body)
        payload["temperature"] = _to_float(payload["temperature"], "temperature")
        payload["humidity"] = _to_float(payload["humidity"], "humidity")
        payload["moisture"] = _to_float(payload["moisture"], "moisture")
        payload["nitrogen"] = _to_float(payload["nitrogen"], "nitrogen")
        payload["potassium"] = _to_float(payload["potassium"], "potassium")
        payload["phosphorous"] = _to_float(payload["phosphorous"], "phosphorous")
        _validate_range(payload["temperature"], "temperature", min_value=-20, max_value=60)
        _validate_range(payload["humidity"], "humidity", min_value=0, max_value=100)
        _validate_range(payload["moisture"], "moisture", min_value=0, max_value=100)
        _validate_range(payload["nitrogen"], "nitrogen", min_value=0, max_value=300)
        _validate_range(payload["potassium"], "potassium", min_value=0, max_value=300)
        _validate_range(payload["phosphorous"], "phosphorous", min_value=0, max_value=300)

        payload["soil_type"] = _normalize_label(payload["soil_type"], "soil_type")
        payload["crop_type"] = _normalize_label(payload["crop_type"], "crop_type")
        allowed_soils = {str(x) for x in soil_enc.classes_}
        allowed_crops = {str(x) for x in crop_enc.classes_}
        if payload["soil_type"] not in allowed_soils:
            raise ValueError("Invalid soil_type")
        if payload["crop_type"] not in allowed_crops:
            raise ValueError("Invalid crop_type")
        label = run_fertilizer_predict(fert_model, soil_enc, crop_enc, payload)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except AttributeError as e:
        # e.g. old pickles vs new sklearn — should be mitigated by ml_compat.patch_legacy_sklearn
        return jsonify({"error": f"Fertilizer model runtime error: {e}"}), 503
    inp = {
        k: (
            float(payload[k])
            if k in ("temperature", "humidity", "moisture", "nitrogen", "potassium", "phosphorous")
            else payload[k]
        )
        for k in payload
    }
    eng = compute_unified(field, fertilizer_label=label)
    out = {"label": label, "inputs": inp, "intelligence": eng}
    db.prediction_add(
        field_id,
        "fertilizer",
        out,
        input_payload=inp,
        health_score=eng["health_score"],
        risk_level=eng["risk_level"],
    )
    uni = compute_unified(
        field,
        crop_label=_latest_label(field_id, "crop"),
        fertilizer_label=label,
        disease_label=_latest_label(field_id, "disease"),
    )
    db.prediction_add(
        field_id,
        "unified",
        {"intelligence": uni},
        input_payload={"trigger": "fertilizer"},
        health_score=uni["health_score"],
        risk_level=uni["risk_level"],
    )
    return jsonify(out)


@api_bp.route("/fields/<int:field_id>/predict/leaf", methods=["POST"])
def predict_leaf_api(field_id: int):
    field = db.field_get(field_id)
    if not field:
        abort(404)
    try:
        import leaf_inference
    except ImportError as e:
        current_app.logger.warning("leaf_inference_import_failed: %s", e)
        return (
            jsonify(
                {
                    "error": "Leaf inference dependencies could not be loaded.",
                    "detail": str(e),
                    "hint": "Install onnxruntime (and pandas) for ONNX inference, or torch/torchvision if only model.pth is available.",
                }
            ),
            503,
        )

    if not leaf_inference.leaf_pipeline_ready():
        return (
            jsonify(
                {
                    "error": "Leaf model weights or metadata files are missing on the server.",
                    "hint": "Deploy app/leaf_models/model.onnx (or model.pth) plus disease CSVs; use Git LFS for weight files.",
                }
            ),
            503,
        )
    upload = request.files.get("image")
    if not upload or not upload.filename:
        return jsonify({"error": "image file required"}), 400
    ext = os.path.splitext(secure_filename(upload.filename))[1].lower()
    allowed = current_app.config["ALLOWED_UPLOAD_EXT"]
    if ext not in allowed:
        return jsonify({"error": "invalid image type"}), 400
    up_dir = current_app.config["UPLOAD_DIR"]
    stored = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(up_dir, stored)
    upload.save(path)
    try:
        data = leaf_inference.predict_leaf_image(path)
    except Exception as exc:  # noqa: BLE001
        current_app.logger.exception("leaf_inference_failed field_id=%s", field_id)
        if os.path.isfile(path):
            os.remove(path)
        return jsonify({"error": str(exc)}), 400
    data["image_url"] = f"/uploads/{stored}"
    pred_label = data.get("prediction", "")
    out = {
        "prediction": pred_label,
        "description": data.get("description"),
        "possible_steps": data.get("possible_steps"),
        "supplement": data.get("supplement"),
        "image_url": data["image_url"],
        "intelligence": compute_unified(field, disease_label=pred_label),
    }
    db.prediction_add(
        field_id,
        "disease",
        out,
        input_payload={"image": stored},
        health_score=out["intelligence"]["health_score"],
        risk_level=out["intelligence"]["risk_level"],
    )
    uni = compute_unified(
        field,
        crop_label=_latest_label(field_id, "crop"),
        fertilizer_label=_latest_label(field_id, "fertilizer"),
        disease_label=pred_label,
    )
    db.prediction_add(
        field_id,
        "unified",
        {"intelligence": uni},
        input_payload={"trigger": "disease"},
        health_score=uni["health_score"],
        risk_level=uni["risk_level"],
    )
    return jsonify(out)


@api_bp.route("/dashboard")
def dashboard_data():
    counts = db.dashboard_counts()
    recent = db.recent_predictions(15)
    farms = db.farm_list()
    alerts_all: list[dict] = []
    for fm in farms:
        for f in db.fields_for_farm(fm["id"]):
            dlabel = _latest_label(f["id"], "disease")
            clabel = _latest_label(f["id"], "crop")
            for a in compute_alerts(f, latest_disease=dlabel, latest_crop=clabel):
                a["field_id"] = f["id"]
                a["field_name"] = f["name"]
                a["farm_name"] = fm["name"]
                alerts_all.append(a)
    return jsonify(
        {
            "counts": counts,
            "recent_predictions": recent,
            "farms": farms,
            "alerts": alerts_all[:12],
        }
    )


@api_bp.route("/fields/<int:field_id>/export.csv", methods=["GET"])
def export_field_csv(field_id: int):
    """Export telemetry + predictions for reproducible analysis."""
    field = db.field_get(field_id)
    if not field:
        abort(404)
    preds = db.predictions_for_field(field_id, limit=500)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["section", "key", "value"])
    for k, v in field.items():
        writer.writerow(["field", k, v])
    for i, p in enumerate(preds, start=1):
        writer.writerow(["prediction", f"row_{i}_kind", p.get("kind")])
        writer.writerow(["prediction", f"row_{i}_created_at", p.get("created_at")])
        writer.writerow(["prediction", f"row_{i}_risk_level", p.get("risk_level")])
        writer.writerow(["prediction", f"row_{i}_health_score", p.get("health_score")])
        writer.writerow(
            ["prediction", f"row_{i}_output", json.dumps(p.get("output") or {}, ensure_ascii=True, sort_keys=True)]
        )
    body = buf.getvalue()
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=field_{field_id}_research_export.csv"},
    )


@api_bp.route("/fields/<int:field_id>/intelligence", methods=["GET"])
def intelligence_refresh(field_id: int):
    field = db.field_get(field_id)
    if not field:
        abort(404)
    uni = compute_unified(
        field,
        crop_label=_latest_label(field_id, "crop"),
        fertilizer_label=_latest_label(field_id, "fertilizer"),
        disease_label=_latest_label(field_id, "disease"),
    )
    return jsonify({"intelligence": uni})
