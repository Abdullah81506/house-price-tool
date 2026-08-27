import pandas as pd
from clean_data import extract_area as old_extract_area
from location_parser import split_location

df = pd.read_csv('listings_cleaned.csv')

new = df['best_location'].apply(split_location)
df['_new_area'] = new.apply(lambda t: t[0])
df['_new_block'] = new.apply(lambda t: t[1])
df['_old_area'] = df['best_location'].apply(old_extract_area)

diff = df[df['_new_area'] != df['_old_area']]
print(f"area labels that CHANGE: {len(diff)} of {len(df)} ({len(diff)/len(df):.2%})")
if len(diff):
    print(diff[['best_location', '_old_area', '_new_area']].head(25).to_string())
    print("\ndistinct old labels affected:", diff['_old_area'].nunique())

print("\nblocks found:", df['_new_block'].notna().sum())

print("\n--- live parity: does serving produce the same string as training? ---")
import requests
from bs4 import BeautifulSoup
headers = {"User-Agent": "Mozilla/5.0"}

sample = df[df['_new_block'].notna() & df['url'].notna()].sample(5, random_state=1)
for _, r in sample.iterrows():
    try:
        resp = requests.get(r['url'], headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        h = soup.find(attrs={"aria-label": "Property header"})
        live = h.get_text(strip=True) if h else None
    except Exception as e:
        live = f"ERROR {type(e).__name__}"
    print(f"\nstored: {r['best_location']}")
    print(f"live  : {live}")
    print(f"stored -> {split_location(r['best_location'])}")
    print(f"live   -> {split_location(live)}")
