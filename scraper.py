"""Scrapes Zameen search result pages.

Persists everything the card shows. Derive features later, never here:
a field not written to disk cannot be recovered without another scrape.

PAGINATION CAP. A single Lahore houses URL stops at page 649, which is 16,225
of the 23,212 houses Zameen reports. The result set is ordered by bump date, so
the ~7,000 unreachable listings are the ones agents have not refreshed recently,
which correlates with slower-moving areas (Bedian Road shows 260 properties on
Zameen and only 6 reached the old scrape).

The fix is price bands. They are non-overlapping by construction, each sits well
under the cap, and they need no reasoning about Zameen's nested locations
(DHA Defence contains DHA Phase 6 contains Block K). Verified band sizes:

    under 1.5cr   2,358      1.5 to 3cr    7,354
    3 to 6cr      6,456      6 to 12cr     5,190
    over 12cr     2,593                    total 23,951

The total slightly exceeds Zameen's 23,212 because listings priced on a boundary
appear in two bands. clean_data.py dedups on listing_id, so that is handled.
A price changing mid-run can also duplicate or miss a listing; both are rare and
the dedup covers the first. Do not scrape bands in parallel, since that widens
the window for it.

Flats need no banding: 3,172 scraped against 3,171 reported, already complete.
"""
import csv
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

HOUSES_URL = "https://www.zameen.com/Houses_Property/Lahore-1-{page}.html"
FLATS_URL = "https://www.zameen.com/Flats_Apartments/Lahore-1-{page}.html"

# (min, max) in rupees. max=None means no upper bound.
PRICE_BANDS = [
    (0, 15_000_000),
    (15_000_000, 30_000_000),
    (30_000_000, 60_000_000),
    (60_000_000, 120_000_000),
    (120_000_000, None),
]

MAX_PAGES = 649          # hard cap; bands should stop well before this
DELAY = 1.5

FIELDNAMES = [
    "listing_id", "url", "page", "property_type", "price_band",
    "title", "location", "currency", "price", "beds", "baths", "size",
    "created_text", "updated_text", "created_days", "updated_days",
    "created_date", "updated_date", "scraped_at",
    "cover_image",
]

UNPARSED_DATES = set()


def parse_relative_date(text, scraped_at):
    """'Added: 2 days ago' -> (2, '2026-08-27'). Returns (None, None) if unparsed.

    NOTE: this is a BUMP timestamp, not a creation date. Zameen resets it when
    an agent refreshes a listing. Verified: 2,858 listings demonstrably live
    3-4 weeks earlier reported being under a day old. Do not read it as age.
    """
    if not text:
        return None, None

    t = re.sub(r"^\s*\(?\s*(added|updated)\s*:\s*", "", text.lower()).strip(" ()")

    if "just now" in t or "moment" in t or "today" in t:
        days = 0
    elif "yesterday" in t:
        days = 1
    else:
        m = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)", t)
        if not m:
            UNPARSED_DATES.add(text)
            return None, None
        n, unit = int(m.group(1)), m.group(2)
        days = {"minute": 0, "hour": 0, "day": n,
                "week": n * 7, "month": n * 30, "year": n * 365}[unit]

    return days, (scraped_at - timedelta(days=days)).date().isoformat()


def extract_listing_id(url):
    """'...-54571095-1619-1.html' -> '54571095'. Stable key; slugs vary."""
    if not url:
        return None
    m = re.search(r"-(\d+)-\d+-\d+\.html", url)
    return m.group(1) if m else None


