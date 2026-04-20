# Data directory

This directory is the canonical location for tabular datasets in future revisions.

Recommended layout:

- `data/raw/` for immutable source files
- `data/processed/` for cleaned/derived artifacts

Raw tabular files are now stored in `data/raw/` and should be referenced from there by notebooks and scripts.
