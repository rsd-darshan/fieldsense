"""Shim: Flask code imports `services.intelligence`; implementation lives in `fieldsense.engine`."""

from fieldsense.engine.intelligence import compute_unified, merge_engine_into_output

__all__ = ["compute_unified", "merge_engine_into_output"]
