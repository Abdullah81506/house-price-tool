# import pandas as pd
# df = pd.read_csv('listings_cleaned.csv')
# # print(df[['price_numeric', 'size_marla', 'beds', 'baths', 'area']].isnull().sum())
# # print(df.shape)
#
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
# from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
#
# features = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# x = df[features].copy()
# y = df['price_numeric']
# x['area'] = x['area'].astype('category')
# x['property_type'] = x['property_type'].astype('category')
#
# x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
# model = xgb.XGBRegressor(enable_categorical=True).fit(x_train, y_train)
# y_pred = model.predict(x_test)
# mae = mean_absolute_error(y_test, y_pred)
# r2 = r2_score(y_test, y_pred)
# mape = mean_absolute_percentage_error(y_test, y_pred)
# mse = mean_squared_error(y_test, y_pred)
# print(f"Mean Absolute Error: {mae:,.0f} PKR")
# print(f"R² score: {r2:.3f}")
# print(f"MAPE: {mape:.1%}")
# print(f"MSE: {mse:,.0f}")
# model.save_model('house_price_model.json')
# print('Model saved successfully')
# ===============================================================================
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
# from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error, mean_squared_error
#
# df = pd.read_csv('listings_cleaned.csv')
#
# features = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# x = df[features].copy()
# y = df['price_numeric']
# x['area'] = x['area'].astype('category')
# x['property_type'] = x['property_type'].astype('category')
#
# x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
#
#
# def report(name, y_true, y_pred):
#     print(f"--- {name} ---")
#     print(f"  MAE : {mean_absolute_error(y_true, y_pred):,.0f} PKR")
#     print(f"  R²  : {r2_score(y_true, y_pred):.3f}")
#     print(f"  MAPE: {mean_absolute_percentage_error(y_true, y_pred):.1%}")
#     # median % error is more robust than MAPE on skewed prices
#     med = np.median(np.abs(y_pred - y_true) / y_true)
#     print(f"  median % error: {med:.1%}")
#     # is the model biased high or low?
#     bias = np.median((y_pred - y_true) / y_true)
#     print(f"  median signed bias: {bias:+.1%}   (positive = overpredicting)")
#     print()
#
#
# # ---------- A: current approach, raw price target ----------
# model_raw = xgb.XGBRegressor(enable_categorical=True).fit(x_train, y_train)
# pred_raw = model_raw.predict(x_test)
# report("RAW target (current)", y_test, pred_raw)
#
# # ---------- B: log target ----------
# y_train_log = np.log1p(y_train)                      # CHANGE 1: log the training target
# model_log = xgb.XGBRegressor(enable_categorical=True).fit(x_train, y_train_log)
# pred_log = np.expm1(model_log.predict(x_test))       # CHANGE 2: unwrap before scoring
# report("LOG target (new)", y_test, pred_log)
#
# # ---------- save whichever you want to keep ----------
# SAVE_LOG_MODEL = True     # flip to False to keep the raw-target model
#
# if SAVE_LOG_MODEL:
#     model_log.save_model('house_price_model.json')
#     print(">>> Saved LOG-target model.")
#     print(">>> main.py MUST now wrap predictions: float(np.expm1(model.predict(row)[0]))")
# else:
#     model_raw.save_model('house_price_model.json')
#     print(">>> Saved RAW-target model. main.py needs no change.")
#
# # ---------- regenerate KNOWN_AREAS for main.py ----------
# areas = sorted(df['area'].dropna().unique().tolist())
# print(f"\n>>> {len(areas)} area categories. Paste into main.py as KNOWN_AREAS:\n")
# print("KNOWN_AREAS = [")
# for a in areas:
#     print(f"    {a!r},")
# print("]")
# ==================================================================================================
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
# from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error
#
# df = pd.read_csv('listings_cleaned.csv')
#
# features = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# x = df[features].copy()
# y = df['price_numeric']
# x['area'] = x['area'].astype('category')
# x['property_type'] = x['property_type'].astype('category')
#
# SEEDS = [0, 7, 21, 42, 99, 123, 2024]
# rows = []
#
# for seed in SEEDS:
#     x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, random_state=seed)
#
#     m_raw = xgb.XGBRegressor(enable_categorical=True, random_state=seed).fit(x_tr, y_tr)
#     p_raw = m_raw.predict(x_te)
#
#     m_log = xgb.XGBRegressor(enable_categorical=True, random_state=seed).fit(x_tr, np.log1p(y_tr))
#     p_log = np.expm1(m_log.predict(x_te))
#
#     for label, p in [("raw", p_raw), ("log", p_log)]:
#         rows.append({
#             "seed": seed,
#             "target": label,
#             "mape": mean_absolute_percentage_error(y_te, p) * 100,
#             "r2": r2_score(y_te, p),
#             "mae": mean_absolute_error(y_te, p),
#             "median_pct_err": np.median(np.abs(p - y_te) / y_te) * 100,
#         })

