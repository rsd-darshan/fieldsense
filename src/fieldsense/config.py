"""Research package configuration helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchConfig:
    random_seed: int = 42
    crop_model_path: str = "app/stored_model.pkl"
    fertilizer_model_path: str = "app/stored_model_fr.pkl"
