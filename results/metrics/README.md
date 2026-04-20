# Metrics templates

Use this directory for reproducible quantitative summaries.

## Crop model report template

| metric | value | notes |
|---|---:|---|
| accuracy |  | held-out split |
| macro_f1 |  | class balance-sensitive |
| seed | 42 | deterministic split/training |

## Fertilizer model report template

| metric | value | notes |
|---|---:|---|
| accuracy |  | held-out split |
| macro_f1 |  | class balance-sensitive |
| seed | 42 | deterministic split/training |

## Engine rollup study template

| scenario | health_score | risk_level | triggered_flags |
|---|---:|---|---|
| baseline |  |  |  |
| low_moisture |  |  |  |
| ph_stress |  |  |  |
| nitrogen–phosphorus–potassium imbalance (`npk_imbalance` flag) |  |  |  |
