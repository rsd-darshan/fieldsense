# Heuristic engine design

## Purpose

Combine telemetry and latest model outputs into an interpretable field-level summary.

## Current scoring components

- pH stress penalty outside broad fertile range
- moisture stress penalties for low/high readings
- aridity trend penalty from low rainfall + low humidity
- Nitrogen–phosphorus–potassium (N–P–K) imbalance penalty via ratio deviation heuristic
- disease signal reward/penalty based on leaf classification
- small reward for available crop/fertilizer model outputs

## Risk mapping

- `low`: score >= 75
- `medium`: 50 <= score < 75
- `high`: score < 50

## Transparency principle

Each score change should map to a documented rule and emitted `flags` list for traceability.
