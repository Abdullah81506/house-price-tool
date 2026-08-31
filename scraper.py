"""Scrapes Zameen search result pages.

Persists everything the card shows. Derive features later, never here:
a field not written to disk cannot be recovered without another scrape.

Page cap is 649 for the Lahore houses URL (verified). Pages past that 404.
Default sort is recency, so page 1 is today's listings and the tail areas
surface deeper.
"""
import csv
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

FIELDNAMES = [
    # identity
    "listing_id", "url", "page", "property_type",
    # what the card shows
    "title", "location", "currency", "price", "beds", "baths", "size",
    # recency
    "created_text", "updated_text", "created_days", "updated_days",
    "created_date", "updated_date", "scraped_at",
    # media
    "cover_image",
]

# collects any date wording the parser does not recognise, printed at the end
UNPARSED_DATES = set()


def parse_relative_date(text, scraped_at):
    """'Added: 2 days ago' -> (2, '2026-08-27'). Returns (None, None) if unparsed.

    Zameen buckets coarsely past a week, so 'ago' in weeks or months is
    approximate. Fine for a 60-90 day filter, not for anything finer.
    """
    if not text:
        return None, None

    t = text.lower()
    t = re.sub(r"^\s*\(?\s*(added|updated)\s*:\s*", "", t)
    t = t.strip(" ()")

    if "just now" in t or "moment" in t:
        days = 0
    elif "today" in t:
        days = 0
    elif "yesterday" in t:
        days = 1
    else:
        m = re.search(r"(\d+)\s*(minute|hour|day|week|month|year)", t)
        if not m:
            UNPARSED_DATES.add(text)
            return None, None
        n, unit = int(m.group(1)), m.group(2)
        days = {
            "minute": 0, "hour": 0, "day": n,
            "week": n * 7, "month": n * 30, "year": n * 365,
        }[unit]
        if unit in ("minute", "hour"):
            days = 0

    date = (scraped_at - timedelta(days=days)).date().isoformat()
    return days, date


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


def scrape_page(page_url, max_retries=2):
    """Returns a list of listings, or None if the page never parsed cleanly.

    Returning None rather than the degraded list is the point: the previous
    version silently wrote bad rows after exhausting its retries.
    """
    for attempt in range(max_retries + 1):
        scraped_at = datetime.now()
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)
        except requests.RequestException as e:
            print(f"    attempt {attempt + 1}: {type(e).__name__}")
            time.sleep(3)
            continue

        if resp.status_code != 200:
            print(f"    attempt {attempt + 1}: status {resp.status_code}")
            if resp.status_code == 404:
                return None          # past the page cap, no point retrying
            time.sleep(3)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("li", attrs={"aria-label": "Listing"})
        if not cards:
            print(f"    attempt {attempt + 1}: no cards")
            time.sleep(3)
            continue

        listings = [parse_card(c, scraped_at) for c in cards]

        missing = sum(1 for l in listings if l["title"] is None)
        if missing / len(listings) > 0.5:
            print(f"    attempt {attempt + 1}: degraded "
                  f"({missing}/{len(listings)} titles missing)")
            time.sleep(3)
            continue

        return listings

    return None


def scrape_and_save(base_url, output_file, property_type, num_pages, start_page=1):
    failed = []
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        total = 0
        for page_num in range(start_page, num_pages + 1):
            page_url = base_url.format(page_num)
            listings = scrape_page(page_url)

            if listings is None:
                failed.append(page_num)
                print(f"page {page_num}: FAILED, nothing written")
                time.sleep(1.5)
                continue

            for l in listings:
                l["page"] = page_num
                l["property_type"] = property_type
            writer.writerows(listings)
            total += len(listings)
            print(f"page {page_num}: {len(listings)} listings (total {total})")
            time.sleep(1.5)

    print(f"\nDone. {total} listings written to {output_file}.")
    if failed:
        print(f"FAILED PAGES ({len(failed)}): {failed}")
        print("Rerun these before trusting the file as complete.")
    if UNPARSED_DATES:
        print(f"\nUnrecognised date wording ({len(UNPARSED_DATES)} distinct):")
        for d in sorted(UNPARSED_DATES)[:20]:
            print(f"  {d!r}")
        print("Add these to parse_relative_date before the full run.")


if __name__ == "__main__":

    # --- full run: uncomment once the test output has been inspected ---
    scrape_and_save("https://www.zameen.com/Houses_Property/Lahore-1-{}.html",
                    "listings_houses.csv", "House", num_pages=649)
    scrape_and_save("https://www.zameen.com/Flats_Apartments/Lahore-1-{}.html",
                    "listings_flats.csv", "Flat", num_pages=200)