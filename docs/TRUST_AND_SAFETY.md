# Trust and safety

## Scope

FieldSense is an experimental platform for agricultural ML research and decision-support workflow studies.

## Not intended uses

- Not agronomic, veterinary, legal, or regulatory advice.
- Not a certified prescription or farm-management platform.
- Not validated for all crops, regions, or operational settings.

## Data handling

- SQLite stores farm/field telemetry and prediction history.
- Uploaded leaf images are stored in `app/uploads/`.
- Avoid adding personal or sensitive data to shared deployments.

## Model limitations

- Tabular models can fail under domain shift and noisy measurements.
- Leaf screening is an optional extension and may be unavailable in constrained deployments.
- Heuristic rollup outputs are interpretable summaries, not calibrated risk probabilities.
