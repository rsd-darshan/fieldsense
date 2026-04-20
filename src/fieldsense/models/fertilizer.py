"""Fertilizer model wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np


@dataclass
class FertilizerModelWrapper:
    model: object
    soil_encoder: object
    crop_encoder: object

    def predict(self, payload: Mapping[str, Any]) -> str:
        vec = [
            float(payload["temperature"]),
            float(payload["humidity"]),
            float(payload["moisture"]),
            self.soil_encoder.transform([payload["soil_type"]])[0],
            self.crop_encoder.transform([payload["crop_type"]])[0],
            float(payload["nitrogen"]),
            float(payload["potassium"]),
            float(payload["phosphorous"]),
        ]
        arr = [np.array(vec, dtype=float)]
        return str(self.model.predict(arr)[0])
