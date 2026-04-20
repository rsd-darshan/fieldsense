"""Leaf image disease classification (ResNet-18, 38-class head).

Runtime inference uses **ONNX + onnxruntime** when `leaf_models/model.onnx` is
present (default for deployment). Falls back to the original **PyTorch** `.pth`
weights only when ONNX is missing (local research / export workflows).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LEAF_DIR = os.path.join(APP_DIR, "leaf_models")
MODEL_ONNX = os.path.join(LEAF_DIR, "model.onnx")
MODEL_PATH = os.path.join(LEAF_DIR, "model.pth")
DISEASE_CSV = os.path.join(LEAF_DIR, "disease_info.csv")
SUPPLEMENT_CSV = os.path.join(LEAF_DIR, "supplement_info.csv")

_NUM_CLASSES = 38

_ort_session: Optional[Any] = None
_torch_model: Optional[Any] = None
_torch_transform: Optional[Any] = None
_torch_device: Optional[Any] = None
_disease_df: Optional[pd.DataFrame] = None
_supplement_df: Optional[pd.DataFrame] = None


def _ensure_tables() -> Tuple[pd.DataFrame, pd.DataFrame]:
    global _disease_df, _supplement_df
    if _disease_df is None:
        _disease_df = pd.read_csv(DISEASE_CSV)
    if _supplement_df is None:
        _supplement_df = pd.read_csv(SUPPLEMENT_CSV, encoding="cp1252")
    return _disease_df, _supplement_df


def _preprocess_chw(image_path: str) -> np.ndarray:
    """Match torchvision Resize(256) → CenterCrop(224) → ToTensor → Normalize."""
    im = Image.open(image_path).convert("RGB")
    im = im.resize((256, 256), Image.Resampling.BILINEAR)
    w, h = im.size
    crop = 224
    left = max(0, (w - crop) // 2)
    top = max(0, (h - crop) // 2)
    im = im.crop((left, top, left + crop, top + crop))
    arr = np.asarray(im, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
    arr = (arr - mean) / std
    return np.expand_dims(arr, axis=0)


def _ensure_ort_session() -> Any:
    global _ort_session
    if _ort_session is None:
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        _ort_session = ort.InferenceSession(
            MODEL_ONNX,
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
    return _ort_session


def _predict_onnx(image_path: str) -> Dict[str, Any]:
    disease_df, supplement_df = _ensure_tables()
    session = _ensure_ort_session()
    inp = _preprocess_chw(image_path)
    name = session.get_inputs()[0].name
    logits = session.run(None, {name: inp})[0]
    index = int(np.argmax(logits, axis=1).item())
    if index < 0 or index >= len(disease_df):
        raise ValueError("Model output index out of range for disease table.")
    if index >= len(supplement_df):
        raise ValueError("Model output index out of range for supplement table.")
    drow = disease_df.iloc[index]
    srow = supplement_df.iloc[index]
    return {
        "prediction": str(drow["disease_name"]),
        "description": str(drow["description"]),
        "possible_steps": str(drow["Possible Steps"]),
        "supplement": str(srow["supplement name"]),
        "supplement_img": str(srow["supplement image"]),
        "supplement_prod_link": str(srow["buy link"]),
    }


def _device_pick():
    import torch

    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _build_torch_model(device) -> Any:
    import torch
    import torchvision.models as models
    from torchvision import transforms

    global _torch_transform
    net = models.resnet18(weights=None)
    net.fc = torch.nn.Linear(net.fc.in_features, _NUM_CLASSES)
    try:
        state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
    except TypeError:
        state = torch.load(MODEL_PATH, map_location=device)
    net.load_state_dict(state)
    net.to(device)
    net.eval()
    _torch_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    return net


def _ensure_torch_model() -> Tuple[Any, Any, Any]:
    global _torch_model, _torch_transform, _torch_device
    if _torch_model is None:
        import torch

        _torch_device = _device_pick()
        _torch_model = _build_torch_model(_torch_device)
    assert _torch_model is not None and _torch_transform is not None and _torch_device is not None
    return _torch_model, _torch_transform, _torch_device


def _predict_torch(image_path: str) -> Dict[str, Any]:
    import torch

    model, transform, device = _ensure_torch_model()
    disease_df, supplement_df = _ensure_tables()
    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)
    with torch.inference_mode():
        logits = model(tensor)
    index = int(torch.argmax(logits, dim=1).item())
    if index < 0 or index >= len(disease_df):
        raise ValueError("Model output index out of range for disease table.")
    if index >= len(supplement_df):
        raise ValueError("Model output index out of range for supplement table.")
    drow = disease_df.iloc[index]
    srow = supplement_df.iloc[index]
    return {
        "prediction": str(drow["disease_name"]),
        "description": str(drow["description"]),
        "possible_steps": str(drow["Possible Steps"]),
        "supplement": str(srow["supplement name"]),
        "supplement_img": str(srow["supplement image"]),
        "supplement_prod_link": str(srow["buy link"]),
    }


def predict_leaf_image(image_path: str) -> Dict[str, Any]:
    """Run the classifier and join metadata rows for the predicted class index."""
    if os.path.isfile(MODEL_ONNX):
        return _predict_onnx(image_path)
    if os.path.isfile(MODEL_PATH):
        return _predict_torch(image_path)
    raise FileNotFoundError("No leaf model weights (model.onnx or model.pth) found.")


def leaf_pipeline_ready() -> bool:
    has_meta = os.path.isfile(DISEASE_CSV) and os.path.isfile(SUPPLEMENT_CSV)
    if not has_meta:
        return False
    if os.path.isfile(MODEL_ONNX):
        return True
    return os.path.isfile(MODEL_PATH)


def leaf_backend() -> str:
    if os.path.isfile(MODEL_ONNX):
        return "onnx"
    if os.path.isfile(MODEL_PATH):
        return "torch"
    return "none"
