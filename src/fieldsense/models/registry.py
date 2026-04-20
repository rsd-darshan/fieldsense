"""Model artifact path registry used by experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelRegistry:
    crop_model: str = "app/stored_model.pkl"
    fertilizer_model: str = "app/stored_model_fr.pkl"
    leaf_model: str = "app/leaf_models/model.pth"
