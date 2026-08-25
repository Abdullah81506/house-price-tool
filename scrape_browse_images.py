"""
Fetches cover photos for the listings that browse mode shows (the flagged ones).
Resumable — re-run after any interruption. Adds an 'image' column to
listing_deviations.csv when done.
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time, os

HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY = 1.2
SAVE_EVERY = 50
CACHE = "listing_images.csv"

dev = pd.read_csv('listing_deviations.csv')

# browse only ever shows flagged, high-confidence listings
targets = dev[(dev['position'] != 'within') & (dev['confidence'] == 'high')]
urls = targets['url'].dropna().unique().tolist()
print(f"{len(urls):,} listings need a cover photo")

done = {}
if os.path.exists(CACHE):
    prev = pd.read_csv(CACHE)
    done = dict(zip(prev['url'], prev['image']))
    print(f"resuming: {len(done):,} already fetched")

todo = [u for u in urls if u not in done]
print(f"{len(todo):,} remaining (~{len(todo)*(DELAY+1.2)/60:.0f} min)\n")


def cover_photo(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=20).text
    except Exception:
        return None
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:image")
    return og["content"] if og and og.get("content") else None


try:
    for i, u in enumerate(todo, 1):
        done[u] = cover_photo(u)
        if i % SAVE_EVERY == 0:
            pd.DataFrame({"url": list(done), "image": list(done.values())}).to_csv(CACHE, index=False)
            print(f"  {i:,}/{len(todo):,}")
        time.sleep(DELAY)
except KeyboardInterrupt:
    print("\ninterrupted — saving")

pd.DataFrame({"url": list(done), "image": list(done.values())}).to_csv(CACHE, index=False)

# merge into the deviations file main.py reads
imgs = pd.read_csv(CACHE)
dev = dev.drop(columns=['image'], errors='ignore').merge(imgs, on='url', how='left')
dev.to_csv('listing_deviations.csv', index=False)

got = dev['image'].notna().sum()
print(f"\ndone — {got:,} of {len(dev):,} rows now have a photo")
print(f"(flagged listings with a photo: {dev[(dev['position']!='within') & (dev['confidence']=='high')]['image'].notna().sum():,})")