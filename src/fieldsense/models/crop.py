"""Crop model wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class CropModelWrapper:
    model: object

    def predict(self, features: Sequence[float]) -> str:
        arr = [np.array(features, dtype=float)]
        return str(self.model.predict(arr)[0])
