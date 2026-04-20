"""Rule-based alerts from field telemetry and latest predictions."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def compute_alerts(
    field: Dict[str, Any],
    latest_disease: Optional[str] = None,
    latest_crop: Optional[str] = None,
) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []

    moisture = field.get("moisture")
    if moisture is not None and moisture < 22:
        alerts.append(
            {
                "id": "dry_soil",
                "severity": "high",
                "title": "Soil moisture critically low",
                "detail": "Irrigation or rainfall may be insufficient for active crop demand.",
                "cta": "Review irrigation schedule",
            }
        )
    elif moisture is not None and moisture < 35:
        alerts.append(
            {
                "id": "dry_soil_warn",
                "severity": "medium",
                "title": "Soil moisture below comfort",
                "detail": "Consider increasing monitoring frequency.",
                "cta": "Check field sensors",
            }
        )

    ph = field.get("ph")
    if ph is not None and (ph < 5.2 or ph > 8.2):
        alerts.append(
            {
                "id": "ph_extreme",
                "severity": "medium",
                "title": "pH outside common fertile range",
                "detail": "Nutrient availability may be limited until pH is corrected.",
                "cta": "Plan soil test",
            }
        )

    if latest_disease:
        low = latest_disease.lower()
        if "healthy" not in low:
            alerts.append(
                {
                    "id": "leaf_pathogen",
                    "severity": "high",
                    "title": "Leaf condition needs attention",
                    "detail": f"Model suggestion: {latest_disease}",
                    "cta": "Open leaf analysis",
                }
            )

    n, p, k = field.get("n"), field.get("p"), field.get("k")
    if n is not None and p is not None and k is not None and p > 0:
        if n / p > 6 or k / p > 6:
            alerts.append(
                {
                    "id": "npk_skew",
                    "severity": "low",
                    "title": "Macronutrient ratio unusual",
                    "detail": "Nitrogen, phosphorus, and potassium (N–P–K) may not match crop stage—validate with soil test.",
                    "cta": "Review nutrients",
                }
            )

    return alerts[:8]
