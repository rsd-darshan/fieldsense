"""Shim: Flask code imports `services.alerts`; implementation lives in `fieldsense.engine`."""

from fieldsense.engine.alerts import compute_alerts

__all__ = ["compute_alerts"]
