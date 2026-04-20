# FieldSense

**Structured agronomy assistance from tabular field data and optional leaf imagery — with an API, audit trail, and honest uncertainty boundaries.**

[![CI](https://github.com/rsd-darshan/FieldSense/actions/workflows/ci.yml/badge.svg)](https://github.com/rsd-darshan/FieldSense/actions/workflows/ci.yml)

**Live:** [fieldsense-ai-platform.vercel.app](https://fieldsense-ai-platform.vercel.app/)

---

## Who it’s for

**Target user:** agritech PMs, ML engineers evaluating domain verticals, or researchers who need a *credible* demo that combines classical ML, lightweight CV, and product-shaped APIs — not a notebook dump.

**Problem:** farm decisions need repeatable inputs, explainable outputs, and history. Spreadsheets and one-off models don’t give you versioned predictions tied to a field record or CSV export for review.

**Use case:** enter soil **nitrogen, phosphorus, and potassium (N, P, K)**, weather, and soil context (and optionally a leaf photo); get crop and fertilizer suggestions plus a **heuristic health rollup** (score, risk band, actions) and **persisted predictions** per field.

---

## What’s impressive vs. what’s honest

| Strength | Limitation (explicit) |
|----------|------------------------|
| Full **REST surface** (`/api/...`) + minimal **server-rendered UI** | Not a regulatory or agronomic authority — outputs require human validation |
| **SQLite history** + CSV export for audit / analysis | Serverless SQLite is ephemeral unless you attach external DB |
| **Separation of concerns**: `fieldsense.engine` (library) vs `app` (HTTP + persistence) | Pickled sklearn tied to runtime deps (`category-encoders`, sklearn version drift) |
| **Application factory**, structured logging hooks, `/api` JSON 500 handling | Leaf path uses **onnxruntime + model.onnx** (smaller than PyTorch on serverless); weight files use **Git LFS** |

---

## Architecture

High-level diagram: [`docs/figures/ARCHITECTURE.md`](docs/figures/ARCHITECTURE.md)

```text
┌─────────────┐     ┌──────────────────────────────────────┐
│  Browser    │────▶│  Flask (`app/`)                      │
│  or HTTP    │     │  factory → routes + Jinja + static     │
└─────────────┘     └───────────┬──────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  sklearn pickles      fieldsense.engine        SQLite
  crop / fertilizer    (health rollup + alerts)  farms / fields /
  (in `app/`)          in `src/fieldsense/`      predictions
```

**Request path (predict crop):** resolve field → build feature vector → `run_crop_predict` → `compute_unified` with new label → write `predictions` rows (crop + unified rollup).

---

## Features (why they exist)

- **Crop & fertilizer models** — sklearn pipelines over documented tabular features; outputs include **which numbers were used**, not only the label.
- **Intelligence rollup** — deterministic heuristic over telemetry + model labels: health score, risk tier, flags, short actions. Clearly **not** a second opaque ML model.
- **Rule alerts** — moisture / pH / nitrogen–phosphorus–potassium ratio skew / disease string signals → structured alert objects for dashboards.
- **History & export** — `/history` UI and `GET /api/fields/<id>/export.csv` for offline QA.
- **Legacy path redirects** — old demo URLs 302 to `/` so bookmarks don’t rot.

---

## Repository layout

```text
FieldSense/
├── api/                 # Vercel serverless entry → Flask `app`
├── app/                 # HTTP app: factory, routes, templates, static, weights
├── src/fieldsense/      # Installable library: engine, data helpers, model registry
├── config/              # Reserved for deployment/env conventions (see .env.example)
├── data/                # Documented raw / processed datasets
├── experiments/         # Training & evaluation (offline)
├── docs/                # Methodology, model cards, architecture
└── tests/               # pytest (API smoke + engine shape)
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
git lfs install && git lfs pull
cd app && PORT=5050 python app.py
```

Open [http://127.0.0.1:5050/](http://127.0.0.1:5050/). **Model 3 (leaf)** runs **`model.onnx` via onnxruntime** (default). Regenerate ONNX after changing the PyTorch checkpoint: `python scripts/export_leaf_onnx.py` (needs `torch`, `torchvision`, and `onnx` installed locally). Pull **`app/leaf_models/model.onnx`** (and `.pth` if you use the torch fallback) with **Git LFS** so deploys get real bytes, not pointers.

**Tests**

```bash
python -m pytest tests/ -v
```

**Environment**

| Variable | Role |
|----------|------|
| `FIELDSENSE_SECRET_KEY` | Flask session signing in real deployments |
| `FIELDSENSE_DB_PATH` | SQLite file (default under `app/`; Vercel uses `/tmp`) |
| `FIELDSENSE_SECURE_COOKIE` | Set to `1` in HTTPS deployments to force secure session cookies |

See [`.env.example`](.env.example).

---

## Example API

**Health**

```http
GET /api/health
```

```json
{"status": "ok", "service": "fieldsense-api", "version": "1.0.0", "stage": "research-prototype"}
```

**Crop prediction** (field `1` exists after seed)

```http
POST /api/fields/1/predict/crop
Content-Type: application/json

{"N": 90, "P": 42, "K": 43, "temperature": 20, "humidity": 82, "ph": 6.5, "rainfall": 202}
```

Keys **N**, **P**, and **K** are **nitrogen**, **phosphorus**, and **potassium** in the same units as the training data (see `docs/data_card.md`).

Response shape (abridged): `label`, `features_used`, `intelligence` with `health_score`, `risk_level`, `summary`, `actions`, `flags`.

Validation guardrails:
- Crop route enforces finite values with practical ranges (`pH 0–14`, `humidity/moisture 0–100`, etc.).
- Fertilizer route validates numeric ranges and rejects unknown `soil_type` / `crop_type`.

---

## Tech stack (justified)

| Piece | Why |
|-------|-----|
| **Flask** | Small sync WSGI surface; easy to read in interviews; maps cleanly to Vercel Python. |
| **sklearn + pickles** | Matches how many ag tabular baselines ship; deps pinned where deployment broke (`category-encoders`). |
| **ONNX Runtime (leaf)** | Same ResNet-18 head as training, but a **~50MB** runtime instead of **>500MB** with PyTorch on serverless. |
| **SQLite** | Zero-ops persistence for demo; documents the product idea (field-scoped history). |
| **`src/fieldsense` package** | Engine logic testable without HTTP; shows intent to grow past a script. |
| **Vercel** | One-command deploy for reviewers; `api/index.py` wires repo paths + `/tmp` DB. |

---

## Future improvements (non-filler)

1. **Replace pickle with ONNX / sklearn version lockfile** — removes `InconsistentVersionWarning` class of risk.
2. **Managed DB + migrations** — Postgres + Alembic when multi-tenant or durable history matters.
3. **Authn + field-level ACL** — required before any non-research deployment.
4. **Leaf model as optional microservice** — keep API slim; ship GPU worker separately.
5. **Contract tests on OpenAPI** — freeze `/api` for integrators.

---

## Ethics & citation

Outputs are **not** agronomic, veterinary, or regulatory advice. Validate with qualified experts and local regulations.

See [`CITATION.cff`](CITATION.cff). Deeper methodology: [`docs/methodology.md`](docs/methodology.md), trust framing: [`docs/TRUST_AND_SAFETY.md`](docs/TRUST_AND_SAFETY.md).
