"""Let sklearn models pickled on older versions run under newer sklearn (predict-time attrs)."""
from __future__ import annotations

from typing import Any


def patch_legacy_sklearn(est: Any) -> None:
    """Fill `monotonic_cst` etc. on trees from old pickles (sklearn 1.8+ reads it in `_validate_X_predict`)."""
    name = type(est).__name__
    if name == "DecisionTreeClassifier":
        if not hasattr(est, "monotonic_cst"):
            est.monotonic_cst = None
        return
    if name == "Pipeline" and hasattr(est, "steps"):
        for _, step in est.steps:
            patch_legacy_sklearn(step)
        return
    estimators = getattr(est, "estimators_", None)
    if estimators is not None:
        for e in estimators:
            patch_legacy_sklearn(e)
    named = getattr(est, "named_steps", None)
    if isinstance(named, dict):
        for step in named.values():
            patch_legacy_sklearn(step)
