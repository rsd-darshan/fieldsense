# Methodology

## Data

- Crop recommendation tabular dataset (`N`, `P`, `K`, temperature, humidity, pH, rainfall).
- Fertilizer recommendation tabular dataset (environmental and nutrient variables plus categorical soil/crop labels).
- Optional leaf disease image pipeline (experimental extension).

## Modeling pipeline

1. Load and validate raw tabular records.
2. Encode categorical features for fertilizer recommendation.
3. Train task-specific classifiers (crop and fertilizer).
4. Persist model artifacts and evaluate on held-out splits.

## Heuristic intelligence engine

The engine computes a field-level rollup:

- `health_score` (0-100)
- `risk_level` (`low`, `medium`, `high`)
- `actions` (human-readable follow-up steps)
- `flags` (triggered heuristic conditions)

Rules combine:

- pH comfort ranges
- moisture and aridity signals
- Nitrogen, phosphorus, and potassium (N–P–K) balance heuristics
- latest model labels (crop, fertilizer, optional disease)

See `docs/engine_design.md` for thresholds and rationale.
