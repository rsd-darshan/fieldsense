# Reproducibility

## Git LFS

Leaf classifier artifacts at `app/leaf_models/model.pth` and `app/leaf_models/model.onnx` use Git LFS:

```bash
git lfs install
git lfs pull
```

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Tests

```bash
python -m pytest tests/ -v
```

## Web UI

```bash
cd app
PORT=5050 python app.py
```

Pages: `/` (home), `/model1` (crop), `/model2` (fertilizer), `/model3` (leaf). Same paths on [the live deployment](https://fieldsense-ai-platform.vercel.app/) when `main` is deployed.

## Training scripts

```bash
python experiments/train_crop.py
python experiments/train_fertilizer.py
python experiments/evaluate_crop.py
python experiments/evaluate_fertilizer.py
```

## Leaf stack

Model 3 requires PyTorch and torchvision in the environment in addition to `requirements-dev.txt`, plus LFS for the `.pth` file.
