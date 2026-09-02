# data.py
"""Single place that knows where the data lives and what shape it should be.

Four scripts read these files. Four separate reads is the shape that has
produced four bugs in this project, so the path, the format and the validation
live here.

Data lives in a public HF dataset repo rather than the Space repo, because
Space repos reject binary files outright (so no parquet) and cap files at 10MB,
which listings_cleaned.csv exceeded at 27,712 rows. A local file takes
precedence when present, so local scripts use the working copy and the deployed
Space falls back to the hub.
"""
import os
import pandas as pd
from huggingface_hub import hf_hub_download

REPO = "Abdullah81506/house-price-tool-data"
LISTINGS = 'listings_cleaned.parquet'
DEVIATIONS = 'listing_deviations.parquet'

MIN_LISTINGS = 20_000
REQUIRED = ['area', 'block', 'property_type', 'size_marla', 'price_numeric',
            'url', 'title', 'generation', 'is_commercial']


def _read(filename):
    """Local copy first, then the hub."""
    if os.path.exists(filename):
        return pd.read_parquet(filename), "local"
    path = hf_hub_download(repo_id=REPO, filename=filename, repo_type="dataset")
    return pd.read_parquet(path), "hub"


def load_listings():
    df, src = _read(LISTINGS)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{LISTINGS} ({src}) is missing required columns: "
                         f"{missing}. It has {len(df.columns)} columns and "
                         f"{len(df):,} rows.")
    if len(df) < MIN_LISTINGS:
        raise ValueError(f"{LISTINGS} ({src}) has only {len(df):,} rows, "
                         f"expected at least {MIN_LISTINGS:,}. Possibly truncated.")
    print(f"loaded {len(df):,} listings from {src}", flush=True)
    return df


def load_deviations():
    try:
        df, src = _read(DEVIATIONS)
        print(f"loaded {len(df):,} deviations from {src}", flush=True)
        return df
    except Exception as e:
        print(f"WARNING: could not load {DEVIATIONS}: {e}", flush=True)
        return pd.DataFrame()