# res = pd.DataFrame(rows)
#
# print("=== per-seed results ===")
# print(res.pivot(index="seed", columns="target",
#                 values=["mape", "r2", "median_pct_err"]).round(3).to_string())
#
# print("\n=== paired differences (log - raw), per seed ===")
# piv = res.pivot(index="seed", columns="target", values=["mape", "r2", "median_pct_err"])
# for metric in ["mape", "r2", "median_pct_err"]:
#     diff = piv[metric]["log"] - piv[metric]["raw"]
#     print(f"{metric:>16}: " + "  ".join(f"{d:+.3f}" for d in diff))
#     wins = (diff < 0).sum() if metric != "r2" else (diff > 0).sum()
#     print(f"{'':>16}  log better on {wins}/{len(SEEDS)} seeds, "
#           f"mean diff {diff.mean():+.3f}")
#
# ============================================================
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
# from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error
#
# df = pd.read_csv('listings_cleaned.csv')
#
# features = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# x = df[features].copy()
# y = df['price_numeric']
# x['area'] = x['area'].astype('category')
# x['property_type'] = x['property_type'].astype('category')
#
# x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
#
# # ---- train on log price ----
# model = xgb.XGBRegressor(enable_categorical=True).fit(x_train, np.log1p(y_train))
# y_pred = np.expm1(model.predict(x_test))
#
# # ---- twin mask: which test rows share a feature vector with a training row? ----
# KEY = ['area', 'property_type', 'size_marla', 'beds', 'baths']
# train_keys = set(map(tuple, x_train[KEY].astype(str).values))
# has_twin = np.array([tuple(k) in train_keys for k in x_test[KEY].astype(str).values])
#
# # ---- report overall AND novel-only ----
# def report(label, y_true, y_pred):
#     err = np.abs(y_pred - y_true) / y_true
#     print(f"--- {label}  (n={len(y_true):,}) ---")
#     print(f"  MAE            : {mean_absolute_error(y_true, y_pred):,.0f} PKR")
#     print(f"  R²             : {r2_score(y_true, y_pred):.3f}")
#     print(f"  MAPE           : {mean_absolute_percentage_error(y_true, y_pred):.1%}")
#     print(f"  median % error : {np.median(err):.1%}")
#     print(f"  >30% off       : {(err > 0.30).mean():.1%}")
#     print()
#
# report("ALL test listings", y_test, y_pred)
# report("DENSE (has a twin in training)", y_test[has_twin], y_pred[has_twin])
# report("NOVEL (no twin) <-- the honest number", y_test[~has_twin], y_pred[~has_twin])
#
# model.save_model('house_price_model.json')
# print("Model saved. Remember: main.py must use np.expm1() on predictions.")

# print(df['price_numeric'].describe())
# print(df.nsmallest(5, 'price_numeric')[['title', 'price', 'price_numeric']])
# print(df.nlargest(5, 'price_numeric')[['title', 'price', 'price_numeric']])
# print(df.nlargest(5, 'size_marla')[['title', 'size', 'size_marla']])
# print(df.loc[[183, 1920, 282, 1796], ['title', 'price']])
# comparison = pd.DataFrame({'actual': y_test, 'predicted': y_pred})
# comparison['error'] = abs(comparison['actual'] - comparison['predicted'])
# comparison['pct_error'] = comparison['error'] / comparison['actual'] * 100
# print(comparison[comparison['actual'] < 100_000_000]['pct_error'].describe())
# print(comparison[comparison['actual'] >= 100_000_000]['pct_error'].describe())
# print(comparison.sort_values('error', ascending=False).head(10))
# print(df[df['price_numeric'] > 150_000_000].shape[0])
# comparison = pd.DataFrame({'actual': y_test, 'predicted': y_pred})
# comparison['property_type'] = x_test['property_type'].values
# comparison['error'] = abs(comparison['actual'] - comparison['predicted'])
# comparison['pct_error'] = comparison['error'] / comparison['actual'] * 100
#
# print(comparison[comparison['property_type'] == 'House']['pct_error'].describe())
# print(comparison[comparison['property_type'] == 'Flat']['pct_error'].describe())
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt

