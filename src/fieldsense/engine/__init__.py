"""Heuristic intelligence engine (health rollup + rule alerts)."""

from .alerts import compute_alerts
from .intelligence import compute_unified, merge_engine_into_output
from .rollup import compute_rollup

__all__ = [
    "compute_alerts",
    "compute_unified",
    "compute_rollup",
    "merge_engine_into_output",
]
