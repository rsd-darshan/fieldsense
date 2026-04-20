"""Rollup: same contract as compute_unified for engine consumers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .intelligence import compute_unified


def compute_rollup(
    field: Dict[str, Any],
    crop_label: Optional[str] = None,
    fertilizer_label: Optional[str] = None,
    disease_label: Optional[str] = None,
) -> Dict[str, Any]:
    return compute_unified(
        field,
        crop_label=crop_label,
        fertilizer_label=fertilizer_label,
        disease_label=disease_label,
    )
