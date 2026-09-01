# data.py
"""Single place that knows where the data lives and what shape it should be.

Four scripts read these files. Four separate pd.read_* calls is the shape that
has produced four bugs in this project, so the path, the format and the
validation live here.
"""
import os
import pandas as pd

LISTINGS = 'listings_cleaned.csv'
DEVIATIONS = 'listing_deviations.csv'

MIN_LISTINGS = 15_000        # sanity floor; a truncated file should fail loudly
REQUIRED = ['area', 'block', 'property_type', 'size_marla', 'price_numeric',
            'url', 'title', 'generation', 'is_commercial']


def load_listings(path=LISTINGS):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Run clean_data.py to build it.")
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}. "
                         f"It has {len(df.columns)} columns and {len(df):,} rows.")
    if len(df) < MIN_LISTINGS:
        raise ValueError(f"{path} has only {len(df):,} rows, expected at least "
                         f"{MIN_LISTINGS:,}. The file may be truncated.")
    return df


def load_deviations(path=DEVIATIONS):
    """Returns an empty frame if absent; browse degrades rather than crashing."""
    if not os.path.exists(path):
        print(f"WARNING: {path} missing - run precompute_deviations.py", flush=True)
        return pd.DataFrame()
    return pd.read_csv(path)