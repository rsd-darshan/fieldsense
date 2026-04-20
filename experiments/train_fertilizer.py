"""Baseline fertilizer training script scaffold."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SEED = 42
DATA = Path("data/raw/fertilizer_dataset.csv")


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA}")
    df = pd.read_csv(DATA)
    target = "Fertilizer Name"
    features = [c for c in df.columns if c != target]
    X = df[features]
    y = df[target]
    cat = [c for c in X.columns if X[c].dtype == "object"]
    num = [c for c in X.columns if c not in cat]
    prep = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
            ("num", "passthrough", num),
        ]
    )
    model = Pipeline(
        steps=[
            ("prep", prep),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=SEED)),
        ]
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "macro_f1": float(f1_score(y_test, pred, average="macro")),
        "seed": SEED,
    }
    out = Path("results/metrics/fertilizer_metrics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(metrics)


if __name__ == "__main__":
    main()
