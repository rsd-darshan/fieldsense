# Contributing

Thanks for contributing to FieldSense.

## Contribution focus

This repository prioritizes reproducible agricultural ML research:

- New datasets or data quality analyses
- Model baselines and evaluation protocols
- Heuristic engine transparency and ablations
- Documentation improvements (methodology, limitations, reproducibility)

## Workflow

1. Open an issue describing the research motivation.
2. Keep changes scoped and include tests when possible.
3. Update `docs/` when assumptions or methodology change.
4. Run:
   - `python -m pytest tests/ -v`
   - relevant scripts in `experiments/`

## Style

- Prefer typed Python functions and explicit assumptions.
- Avoid hidden thresholds; document them in `docs/engine_design.md` or `src/fieldsense/engine/thresholds.md`.
