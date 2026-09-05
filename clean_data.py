"""Cleans and unions the scraped listings.

Produces one file with a `generation` column rather than two files, because
two files that must agree is the failure mode this project keeps hitting.

    generation = 'august'  seen only in the August scrape (delisted or unbumped)
    generation = 'fresh'   present in the current scrape

`COMPS` in main.py should filter to generation == 'fresh': a buyer can only
buy what is currently listed. Training uses everything, because listings that
vanished are the closest thing to a transaction signal in a market with no
sale-price registry.

Also writes listing_history.csv, which accumulates first_seen / last_seen per
listing across scrapes. Zameen's "Added: N ago" is a BUMP timestamp, not a
creation date (verified: 2,858 listings live in August report being under a
day old), so true listing age can only be built up from our own scrape dates.
"""
import re
from collections import Counter

import pandas as pd
import os
from location_parser import extract_area, extract_block
import sys
FRESH_ONLY = '--fresh-only' in sys.argv

# When the August scrape ran. Only used to seed listing_history for rows that
# predate scraped_at being captured. Adjust if the real date is known.
AUGUST_SCRAPE_DATE = "2026-08-05"

FRESH_FILES = [("listings_houses.csv", "House"), ("listings_flats.csv", "Flat")]
AUGUST_FILES = [("raw_backup/listings_houses_august.csv", "House"),
                ("raw_backup/listings_flats_august.csv", "Flat")]


def parse_price(price_text):
    if not price_text or not isinstance(price_text, str):
        return None
    price_text = price_text.replace(',', '')
    match = re.search(r"\d+\.?\d*", price_text)
    if not match:
        return None
    number = float(match.group())
    low = price_text.lower()
    if 'lakh' in low:
        number *= 100_000
    elif 'crore' in low:
        number *= 10_000_000
    elif 'arab' in low:
        number *= 1_000_000_000
    return number


def parse_size(size_text):
    if not size_text or not isinstance(size_text, str):
        return None
    size_text = size_text.replace(',', '')
    match = re.search(r"\d+\.?\d*", size_text)
    if not match:
        return None
    number = float(match.group())
    low = size_text.lower()
    if 'kanal' in low:
        number *= 20
    elif 'sqft' in low:
        number /= 272.25
    return number


def extract_listing_id(url):
    """'...-54571095-1619-1.html' -> '54571095'. None for project pages,
    which use a different URL shape and are not individual properties."""
    if not isinstance(url, str):
        return None
    m = re.search(r"-(\d+)-\d+-\d+\.html", url)
    return m.group(1) if m else None


def extract_title_features(title):
    if not title or not isinstance(title, str):
        return pd.Series([0, 0, 0, 0, 0, 0])
    t = title.lower()
    return pd.Series([
        int('new' in t or 'brand' in t),
        int('furnished' in t),
        int('luxury' in t or 'ultra' in t),
        int('basement' in t),
        int('corner' in t),
        int(bool(re.search(r'semi.?commercial|commercial house|commercial property'
                           r'|commercial use|commercial plot', t))),
    ])


FLOOR_WORDS = {
    'ground': 0, 'first': 1, 'second': 2, 'third': 3, 'fourth': 4,
    'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
}


def extract_floor(title):
    if not title or not isinstance(title, str):
        return None
    t = title.lower()
    match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', t)
    if match:
        return float(match.group(1))
    for word, num in FLOOR_WORDS.items():
        if f'{word} floor' in t:
            return float(num)
    return None


