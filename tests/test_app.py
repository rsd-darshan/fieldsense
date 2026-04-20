"""Smoke tests for FieldSense CI."""

import json


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("X-FieldSense-Version")
    assert r.headers.get("X-FieldSense-Stage")
    data = json.loads(r.data)
    assert data["status"] == "ok"
    assert data.get("version")


def test_engine_info(client):
    r = client.get("/api/engine")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data.get("version")
    assert "leaf_onnx" in (data.get("models") or [])


def test_home(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"FieldSense" in r.data
    assert b"/model1" in r.data
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"


def test_history_page(client):
    r = client.get("/history")
    assert r.status_code == 200
    assert b"History" in r.data
    assert b"Prediction history" in r.data


def test_history_endpoint_registered(client):
    endpoints = {rule.endpoint for rule in client.application.url_map.iter_rules()}
    assert "history" in endpoints


def test_model1_page(client):
    r = client.get("/model1")
    assert r.status_code == 200
    assert b"Model 1" in r.data
    assert b"predict/crop" in r.data


def test_model2_page(client):
    r = client.get("/model2")
    assert r.status_code == 200
    assert b"Model 2" in r.data


def test_model3_page(client):
    r = client.get("/model3")
    assert r.status_code == 200
    assert b"Model 3" in r.data
    assert b"Drop image here" in r.data


def test_legacy_redirect_dashboard(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (301, 302)
    assert "/" in (r.headers.get("Location") or "")


def test_legacy_redirect_index(client):
    r = client.get("/index.html", follow_redirects=False)
    assert r.status_code in (301, 302)
    assert "/" in (r.headers.get("Location") or "")


def test_export_csv(client):
    r = client.get("/api/fields/1/export.csv")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("text/csv")
    assert b"section,key,value" in r.data


def test_crop_prediction_rejects_out_of_range_ph(client):
    r = client.post(
        "/api/fields/1/predict/crop",
        json={"ph": 20},
    )
    assert r.status_code == 400
    data = json.loads(r.data)
    assert "Invalid ph" in (data.get("error") or "")


def test_fertilizer_prediction_rejects_unknown_soil_type(client):
    r = client.post(
        "/api/fields/1/predict/fertilizer",
        json={"soil_type": "MoonDust"},
    )
    assert r.status_code == 400
    data = json.loads(r.data)
    assert "Invalid soil_type" in (data.get("error") or "")


def test_api_version_and_security_headers(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("X-FieldSense-Version")
    assert r.headers.get("X-FieldSense-Stage")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
