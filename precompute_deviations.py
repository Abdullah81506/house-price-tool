"""
Computes each listing's position against its comparables, once.
Run after every retrain / re-clean. Saves listing_deviations.csv,
which main.py loads at startup so /listings is instant.

Uses get_comparables from main.py so browse and paste-a-link
always agree on the same listing.
"""
import os
import numpy as np
import pandas as pd
import xgboost as xgb

from main import COMPS, get_comparables
from config import MARGIN, MAX_DEVIATION

df = COMPS.copy()
print(f"{len(df):,} listings (installment/commercial already excluded)")

model = xgb.XGBRegressor()
model.load_model('house_price_model.json')

DESC_FLAGS = [c for c in df.columns if c.startswith('desc_')]
FEATURES = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
            'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner',
            'is_commercial', 'description_length'] + DESC_FLAGS
X = df[FEATURES].copy()
X['area'] = X['area'].astype('category')
X['property_type'] = X['property_type'].astype('category')
df['predicted_price'] = np.expm1(model.predict(X))
print("model predictions computed")

rows = []
for i, r in df.iterrows():
    if r['area'] == 'Other':
        continue

    c = get_comparables(
        r['area'], r['property_type'], r['size_marla'],
        block=r['block'] if isinstance(r['block'], str) else None,
        url=r['url'],
    )
    if c is None:
        continue

    ask = float(r['price_numeric'])
    if ask < c['low'] * (1 - MARGIN):
        position, deviation = "below", (c['low'] - ask) / c['low']
    elif ask > c['high'] * (1 + MARGIN):
        position, deviation = "above", (ask - c['high']) / c['high']
    else:
        position, deviation = "within", 0.0

    rows.append({
        "row_id": int(i),
        "title": r['title'],
        "url": r['url'],
        "area": r['area'],
        "block": r['block'] if isinstance(r['block'], str) else None,
        "scope": c['scope'],
        "property_type": r['property_type'],
        "size_marla": round(float(r['size_marla']), 2),
        "beds": r['beds'],
        "baths": r['baths'],
        "asking_price": ask,
        "comp_count": c['count'],
        "comp_low": c['low'],
        "comp_typical": c['typical'],
        "comp_high": c['high'],
        "position": position,
        "deviation": round(float(deviation), 4),
        "confidence": "high" if c['count'] >= 20 else "low",
        "predicted_price": float(r['predicted_price']),
    })

out = pd.DataFrame(rows)

# --- agents relist the same property; show it once ---
before_dedup = len(out)
out['_dedup_key'] = out['title'].astype(str).str.lower().apply(lambda t: ' '.join(t.split()))
out = out.drop_duplicates(subset=['_dedup_key', 'asking_price', 'area'], keep='first')
out = out.drop(columns=['_dedup_key'])
before_cap = len(out)

# --- extreme deviations are price typos far more often than real outliers ---
out = out[out['deviation'] <= MAX_DEVIATION]

if os.path.exists('listing_images.csv'):
    out = out.merge(pd.read_csv('listing_images.csv'), on='url', how='left')
    print(f"merged photos: {out['image'].notna().sum():,}")

out.to_csv('listing_deviations.csv', index=False)

print(f"\nremoved duplicates      : {before_dedup - before_cap:,}")
print(f"removed extreme (>{MAX_DEVIATION:.0%}) : {before_cap - len(out):,}")
print(f"\nsaved listing_deviations.csv: {len(out):,} judged")
print(out['position'].value_counts(normalize=True).mul(100).round(1).to_string())
print(out['scope'].value_counts().to_string())
print(f"\nhigh-confidence flagged: "
      f"{len(out[(out['position'] != 'within') & (out['confidence'] == 'high')]):,}")