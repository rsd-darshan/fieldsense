"""Route metadata for research API consumers."""

from __future__ import annotations


def api_overview() -> dict:
    return {
        "health": "/api/health",
        "dashboard": "/api/dashboard",
        "predict_crop": "/api/fields/<id>/predict/crop",
        "predict_fertilizer": "/api/fields/<id>/predict/fertilizer",
        "predict_leaf": "/api/fields/<id>/predict/leaf",
        "export_csv": "/api/fields/<id>/export.csv",
        "ui_home": "/",
        "ui_model1_crop": "/model1",
        "ui_model2_fertilizer": "/model2",
        "ui_model3_leaf": "/model3",
    }
