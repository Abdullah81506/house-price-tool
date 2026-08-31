"""Trains the price model and reports ALL / DENSE / NOVEL metrics.

NOVEL is the honest number: test listings with no near-identical twin in
training. Judge every change on it.

Report the NOVEL *fraction* alongside the NOVEL error. Adding listings shrinks
the novel block (more listings means more twins), so NOVEL error can improve
because the split changed rather than because the model did. The two are only
separable if both are printed.
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (mean_absolute_error,
                             mean_absolute_percentage_error, r2_score)
from sklearn.model_selection import train_test_split

df = pd.read_csv('listings_cleaned.csv')
print(f"{len(df):,} rows")
if 'generation' in df.columns:
    print(df['generation'].value_counts().to_string())

DESC_FLAGS = [c for c in df.columns if c.startswith("desc_")]
TEXT_FEATURES = ['description_length'] + DESC_FLAGS

features = (
    ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
     'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner',
     'is_commercial']
    + TEXT_FEATURES
)
print(f"\n{len(features)} features")

# `generation` is deliberately NOT a feature. It records when we scraped,
# not anything about the property.

x = df[features].copy()
y = df['price_numeric']

# Listings with no detail scrape have NaN here, but main.py's
# build_desc_features always returns 0 or 1 and /estimate sends all zeros.
# Training on NaN would teach a branch that serving never produces.
missing = x[TEXT_FEATURES].isna().any(axis=1).sum()
print(f"{missing:,} rows ({missing/len(x):.1%}) have no description features; "
      f"filling with 0 to match serving")
x[TEXT_FEATURES] = x[TEXT_FEATURES].fillna(0)

x['area'] = x['area'].astype('category')
x['property_type'] = x['property_type'].astype('category')

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(enable_categorical=True).fit(x_train, np.log1p(y_train))
y_pred = np.expm1(model.predict(x_test))

# ---- twin mask ----
KEY = ['area', 'property_type', 'size_marla', 'beds', 'baths']
train_keys = set(map(tuple, x_train[KEY].astype(str).values))
has_twin = np.array([tuple(k) in train_keys
                     for k in x_test[KEY].astype(str).values])


def report(label, yt, yp):
    err = np.abs(yp - yt) / yt
    print(f"--- {label}  (n={len(yt):,}) ---")
    print(f"  MAE            : {mean_absolute_error(yt, yp):,.0f} PKR")
    print(f"  R2             : {r2_score(yt, yp):.3f}")
    print(f"  MAPE           : {mean_absolute_percentage_error(yt, yp):.1%}")
    print(f"  median % error : {np.median(err):.1%}")
    print(f"  >30% off       : {(err > 0.30).mean():.1%}")
    print()


print()
report("ALL test listings", y_test, y_pred)
report("DENSE (has a twin)", y_test[has_twin], y_pred[has_twin])
report("NOVEL (no twin) <-- judge changes on this",
       y_test[~has_twin], y_pred[~has_twin])

print(f"NOVEL fraction: {(~has_twin).mean():.1%} of the test set "
      f"({(~has_twin).sum():,} of {len(has_twin):,})")
print("  Compare against the previous run before reading the NOVEL error as\n"
      "  an improvement. A smaller novel block is an easier novel block.\n")

# ---- does the model do better or worse on the delisted August rows? ----
if 'generation' in df.columns:
    gen_test = df.loc[x_test.index, 'generation']
    for g in gen_test.unique():
        m = (gen_test == g).values
        if m.sum() >= 30:
            e = np.abs(y_pred[m] - y_test[m]) / y_test[m]
            print(f"  {g:8s} n={m.sum():5d}  median error {np.median(e):.1%}")
    print()

imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("=== top 20 features by importance ===")
print(imp.head(20).to_string())

model.save_model('house_price_model.json')
print("\nModel saved. main.py applies np.expm1() to predictions.")
print("KNOWN_AREAS is derived from COMPS at startup in main.py; nothing to paste.")


import pandas as pd, numpy as np
# rerun the split from train.py, then:
err = np.abs(y_pred - y_test) / y_test
big = err > 0.30
d = df.loc[y_test.index]
print("worst-error areas:")
print(d.loc[big.values, 'area'].value_counts().head(15).to_string())
print("\narea sizes for those:")
counts = df['area'].value_counts()
print(counts[d.loc[big.values, 'area'].value_counts().head(15).index].to_string())