def load(files, generation):
    frames = []
    for path, ptype in files:
        try:
            d = pd.read_csv(path)
        except FileNotFoundError:
            print(f"  MISSING: {path}")
            continue
        if 'property_type' not in d.columns:
            d['property_type'] = ptype
        d['generation'] = generation
        frames.append(d)
        print(f"  {path}: {len(d):,}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


if __name__ == '__main__':

    # ---------------------------------------------------------------- load
    print("fresh:")
    fresh = load(FRESH_FILES, "fresh")
    if FRESH_ONLY:
        print("fresh-only mode: skipping the August union and the detail merge")
        august = pd.DataFrame(columns=fresh.columns)
    else:
        print("august:")
        august = load(AUGUST_FILES, "august")


    # The August scrape predates these columns. Deriving the id the same way
    # for both generations is what makes the union dedupable.
    for d in (fresh, august):
        d['listing_id'] = d['url'].apply(extract_listing_id)
    if 'scraped_at' not in august.columns:
        august['scraped_at'] = AUGUST_SCRAPE_DATE

    # `created_*` is time since last bump, not listing age. Renamed so the
    # column name does not imply something it cannot support.
    fresh = fresh.rename(columns={
        "created_text": "bumped_text", "created_days": "bumped_days",
        "created_date": "bumped_date",
    })

    # ------------------------------------------------------- project pages
    for name, d in (("fresh", fresh), ("august", august)):
        bad = d['listing_id'].isna()
        if bad.any():
            print(f"\ndropping {bad.sum()} non-property pages from {name} "
                  f"(project/development URLs)")
            print(d.loc[bad, 'url'].head(3).to_string())
    fresh = fresh[fresh['listing_id'].notna()].copy()
    august = august[august['listing_id'].notna()].copy()

    # ------------------------------------------------------------- history
    # Accumulates true age across scrapes. Useless today, valuable in three
    # months, and only if it starts now.
    hist_rows = []
    for gen, d in (("august", august), ("fresh", fresh)):
        seen = d.groupby('listing_id')['scraped_at'].min().reset_index()
        seen['generation'] = gen
        hist_rows.append(seen)
    hist = pd.concat(hist_rows, ignore_index=True)
    history = hist.groupby('listing_id').agg(
        first_seen=('scraped_at', 'min'),
        last_seen=('scraped_at', 'max'),
        times_seen=('scraped_at', 'size'),
    ).reset_index()

    # Merge with what we already have. Rebuilding from scratch would discard
    # every earlier scrape, and accumulated first_seen dates are the only way
    # to know a listing's true age, since Zameen's date is a bump timestamp.
    if os.path.exists('listing_history.csv'):
        prev = pd.read_csv('listing_history.csv', dtype={'listing_id': str})
        history['listing_id'] = history['listing_id'].astype(str)
        merged = pd.concat([prev, history], ignore_index=True)
        print(f"  merged with {len(prev):,} existing history rows")

    history.to_csv('listing_history.csv', index=False)
    print(f"\nlisting_history.csv: {len(history):,} listings, "
          f"{(history['times_seen'] > 1).sum():,} seen in both scrapes")

    # --------------------------------------------------------------- union
    fresh_ids = set(fresh['listing_id'])
    august_only = august[~august['listing_id'].isin(fresh_ids)].copy()
    print(f"\nunion: {len(fresh):,} fresh + {len(august_only):,} august-only "
          f"= {len(fresh) + len(august_only):,}")
    print(f"  ({len(august) - len(august_only):,} August listings still live, "
          f"fresh version kept for its current price)")

    df = pd.concat([fresh, august_only], ignore_index=True)

    # Same property relisted under a new id keeps both rows. Not solvable
    # here; see the duplicates note in PROJECT_CONTEXT.
    before = len(df)
    df = df.drop_duplicates(subset=['listing_id'], keep='first')
    if before != len(df):
        print(f"  dropped {before - len(df)} duplicate listing_ids")
    before = len(df)
    df = df.drop_duplicates(subset=['url'], keep='first')
    if before != len(df):
        print(f"  dropped {before - len(df)} duplicate urls")

    # -------------------------------------------------------- detail merge
    if FRESH_ONLY:
        # The model expects all 29 features, so the columns must exist even
        # when empty. train.py fills them with 0.
        from detail_parser import DESC_KEYWORDS

        for c in (['detail_location', 'description_length']
                  + ['desc_' + k for k in DESC_KEYWORDS]):
            if c not in df.columns:
                df[c] = None
        print("\nno detail features in fresh-only mode")
    else:
        details = pd.read_csv('detail_features.csv')
        # The new detail scrape only covered fresh URLs, so August-only listings
        # would lose the detail data they already had. Fill them from the old file.
        old_details = pd.read_csv('raw_backup/detail_features_august.csv')
        old_details = old_details[~old_details['url'].isin(set(details['url']))]
        print(f"detail rows: {len(details):,} new + {len(old_details):,} august-only")
        details = pd.concat([details, old_details], ignore_index=True)
        if '_error' in details.columns:
            details = details[details['_error'].isna()].drop(columns=['_error'])
        df = df.merge(details, on='url', how='left')
        print(f"\nafter detail merge: {df.shape}")
        fill = df.groupby('generation')['detail_location'].apply(lambda s: s.notna().mean())
        print("detail_location fill by generation:")
        print(fill.round(3).to_string())
        if fill.get('fresh', 1) < 0.5:
            print("  WARNING: most fresh listings have no detail data, so they have\n"
                  "  no block and a coarser location string. Run the detail scrape\n"
                  "  before using this file to serve.")

    # ---------------------------------------------------------- derive all
    df['price_numeric'] = df['price'].apply(parse_price)
    df['size_marla'] = df['size'].apply(parse_size)
    df['best_location'] = df['detail_location'].fillna(df['location'])
    df['area'] = df['best_location'].apply(extract_area)
    df['block'] = df['best_location'].apply(extract_block)
    df[['is_new', 'is_furnished', 'is_luxury',
        'has_basement', 'is_corner', 'is_commercial']] = df['title'].apply(extract_title_features)
    df['floor'] = df['title'].apply(extract_floor)

    area_counts = df['area'].value_counts()
    rare = area_counts[area_counts < 5].index
    print(f"\nareas: {len(area_counts)} distinct, {len(rare)} with <5 listings "
          f"collapsed to Other")
    df['area'] = df['area'].apply(lambda x: 'Other' if x in rare else x)
    print(f"KNOWN_AREAS will be {df['area'].nunique()} "
          f"(was 221 before this scrape)")

    # ------------------------------------------------ known bad rows
    # Found by inspection; each is a size or price that parses to nonsense.
    BAD_TITLE_PATTERNS = [
        ('NNEW DOUBLE STORY', None),
        ('Premium 1-Bed Apartment In Indigo Heights', None),
        ('Luxury 2 bed Room Apartment', 'Gulberg 3'),
    ]
    for pattern, loc in BAD_TITLE_PATTERNS:
        m = df['title'].str.contains(pattern, case=False, na=False)
        if loc:
            m &= df['best_location'].str.contains(loc, case=False, na=False)
        if m.any():
            print(f"dropping {m.sum()} row(s) matching {pattern!r}")
            df = df[~m]

    df = df.drop_duplicates()

    # ---------------------------------------------------------------- save
    # Kept out of the cleaned file to stay under Hugging Face's 10MB limit.
    # All of these live in detail_features.csv or the raw scrapes, and
    # nothing in main.py, train.py or precompute_deviations.py reads them.
    HEAVY = ['page_text_raw', 'description_raw', 'property_details_raw']
    drop = [c for c in HEAVY if c in df.columns]
    if drop:
        df = df.drop(columns=drop)
        print(f"dropped {len(drop)} columns not read downstream: {sum(df.memory_usage(deep=True))/1e6:.1f} MB")


    df.to_parquet('listings_cleaned.parquet', compression='zstd', index=False)
    print(f"\nSaved listings_cleaned.parquet: {len(df):,} rows, {df.shape[1]} cols")
    print(df['generation'].value_counts().to_string())
    print(df['property_type'].value_counts().to_string())
    print(f"with a block: {df['block'].notna().sum():,}")
    print(f"price parsed: {df['price_numeric'].notna().sum():,}   "
          f"size parsed: {df['size_marla'].notna().sum():,}")