"""Evaluation helper for crop metrics artifacts."""

from pathlib import Path


def main() -> None:
    p = Path("results/metrics/crop_metrics.json")
    if not p.exists():
        print("No crop metrics found. Run experiments/train_crop.py first.")
        return
    print(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
