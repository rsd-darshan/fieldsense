"""Vercel Python entrypoint for FieldSense Flask app."""
from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT_DIR, "app")
SRC_DIR = os.path.join(ROOT_DIR, "src")

for p in (SRC_DIR, APP_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# On Vercel, filesystem is ephemeral/read-write only under /tmp
os.environ.setdefault("FIELDSENSE_DB_PATH", "/tmp/fieldsense.db")
os.environ.setdefault("FIELDSENSE_UPLOAD_DIR", "/tmp/fieldsense_uploads")
os.environ.setdefault("PORT", "8080")

from app import app as app  # noqa: E402
