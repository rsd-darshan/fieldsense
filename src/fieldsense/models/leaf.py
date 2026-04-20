"""Leaf screening integration helpers."""

from __future__ import annotations

from typing import Any, Dict


def safe_leaf_predict(module: Any, image_path: str) -> Dict[str, Any]:
    return module.predict_leaf_image(image_path)
