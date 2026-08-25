"""Parses extra features from listing detail page."""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

BOOL_FEATURES = [
    "Double Glazed Windows", "Central Air Conditioning", "Central Heating",
    "Electricity Backup", "Waste Disposal", "Flooring", "Swimming Pool",
    "Lawn or Garden", "Service Elevators", "Security Staff",
]

NUM_FEATURES = ["Built in year", "Parking Spaces", "Floors",
                "Servant Quarters", "Store Rooms"]

# Descriptions are present on ~100% of listings and average ~788 chars,
# so these flags have no missing-data problem.
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


def parse_detail_page(url):
    """Return a dict of extra features from a Zameen detail page."""
    out = {}
    try:
        html = requests.get(url, headers=HEADERS, timeout=20).text
    except Exception as e:
        return {"_error": str(e)}

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" | ", strip=True)

    # --- granular location: SAME element main.py reads, so training and
    #     prediction share one vocabulary and cannot drift apart ---
    hdr = soup.find(attrs={"aria-label": "Property header"})
    out["detail_location"] = hdr.get_text(strip=True) if hdr else None

    # --- numeric amenities ("Label: N") ---
    for feat in NUM_FEATURES:
        m = re.search(re.escape(feat) + r"\s*\|?\s*:\s*\|?\s*(\d+)", page_text)
        out[feat.lower().replace(" ", "_")] = int(m.group(1)) if m else None

    # --- boolean amenities ---
    for feat in BOOL_FEATURES:
        out["has_" + feat.lower().replace(" ", "_")] = 1 if feat in page_text else 0

    # --- description ---
    desc_el = soup.find(attrs={"aria-label": "Property description"})
    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
    out["description_length"] = len(desc)

    d = desc.lower()
    for key, words in DESC_KEYWORDS.items():
        out["desc_" + key] = 1 if any(w in d for w in words) else 0

    return out


if __name__ == "__main__":
    test_url = ("https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal"
                "_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha"
                "_phase_7_100_original_deal-51524283-1450-1.html")
    for k, v in parse_detail_page(test_url).items():
        print(f"  {k:<28} {v}")