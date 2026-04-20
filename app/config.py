"""Environment-backed defaults for research deployments."""

import os


class Config:
    """Flask config loaded via app.config.from_object."""

    SECRET_KEY = (
        os.environ.get("FIELDSENSE_SECRET_KEY")
        or os.environ.get("FIELDENSE_SECRET_KEY")  # legacy typo, still honored
        or os.environ.get("SECRET_KEY")
        or "dev-fieldsense-insecure-change-me"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = bool(os.environ.get("FIELDSENSE_SECURE_COOKIE", ""))
