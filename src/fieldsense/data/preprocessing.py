"""Basic preprocessing helpers for tabular experiments."""

from __future__ import annotations

import pandas as pd


def drop_missing(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna().reset_index(drop=True)
