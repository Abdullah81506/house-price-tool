"""
Bulk detail-page scraper. Resumable: re-run after any interruption and it
picks up where it stopped. Expects listings_with_urls.csv to have a 'url' column.
"""
import pandas as pd
import time
import os
import sys
from detail_parser import parse_detail_page

INPUT = ["listings_houses.csv", "listings_flats.csv"]
OUTPUT = "detail_features.csv"
DELAY = 1.5              # seconds between requests
SAVE_EVERY = 50          # checkpoint frequency
MAX_CONSECUTIVE_FAILS = 15

src = pd.concat([pd.read_csv(f) for f in INPUT], ignore_index=True)
if "url" not in src.columns:
    sys.exit("ERROR: no 'url' column - re-run the search scraper with link capture first")

urls = src["url"].dropna().unique().tolist()
print(f"{len(urls):,} unique urls in source")

# --- resume from whatever we already have ---
done = {}
if os.path.exists(OUTPUT):
    prev = pd.read_csv(OUTPUT)
    done = {r["url"]: r.to_dict() for _, r in prev.iterrows()}
    print(f"resuming: {len(done):,} already scraped")

todo = [u for u in urls if u not in done]
print(f"{len(todo):,} remaining  (~{len(todo)*DELAY/3600:.1f} hours at {DELAY}s delay)\n")

rows = list(done.values())
consecutive_fails = 0

try:
    for i, url in enumerate(todo, 1):
        feats = parse_detail_page(url)
        feats["url"] = url
        rows.append(feats)

        if feats.get("_error"):
            consecutive_fails += 1
            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                print(f"\n{MAX_CONSECUTIVE_FAILS} failures in a row - likely blocked.")
                print("Saving progress and stopping. Wait a while, then re-run.")
                break
        else:
            consecutive_fails = 0

        if i % SAVE_EVERY == 0:
            pd.DataFrame(rows).to_csv(OUTPUT, index=False)
            pct = 100 * i / len(todo)
            print(f"  {i:,}/{len(todo):,} ({pct:.1f}%)  saved")

        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\ninterrupted - saving progress")

df = pd.DataFrame(rows)
df.to_csv(OUTPUT, index=False)

ok = df[df.get("description_length").notna()] if "description_length" in df else df
print(f"\nsaved {OUTPUT}: {len(df):,} rows, {len(ok):,} successful")
if "built_in_year" in df.columns:
    print(f"built_in_year fill: {df['built_in_year'].notna().mean():.1%}")