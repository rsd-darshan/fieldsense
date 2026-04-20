"""Shared ML inference used by HTML forms and JSON API."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.preprocessing import LabelEncoder

# N, P, K = nitrogen, phosphorus, potassium (sklearn / API feature names)
CROP_FEATURE_KEYS = ("N", "P", "K", "temperature", "humidity", "ph", "rainfall")


def run_crop_predict(crop_model, features: List[float]) -> str:
    final = [np.array(features, dtype=float)]
    pred = crop_model.predict(final)
    return str(pred[0])


def run_fertilizer_predict(
    fertilizer_model,
    soil_type_encoder: LabelEncoder,
    crop_type_encoder: LabelEncoder,
    payload: Dict[str, Any],
) -> str:
    int_features = [
        float(payload["temperature"]),
        float(payload["humidity"]),
        float(payload["moisture"]),
        soil_type_encoder.transform([payload["soil_type"]])[0],
        crop_type_encoder.transform([payload["crop_type"]])[0],
        float(payload["nitrogen"]),
        float(payload["potassium"]),
        float(payload["phosphorous"]),
    ]
    final = [np.array(int_features, dtype=float)]
    pred = fertilizer_model.predict(final)
    return str(pred[0])
