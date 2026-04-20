"""One-shot export of app/leaf_models/model.pth to ONNX for slim serverless inference."""
from __future__ import annotations

import argparse
import os
import sys

import torch
import torchvision.models as models

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
MODEL_PATH = os.path.join(APP_DIR, "leaf_models", "model.pth")
OUT_PATH = os.path.join(APP_DIR, "leaf_models", "model.onnx")
_NUM_CLASSES = 38


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=OUT_PATH, help="Where to write model.onnx")
    args = parser.parse_args()
    if not os.path.isfile(MODEL_PATH):
        print(f"Missing weights: {MODEL_PATH}", file=sys.stderr)
        sys.exit(1)
    device = torch.device("cpu")
    net = models.resnet18(weights=None)
    net.fc = torch.nn.Linear(net.fc.in_features, _NUM_CLASSES)
    try:
        state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    except TypeError:
        state = torch.load(MODEL_PATH, map_location=device)
    net.load_state_dict(state)
    net.eval()
    dummy = torch.randn(1, 3, 224, 224, device=device)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    torch.onnx.export(
        net,
        dummy,
        args.output,
        input_names=["input"],
        output_names=["logits"],
        opset_version=17,
    )
    print(f"Wrote {args.output} ({os.path.getsize(args.output) // 1024 // 1024} MiB approx)")


if __name__ == "__main__":
    main()
