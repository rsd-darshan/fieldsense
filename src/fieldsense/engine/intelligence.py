"""
FieldSense Intelligence Engine — aggregates model outputs + field context into
health score, risk tier, and recommended actions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _parse_npk_ratio(n: Optional[float], p: Optional[float], k: Optional[float]) -> Tuple[float, str]:
    if n is None or p is None or k is None or p == 0:
        return 0.0, "unknown"
    # Ideal rough ratio for many crops ~ 4:2:1 nitrogen:phosphorus:potassium — distance from balance as stress signal
    r1 = n / max(p, 1e-6)
    r2 = k / max(p, 1e-6)
    target1, target2 = 2.0, 1.5  # loose heuristic
    dev = abs(r1 - target1) / 3.0 + abs(r2 - target2) / 3.0
    return _clamp(dev, 0.0, 3.0), "ok" if dev < 1.2 else "imbalanced"


def compute_unified(
    field: Dict[str, Any],
    crop_label: Optional[str] = None,
    fertilizer_label: Optional[str] = None,
    disease_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Produce health score 0–100, risk level, summary, and action items.
    Uses heuristics over tabular field data + model labels — not a second ML model.
    """
    score = 68.0
    actions: List[str] = []
    flags: List[str] = []

    n, p, k = field.get("n"), field.get("p"), field.get("k")
    ph = field.get("ph")
    moisture = field.get("moisture")
    rainfall = field.get("rainfall")
    humidity = field.get("humidity")

    # Soil pH comfort (broad)
    if ph is not None:
        if ph < 5.5 or ph > 8.0:
            score -= 12
            flags.append("ph_stress")
            actions.append("Soil pH is outside a common fertile band—consider liming or acidification based on testing.")
        elif 6.0 <= ph <= 7.5:
            score += 4

    # Moisture / drought signal (fertilizer context)
    if moisture is not None:
        if moisture < 25:
            score -= 10
            flags.append("dry")
            actions.append("Moisture reads low—increase irrigation monitoring before heavy nutrient applications.")
        elif moisture > 85:
            score -= 6
            flags.append("wet")
            actions.append("Very high moisture—watch drainage and disease pressure.")

    if rainfall is not None and rainfall < 40 and (humidity is not None and humidity < 45):
        score -= 5
        flags.append("arid_trend")

    dev, npk_state = _parse_npk_ratio(
        float(n) if n is not None else None,
        float(p) if p is not None else None,
        float(k) if k is not None else None,
    )
    if npk_state == "imbalanced":
        score -= 8
        flags.append("npk_imbalance")
        actions.append(
            "Macronutrients look imbalanced—align nitrogen, phosphorus, and potassium (N–P–K) with soil test and crop stage."
        )

    # Disease signal
    if disease_label:
        dl = disease_label.lower()
        if "healthy" in dl:
            score += 8
        else:
            score -= 22
            flags.append("disease_signal")
            actions.insert(0, f"Leaf screening flagged “{disease_label}”—inspect canopy and consider lab confirmation.")

    # Crop / fert outputs — reward having run models
    if crop_label:
        score += 3
    if fertilizer_label:
        score += 2

    score = int(round(_clamp(score, 0.0, 100.0)))

    if score >= 75:
        risk = "low"
    elif score >= 50:
        risk = "medium"
    else:
        risk = "high"

    summary_parts = [f"Composite field health sits at {score}/100."]
    if risk == "low":
        summary_parts.append("Overall signals look manageable with routine monitoring.")
    elif risk == "medium":
        summary_parts.append("Several indicators warrant follow-up within the week.")
    else:
        summary_parts.append("Multiple stress signals—prioritize field visit and targeted tests.")

    if crop_label:
        summary_parts.append(f"Latest crop model suggestion: {crop_label}.")
    if fertilizer_label:
        summary_parts.append(f"Latest fertilizer class suggestion: {fertilizer_label}.")

    return {
        "health_score": score,
        "risk_level": risk,
        "summary": " ".join(summary_parts),
        "actions": actions[:5],
        "flags": flags,
        "engine_version": "1.0.0-heuristic",
    }


def merge_engine_into_output(
    base: Dict[str, Any],
    engine: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(base)
    out["intelligence"] = engine
    return out
