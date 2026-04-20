"""Evaluation helper for fertilizer metrics artifacts."""

from pathlib import Path


def main() -> None:
    p = Path("results/metrics/fertilizer_metrics.json")
    if not p.exists():
        print("No fertilizer metrics found. Run experiments/train_fertilizer.py first.")
        return
    print(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