def parse_card(card, scraped_at):
    def label(name, tag=None):
        el = card.find(tag, attrs={"aria-label": name}) if tag \
            else card.find(attrs={"aria-label": name})
        return el.get_text(strip=True) if el else None

    link = card.find("a", href=True)
    url = link["href"] if link else None
    if url and url.startswith("/"):
        url = "https://www.zameen.com" + url

    # Cards past the first few lazy-load, putting the real URL in data-src
    # while src holds a placeholder. Reading src alone caught 80 of 500.
    img = card.find("img", attrs={"aria-label": "Listing photo"})
    cover = (img.get("src") or img.get("data-src")) if img else None

    created_text = label("Listing creation date")
    updated_text = label("Listing updated date")
    created_days, created_date = parse_relative_date(created_text, scraped_at)
    updated_days, updated_date = parse_relative_date(updated_text, scraped_at)

    return {
        "listing_id": extract_listing_id(url),
        "url": url,
        "title": label("Title", "h2"),
        "location": label("Location", "div"),
        "currency": label("Currency", "span"),
        "price": label("Price", "span"),
        "beds": label("Beds", "span"),
        "baths": label("Baths", "span"),
        "size": label("Area", "span"),
        "created_text": created_text,
        "updated_text": updated_text,
        "created_days": created_days,
        "updated_days": updated_days,
        "created_date": created_date,
        "updated_date": updated_date,
        "scraped_at": scraped_at.isoformat(timespec="seconds"),
        "cover_image": cover,
    }


def build_url(template, page, band=None):
    url = template.format(page=page)
    if band:
        lo, hi = band
        url += f"?price_min={lo}"
        if hi is not None:
            url += f"&price_max={hi}"
    return url


def scrape_page(page_url, max_retries=2):
    """Returns a list of listings, None past the end of the result set, or
    None after exhausting retries.

    Returning None rather than the degraded list matters: the previous version
    wrote bad rows silently once its retries ran out.
    """
    for attempt in range(max_retries + 1):
        scraped_at = datetime.now()
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"    attempt {attempt + 1}: {type(e).__name__}")
            time.sleep(3)
            continue

        if resp.status_code == 404:
            return None                      # past the end of this band
        if resp.status_code != 200:
            print(f"    attempt {attempt + 1}: status {resp.status_code}")
            time.sleep(3)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("li", attrs={"aria-label": "Listing"})
        if not cards:
            return None                      # empty page, end of the band

        listings = [parse_card(c, scraped_at) for c in cards]
        missing = sum(1 for l in listings if l["title"] is None)
        if missing / len(listings) > 0.5:
            print(f"    attempt {attempt + 1}: degraded "
                  f"({missing}/{len(listings)} titles missing)")
            time.sleep(3)
            continue

        return listings

    return None


def scrape_bands(template, property_type, bands, writer):
    """Walks each band until a page returns nothing. Returns (total, failures)."""
    total, failed = 0, []
    for band in bands:
        lo, hi = band if band else (None, None)
        label = "all" if band is None else \
            f"{lo/1e7:.1f}cr-{'inf' if hi is None else f'{hi/1e7:.1f}cr'}"
        print(f"\n--- {property_type}, band {label} ---")
        band_total = 0

        for page in range(1, MAX_PAGES + 1):
            listings = scrape_page(build_url(template, page, band))
            if listings is None:
                # Distinguish the end of the band from a genuine failure by
                # retrying once; a real 404 returns None again immediately.
                retry = scrape_page(build_url(template, page, band), max_retries=0)
                if retry is None:
                    print(f"  ends at page {page - 1}, {band_total} listings")
                    break
                listings = retry

            for l in listings:
                l["page"] = page
                l["property_type"] = property_type
                l["price_band"] = label
            writer.writerows(listings)
            band_total += len(listings)
            total += len(listings)

            if page % 25 == 0:
                print(f"  page {page}: {band_total} in band, {total} overall")
            time.sleep(DELAY)
        else:
            print(f"  WARNING: band {label} hit the {MAX_PAGES}-page cap. "
                  f"Split it further or listings are being missed.")
            failed.append(label)

    return total, failed


def run(output_file, template, property_type, bands):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        total, failed = scrape_bands(template, property_type, bands, writer)

    print(f"\n{total:,} {property_type} listings written to {output_file}")
    if failed:
        print(f"BANDS THAT HIT THE CAP: {failed}")
    if UNPARSED_DATES:
        print(f"\nUnrecognised date wording ({len(UNPARSED_DATES)} distinct):")
        for d in sorted(UNPARSED_DATES)[:20]:
            print(f"  {d!r}")


if __name__ == "__main__":
    run("listings_houses.csv", HOUSES_URL, "House", PRICE_BANDS)
    run("listings_flats.csv", FLATS_URL, "Flat", [None])
