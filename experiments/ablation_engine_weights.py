"""Simple script to inspect engine sensitivity under telemetry perturbations."""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from fieldsense.engine.intelligence import compute_unified


def main() -> None:
    base_field = {
        "n": 90,
        "p": 45,
        "k": 35,
        "ph": 6.8,
        "moisture": 42,
        "rainfall": 120,
        "humidity": 70,
    }
    scenarios = [
        ("base", base_field),
        ("low_moisture", {**base_field, "moisture": 20}),
        ("ph_stress", {**base_field, "ph": 8.7}),
        ("nitrogen_phosphorus_potassium_imbalance", {**base_field, "n": 200, "p": 10, "k": 20}),
    ]
    for name, field in scenarios:
        out = compute_unified(field, crop_label="rice", fertilizer_label="Urea")
        print(name, out["health_score"], out["risk_level"], out["flags"])


if __name__ == "__main__":
    main()
