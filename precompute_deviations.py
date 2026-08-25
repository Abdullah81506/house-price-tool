"""
Computes each listing's position against its comparables, once.
Run after every retrain / re-clean. Saves listing_deviations.csv,
which main.py loads at startup so /listings is instant.
"""
import pandas as pd
import numpy as np

BAND_LO, BAND_HI = 0.15, 0.85
MARGIN = 0.05
MIN_COMPS = 5
MAX_DEVIATION = 1.0        # >100% off is almost always bad data, not a real outlier

# Listings whose quoted price isn't the property price
PRICE_NOT_REAL = ['installment', 'instalment', 'booking', 'on easy', 'down payment']

df = pd.read_csv('listings_cleaned.csv')
df = df[df['price_numeric'].notna() & df['size_marla'].notna() & (df['size_marla'] > 0)].copy()
df = df.reset_index(drop=True)
import xgboost as xgb
model = xgb.XGBRegressor()
model.load_model('house_price_model.json')

DESC_FLAGS = [c for c in df.columns if c.startswith('desc_')]
FEATURES = ['size_marla','beds','baths','area','property_type','floor',
            'is_new','is_furnished','is_luxury','has_basement','is_corner','is_commercial',
            'description_length'] + DESC_FLAGS
X = df[FEATURES].copy()
X['area'] = X['area'].astype('category')
X['property_type'] = X['property_type'].astype('category')
df['predicted_price'] = np.expm1(model.predict(X))
print("model predictions computed")
print(f"{len(df):,} listings")

rows = []
skipped_commercial = skipped_installment = 0

for (area, ptype), g in df.groupby(['area', 'property_type'], observed=True):
    if area == 'Other':
        continue
    sizes = g['size_marla'].values
    prices = g['price_numeric'].values
    idx = g.index.values
    titles = g['title'].values
    commercial = g['is_commercial'].values

    for i in range(len(g)):
        # --- skip listings that aren't comparable to residential property ---
        if commercial[i] == 1:
            skipped_commercial += 1
            continue
        title_low = str(titles[i]).lower()
        if any(w in title_low for w in PRICE_NOT_REAL):
            skipped_installment += 1
            continue

        lo, hi = sizes[i] * 0.7, sizes[i] * 1.3
        mask = (sizes >= lo) & (sizes <= hi)
        mask[i] = False                      # exclude itself
        comp_prices = prices[mask]

        if len(comp_prices) >= 20:           # trim junk only when there's enough
            comp_sizes = sizes[mask]
            ppm = comp_prices / comp_sizes
            keep = (ppm >= np.quantile(ppm, 0.02)) & (ppm <= np.quantile(ppm, 0.98))
            comp_prices = comp_prices[keep]

        if len(comp_prices) < MIN_COMPS:
            continue

        low = float(np.quantile(comp_prices, BAND_LO))
        typical = float(np.median(comp_prices))
        high = float(np.quantile(comp_prices, BAND_HI))
        ask = float(prices[i])

        if ask < low * (1 - MARGIN):
            position, deviation = "below", (low - ask) / low
        elif ask > high * (1 + MARGIN):
            position, deviation = "above", (ask - high) / high
        else:
            position, deviation = "within", 0.0

        rows.append({
            "row_id": int(idx[i]),
            "title": titles[i],
            "url": g['url'].values[i],
            "area": area,
            "property_type": ptype,
            "size_marla": round(float(sizes[i]), 2),
            "beds": g['beds'].values[i],
            "baths": g['baths'].values[i],
            "asking_price": ask,
            "comp_count": int(len(comp_prices)),
            "comp_low": low,
            "comp_typical": typical,
            "comp_high": high,
            "position": position,
            "deviation": round(float(deviation), 4),
            "confidence": "high" if len(comp_prices) >= 20 else "low",
            "predicted_price": float(g['predicted_price'].values[i]),
        })

out = pd.DataFrame(rows)

# --- agents relist the same property; show it once ---
before_dedup = len(out)
out['_dedup_key'] = out['title'].str.lower().apply(lambda t: ' '.join(str(t).split()))
out = out.drop_duplicates(subset=['_dedup_key', 'asking_price', 'area'], keep='first')
out = out.drop(columns=['_dedup_key'])
# --- extreme deviations are price typos far more often than real outliers ---
before_cap = len(out)
out = out[out['deviation'] <= MAX_DEVIATION]

import os
if os.path.exists('listing_images.csv'):
    out = out.merge(pd.read_csv('listing_images.csv'), on='url', how='left')
    print(f"merged photos: {out['image'].notna().sum():,}")

out.to_csv('listing_deviations.csv', index=False)

print(f"\nskipped commercial      : {skipped_commercial:,}")
print(f"skipped installment/etc : {skipped_installment:,}")
print(f"removed duplicates      : {before_dedup - before_cap:,}")
print(f"removed extreme (>{MAX_DEVIATION:.0%}) : {before_cap - len(out):,}")
print(f"\nsaved listing_deviations.csv: {len(out):,} judged")
print(out['position'].value_counts(normalize=True).mul(100).round(1).to_string())
print(f"\nhigh-confidence flagged: "
      f"{len(out[(out['position'] != 'within') & (out['confidence'] == 'high')]):,}")