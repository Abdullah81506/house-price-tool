"""Bulk detail-page scraper. Resumable: re-run after any interruption and it
picks up where it stopped.

Two things this handles that the previous version did not.

1. Resume keys on the NEW fields, not just the URL. Rows scraped with the old
   parser have a url but no page_text_raw / description_raw / gallery_ids, so
   keying on url alone would skip them and leave the new fields on only half
   the data.

2. Writes by appending a row at a time. page_text_raw makes the output file
   large (~150MB+), and rewriting the whole file every 50 listings gets slower
   as it grows.

Delisted listings fail here. When that happens the old row is kept rather than
replaced with an error, so nothing already collected is lost.
"""
import csv
import os
import sys
import time

import pandas as pd

from detail_parser import (BOOL_FEATURES, DESC_KEYWORDS, NUM_FEATURES,
                           parse_detail_page)

INPUT = ["listings_houses.csv", "listings_flats.csv"]
OUTPUT = "detail_features.csv"
OLD = "raw_backup/detail_features_august.csv"   # fallback for delisted rows
DELAY = 1.5
MAX_CONSECUTIVE_FAILS = 30

# A row counts as already done only if this column is populated. It exists
# only in the new parser's output.
NEW_FIELD_MARKER = "page_text_raw"

# Fixed column order, built from the parser's own constants so it cannot
# drift from what parse_detail_page actually returns.
FIELDNAMES = (
    ["url", "detail_scraped_at", "detail_location", "purpose",
     "detail_added_text", "property_details_raw",
     "description_raw", "description_length"]
    + ["desc_" + k for k in DESC_KEYWORDS]
    + [f.lower().replace(" ", "_") for f in NUM_FEATURES]
    + ["has_" + f.lower().replace(" ", "_") for f in BOOL_FEATURES]
    + ["gallery_ids", "gallery_count", "agent_name", "_agent_label_used",
       "page_text_raw", "_error"]
)


def load_done(path):
    """URLs already scraped with the new parser."""
    if not os.path.exists(path):
        return set()
    try:
        prev = pd.read_csv(path, usecols=["url", NEW_FIELD_MARKER])
    except (ValueError, pd.errors.EmptyDataError):
        print(f"{path} exists but predates the new fields; it will be rebuilt.")
        return set()
    done = set(prev.loc[prev[NEW_FIELD_MARKER].notna(), "url"])
    print(f"resuming: {len(done):,} already scraped with the new parser")
    return done


def load_fallback(path):
    """Old-parser rows, used when a listing is delisted and cannot be refetched."""
    if not os.path.exists(path):
        print(f"no fallback file at {path}; delisted listings will be lost")
        return {}
    prev = pd.read_csv(path)
    if "_error" in prev.columns:
        prev = prev[prev["_error"].isna()]
    fb = {r["url"]: r.dropna().to_dict() for _, r in prev.iterrows()}
    print(f"fallback available for {len(fb):,} listings")
    return fb


if __name__ == "__main__":
    src = pd.concat([pd.read_csv(f) for f in INPUT], ignore_index=True)
    if "url" not in src.columns:
        sys.exit("ERROR: no 'url' column in the source files")

    urls = src["url"].dropna().unique().tolist()
    print(f"{len(urls):,} unique urls in source")

    done = load_done(OUTPUT)
    fallback = load_fallback(OLD)

    todo = [u for u in urls if u not in done]
    print(f"{len(todo):,} to scrape "
          f"(~{len(todo) * DELAY / 3600:.1f} hours at {DELAY}s delay)\n")

    if not todo:
        print("nothing to do")
        sys.exit(0)

    write_header = not done          # fresh file, or one being rebuilt
    mode = "w" if write_header else "a"
    consecutive_fails = 0
    ok = failed = recovered = 0

    with open(OUTPUT, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        try:
            for i, url in enumerate(todo, 1):
                feats = parse_detail_page(url)
                feats["url"] = url

                if feats.get("_error"):
                    consecutive_fails += 1
                    failed += 1
                    if consecutive_fails <= 3:
                        print(f"    {feats['_error'][:90]}")
                    # delisted: keep whatever we already had rather than
                    # writing an error row over it
                    if url in fallback:
                        row = dict(fallback[url])
                        row["url"] = url
                        row["_error"] = feats["_error"]
                        feats = row
                        recovered += 1
                    if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                        print(f"\n{consecutive_fails} failures in a row. "
                              f"Pausing 10 minutes, then continuing.")
                        f.flush()
                        time.sleep(600)
                        consecutive_fails = 0
                else:
                    consecutive_fails = 0
                    ok += 1

                writer.writerow(feats)

                if i % 50 == 0:
                    f.flush()
                    pct = 100 * i / len(todo)
                    eta = (len(todo) - i) * DELAY / 3600
                    print(f"  {i:,}/{len(todo):,} ({pct:.1f}%)  "
                          f"ok={ok:,} failed={failed:,} recovered={recovered:,}  "
                          f"~{eta:.1f}h left")

                time.sleep(DELAY)

        except KeyboardInterrupt:
            print("\ninterrupted, progress is saved")

    print(f"\nscraped ok : {ok:,}")
    print(f"failed     : {failed:,}  (of these, {recovered:,} kept old data)")

    df = pd.read_csv(OUTPUT)
    print(f"\n{OUTPUT}: {len(df):,} rows")
    for col in ["page_text_raw", "description_raw", "gallery_ids",
                "agent_name", "built_in_year", "detail_location"]:
        if col in df.columns:
            print(f"  {col:<20} fill {df[col].notna().mean():.1%}")
    size_mb = os.path.getsize(OUTPUT) / 1e6
    print(f"\nfile size: {size_mb:,.0f} MB  "
          f"(gitignored; back this up off-machine)")