# n_estimators_range = [50, 100, 150, 200, 300, 400, 500]
# train_mape = []
# test_mape = []
#
# for n in n_estimators_range:
#     model = xgb.XGBRegressor(n_estimators=n, enable_categorical=True)
#     model.fit(x_train, y_train)
#     train_pred = model.predict(x_train)
#     test_pred = model.predict(x_test)
#     train_mape.append(mean_absolute_percentage_error(y_train, train_pred))
#     test_mape.append(mean_absolute_percentage_error(y_test, test_pred))
#
# plt.plot(n_estimators_range, train_mape, label='Train MAPE')
# plt.plot(n_estimators_range, test_mape, label='Test MAPE')
# plt.xlabel('n_estimators')
# plt.ylabel('MAPE')
# plt.legend()
# plt.show()
# max_depth_range = [2, 3, 4, 5, 6, 8, 10, 12]
# train_mape = []
# test_mape = []
#
# for d in max_depth_range:
#     model = xgb.XGBRegressor(max_depth=d, enable_categorical=True)
#     model.fit(x_train, y_train)
#     train_pred = model.predict(x_train)
#     test_pred = model.predict(x_test)
#     train_mape.append(mean_absolute_percentage_error(y_train, train_pred))
#     test_mape.append(mean_absolute_percentage_error(y_test, test_pred))
#
# plt.plot(max_depth_range, train_mape, label='Train MAPE')
# plt.plot(max_depth_range, test_mape, label='Test MAPE')
# plt.xlabel('max_depth')
# plt.ylabel('MAPE')
# plt.legend()
# plt.show()


import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

df = pd.read_csv('listings_cleaned.csv')

DESC_FLAGS = [c for c in df.columns if c.startswith("desc_")]

features = (
    # original
    ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
     'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
    # description signals
    + ['description_length'] + DESC_FLAGS
)
print(f"{len(features)} features\n")

x = df[features].copy()
y = df['price_numeric']
x['area'] = x['area'].astype('category')
x['property_type'] = x['property_type'].astype('category')

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(enable_categorical=True).fit(x_train, np.log1p(y_train))
y_pred = np.expm1(model.predict(x_test))

# ---- twin mask ----
KEY = ['area', 'property_type', 'size_marla', 'beds', 'baths']
train_keys = set(map(tuple, x_train[KEY].astype(str).values))
has_twin = np.array([tuple(k) in train_keys for k in x_test[KEY].astype(str).values])


def report(label, yt, yp):
    err = np.abs(yp - yt) / yt
    print(f"--- {label}  (n={len(yt):,}) ---")
    print(f"  MAE            : {mean_absolute_error(yt, yp):,.0f} PKR")
    print(f"  R²             : {r2_score(yt, yp):.3f}")
    print(f"  MAPE           : {mean_absolute_percentage_error(yt, yp):.1%}")
    print(f"  median % error : {np.median(err):.1%}")
    print(f"  >30% off       : {(err > 0.30).mean():.1%}")
    print()


report("ALL test listings", y_test, y_pred)
report("DENSE (has a twin)", y_test[has_twin], y_pred[has_twin])
report("NOVEL (no twin) <-- judge changes on this", y_test[~has_twin], y_pred[~has_twin])

# ---- which new features actually earned their place? ----
imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("=== top 20 features by importance ===")
print(imp.head(20).to_string())

model.save_model('house_price_model.json')
print("\nModel saved. main.py needs np.expm1() on predictions.")

areas = sorted(df['area'].dropna().unique().tolist())
print(f"\n>>> {len(areas)} areas. Paste into main.py as KNOWN_AREAS:\n")
print("KNOWN_AREAS = [")
for a in areas:
    print(f"    {a!r},")
print("]")