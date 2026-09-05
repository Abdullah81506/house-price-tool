"""Checks the pipeline output before anything is published.

The weekly job retrains without anyone watching, so a bad scrape could quietly
replace a working model. Every check here must pass or the workflow stops and
the live data is left alone.

Thresholds were set against measured values, not picked:
    scraped     ~26,700   fail under 15,000
    cleaned     ~25,800   fail under 18,000
    areas          316    fail under 200
    judged      ~21,000   fail under 12,000
    NOVEL median  14.4%   fail over 17%   (5-seed range 13.2-15.7)
    NOVEL >30%    23.1%   fail over 28%   (5-seed range 21.4-24.5)

The model bounds sit roughly two points beyond the worst seed observed, which
is wide enough not to trip on noise and tight enough to catch a real break.
"""
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

MIN_SCRAPED = 15_000
MIN_CLEANED = 18_000
MIN_AREAS = 200
MIN_JUDGED = 12_000
MAX_NOVEL_MEDIAN = 0.17
MAX_NOVEL_TAIL = 0.28
SEEDS = [0, 7, 42, 99, 2024]

failures = []


def check(name, ok, detail):
    print(f"{'PASS' if ok else 'FAIL'}  {name:<22} {detail}")
    if not ok:
        failures.append(name)


# ------------------------------------------------------------- scrape size
scraped = sum(len(pd.read_csv(f)) for f in
              ('listings_houses.csv', 'listings_flats.csv'))
check("scraped listings", scraped >= MIN_SCRAPED,
      f"{scraped:,} (floor {MIN_SCRAPED:,})")

# ------------------------------------------------------------ cleaned file
df = pd.read_parquet('listings_cleaned.parquet')
check("cleaned rows", len(df) >= MIN_CLEANED,
      f"{len(df):,} (floor {MIN_CLEANED:,})")

areas = df['area'].nunique()
check("areas", areas >= MIN_AREAS, f"{areas} (floor {MIN_AREAS})")

check("prices parsed", df['price_numeric'].notna().all(),
      f"{df['price_numeric'].notna().sum():,} of {len(df):,}")
check("sizes parsed", df['size_marla'].notna().all(),
      f"{df['size_marla'].notna().sum():,} of {len(df):,}")

# --------------------------------------------------------------- verdicts
dev = pd.read_parquet('listing_deviations.parquet')
check("judged listings", len(dev) >= MIN_JUDGED,
      f"{len(dev):,} (floor {MIN_JUDGED:,})")

flagged = (dev['position'] != 'within').mean()
check("flag rate", 0.10 <= flagged <= 0.30, f"{flagged:.1%} (expected 10-30%)")

# ------------------------------------------------------------ model, 5 seeds
DESC = [c for c in df.columns if c.startswith("desc_")]
TEXT = ['description_length'] + DESC
feats = (['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
          'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner',
          'is_commercial'] + TEXT)
KEY = ['area', 'property_type', 'size_marla', 'beds', 'baths']

x = df[feats].copy()
y = df['price_numeric']
x[TEXT] = x[TEXT].fillna(0)
x['area'] = x['area'].astype('category')
x['property_type'] = x['property_type'].astype('category')

meds, tails = [], []
for seed in SEEDS:
    xtr, xte, ytr, yte = train_test_split(x, y, test_size=0.2, random_state=seed)
    m = xgb.XGBRegressor(enable_categorical=True, random_state=seed).fit(
        xtr, np.log1p(ytr))
    p = np.expm1(m.predict(xte))
    keys = set(map(tuple, xtr[KEY].astype(str).values))
    nov = ~np.array([tuple(k) in keys for k in xte[KEY].astype(str).values])
    e = np.abs(p - yte) / yte
    meds.append(np.median(e[nov]))
    tails.append((e[nov] > 0.30).mean())
    print(f"  seed {seed:5d}  NOVEL median {meds[-1]:.1%}  >30% {tails[-1]:.1%}")

med, tail = float(np.mean(meds)), float(np.mean(tails))
check("NOVEL median", med <= MAX_NOVEL_MEDIAN,
      f"{med:.2%} (ceiling {MAX_NOVEL_MEDIAN:.0%})")
check("NOVEL >30% off", tail <= MAX_NOVEL_TAIL,
      f"{tail:.2%} (ceiling {MAX_NOVEL_TAIL:.0%})")

# ------------------------------------------------------------------ verdict
print()
if failures:
    print(f"BLOCKED: {len(failures)} check(s) failed: {', '.join(failures)}")
    print("Nothing was uploaded. The live data is unchanged.")
    sys.exit(1)

print("All checks passed.")