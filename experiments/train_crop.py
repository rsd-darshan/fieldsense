"""Baseline crop training script scaffold."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

SEED = 42
DATA = Path("data/raw/crop_recommendation.csv")


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Missing dataset: {DATA}")
    df = pd.read_csv(DATA)
    # N, P, K = nitrogen, phosphorus, potassium (dataset column names)
    feature_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X = df[feature_cols]
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    model = RandomForestClassifier(n_estimators=200, random_state=SEED)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "macro_f1": float(f1_score(y_test, pred, average="macro")),
        "seed": SEED,
    }
    out = Path("results/metrics/crop_metrics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(metrics)


if __name__ == "__main__":
    main()
