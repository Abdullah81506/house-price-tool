"""Parses extra features from a Zameen listing detail page.

Persists raw text alongside derived features. The previous version computed
17 features from the description and never wrote the description, which
permanently blocked full-vocabulary text modelling on 13,000 listings.
Do not remove the *_raw fields to save space.

Note on amenities: the amenity block has no aria-label wrapper, so there is
no clean selector for it. BOOL_FEATURES and NUM_FEATURES therefore match
against the whole page text, which is crude but has been verified to produce
real per-listing variation (fill rates 0.13 to 0.80, not constants).
page_text_raw preserves the source those matches run against, so a better
amenity parser can be written later without another scrape.
"""
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

BOOL_FEATURES = [
    "Double Glazed Windows", "Central Air Conditioning", "Central Heating",
    "Electricity Backup", "Waste Disposal", "Flooring", "Swimming Pool",
    "Lawn or Garden", "Service Elevators", "Security Staff",
]

NUM_FEATURES = ["Built in year", "Parking Spaces", "Floors",
                "Servant Quarters", "Store Rooms"]

DESC_KEYWORDS = {
    "marble": ["marble"],
    "imported": ["imported"],
    "solar": ["solar"],
    "renovated": ["renovat"],
    "grey_structure": ["grey structure", "gray structure"],
    "tiles": ["tile"],
    "basement": ["basement"],
    "servant": ["servant"],
    "lift": ["lift", "elevator"],
    "park_facing": ["park facing", "facing park"],
    "corner": ["corner"],
    "main_boulevard": ["main boulevard", "boulevard"],
    "gated": ["gated"],
    "investor_rate": ["investor rate", "invester rate"],
    "urgent": ["urgent"],
    "negotiable": ["negotiable"],
}

GALLERY_RE = re.compile(r"media\.zameen\.com/thumbnails/(\d+)-\d+x\d+\.jpe?g")

AGENT_LABELS = ["Agency name", "Agent name", "Seller name", "Agency"]


def field_from_details(details_text, label):
    """'Type | House | Purpose | For Sale | ...' -> value after the label."""
    if not details_text:
        return None
    parts = [p.strip() for p in details_text.split("|")]
    for i, p in enumerate(parts[:-1]):
        if p.lower() == label.lower():
            return parts[i + 1]
    return None


def parse_detail_page(url):
    """Return a dict of extra features plus the raw text they came from."""
    out = {"detail_scraped_at": datetime.now().isoformat(timespec="seconds")}
    try:
        html = requests.get(url, headers=HEADERS, timeout=45).text
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" | ", strip=True)

    # --- everything the page shows, so nothing needs a second scrape ---
    out["page_text_raw"] = page_text

    # --- granular location: SAME element main.py reads, so training and
    #     prediction share one vocabulary and cannot drift apart ---
    hdr = soup.find(attrs={"aria-label": "Property header"})
    out["detail_location"] = hdr.get_text(strip=True) if hdr else None

    # --- structured summary block: purpose, and a date cross-check
    #     against the search card ---
    det = soup.find(attrs={"aria-label": "Property details"})
    details_text = det.get_text(" | ", strip=True) if det else None
    out["property_details_raw"] = details_text
    out["purpose"] = field_from_details(details_text, "Purpose")
    out["detail_added_text"] = field_from_details(details_text, "Added")

    # --- raw description, the field whose absence blocked TF-IDF ---
    desc_el = soup.find(attrs={"aria-label": "Property description"})
    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
    out["description_raw"] = desc
    out["description_length"] = len(desc)

    d = desc.lower()
    for key, words in DESC_KEYWORDS.items():
        out["desc_" + key] = 1 if any(w in d for w in words) else 0

    # --- numeric amenities ("Label: N"), absent when the agent left the
    #     amenity section blank. ~77% fill rate historically. ---
    for feat in NUM_FEATURES:
        m = re.search(re.escape(feat) + r"\s*\|?\s*:\s*\|?\s*(\d+)", page_text)
        out[feat.lower().replace(" ", "_")] = int(m.group(1)) if m else None

    # --- boolean amenities. NOTE: has_swimming_pool is contaminated, the
    #     phrase also appears in marketing copy. The others were checked and
    #     do not appear in descriptions. ---
    for feat in BOOL_FEATURES:
        out["has_" + feat.lower().replace(" ", "_")] = 1 if feat in page_text else 0

    # --- gallery: capture now, or pay another long scrape for photo work ---
    ids = []
    for m in GALLERY_RE.finditer(html):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    out["gallery_ids"] = ",".join(ids)
    out["gallery_count"] = len(ids)

    # --- agent and agency: dedup signal, and analysis. Do NOT use as a model
    #     feature without thought: learning "this agency overprices" would make
    #     the model predict higher for them, agreeing with the overpricing
    #     rather than flagging it. ---
    agent = None
    for lbl in AGENT_LABELS:
        el = soup.find(attrs={"aria-label": lbl})
        if el:
            agent = el.get_text(strip=True)
            out["_agent_label_used"] = lbl
            break
    out["agent_name"] = agent

    return out


if __name__ == "__main__":
    test_urls = [
        # no amenity section (numerics should be None)
        "https://www.zameen.com/Property/dha_phase_6_dha_phase_6_-_block_k_a_20_marla"
        "_house_has_landed_on_market_in_dha_phase_6_-_block_k_of_lahore"
        "-54571095-1619-1.html",
        # has amenity section (numerics should populate)
        "https://www.zameen.com/Property/dha_phase_6_dha_phase_6_-_block_k_live_the"
        "_luxury_you_deserve_luxury_living_in_the_heart_of_lahore_house_for_sale"
        "-53794833-1619-1.html",
    ]
    RAW = ("page_text_raw", "description_raw", "gallery_ids", "property_details_raw")
    for u in test_urls:
        print("=" * 70)
        for k, v in parse_detail_page(u).items():
            if k in RAW:
                s = str(v)
                print(f"  {k:<28} len={len(s):<6} {s[:60]!r}")
            else:
                print(f"  {k:<28} {v}")