from fastapi import FastAPI
from pydantic import BaseModel
import xgboost as xgb
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from clean_data import parse_size, parse_price, extract_title_features, extract_floor
from location_parser import split_location
from detail_parser import DESC_KEYWORDS
from config import BAND_LO, BAND_HI, MARGIN, MIN_COMPS, MIN_BLOCK_COMPS, MIN_PRICE_RATIO

app = FastAPI()

headers = {"User-Agent": "Mozilla/5.0"}

model = xgb.XGBRegressor()
model.load_model('house_price_model.json')

# --- comparables data, loaded once at startup ---
PRICE_NOT_REAL = ['installment', 'instalment', 'booking', 'on easy', 'down payment']

_ALL = pd.read_csv('listings_cleaned.csv')

# Vocabulary comes from everything the model was trained on. Filtering this
# would shrink KNOWN_AREAS below the model's categories and silently send
# some areas to "Other".
KNOWN_AREAS = sorted(_ALL['area'].dropna().unique().tolist())
KNOWN_PROPERTY_TYPES = ['House', 'Flat']

COMPS = _ALL[
    _ALL['price_numeric'].notna()
    & _ALL['size_marla'].notna()
    & (_ALL['size_marla'] > 0)
]

# A buyer can only buy what is currently listed. August-only rows are
# delisted or unbumped, so they belong in training but not in comparables.
if 'generation' in COMPS.columns:
    _b = len(COMPS)
    COMPS = COMPS[COMPS['generation'] == 'fresh']
    print(f"excluded {_b - len(COMPS):,} listings not in the current scrape", flush=True)

_before = len(COMPS)
_title_low = COMPS['title'].astype(str).str.lower()
_installment = _title_low.apply(lambda t: any(w in t for w in PRICE_NOT_REAL))
COMPS = COMPS[~_installment & (COMPS['is_commercial'] != 1)]
print(f"excluded {_before - len(COMPS):,} installment/commercial listings", flush=True)

try:
    DEVIATIONS = pd.read_csv('listing_deviations.csv')
    print(f"loaded {len(DEVIATIONS):,} precomputed deviations", flush=True)
except FileNotFoundError:
    DEVIATIONS = pd.DataFrame()
    print("WARNING: listing_deviations.csv missing - run precompute_deviations.py", flush=True)

# --- areas that can actually return browse results ---
if DEVIATIONS.empty:
    BROWSE_AREAS = []
    BROWSE_AREAS_ABOVE = []
    BROWSE_AREAS_BELOW = []
else:
    _hc = DEVIATIONS[DEVIATIONS['confidence'] == 'high']
    BROWSE_AREAS_ABOVE = sorted(_hc[_hc['position'] == 'above']['area'].dropna().unique().tolist())
    BROWSE_AREAS_BELOW = sorted(_hc[_hc['position'] == 'below']['area'].dropna().unique().tolist())
    BROWSE_AREAS = sorted(set(BROWSE_AREAS_ABOVE) | set(BROWSE_AREAS_BELOW))
print(f"{len(BROWSE_AREAS)} areas have high-confidence flagged listings "
      f"({len(BROWSE_AREAS_ABOVE)} above, {len(BROWSE_AREAS_BELOW)} below)", flush=True)

print(f"loaded {len(COMPS):,} comparables across {len(KNOWN_AREAS)} areas", flush=True)


class ListingRequest(BaseModel):
    url: str


def safe_area(area_value):
    return area_value if area_value in KNOWN_AREAS else "Other"


def safe_property_type(value):
    return value if value in KNOWN_PROPERTY_TYPES else "House"

def is_installment(title):
    t = str(title or "").lower()
    return any(w in t for w in PRICE_NOT_REAL)

def scrape_single_listing(url):
    try:
        resp = requests.get(url, headers=headers, timeout=20)
    except requests.RequestException as e:
        return {"_error": f"Could not reach that page ({type(e).__name__})."}

    if resp.status_code != 200:
        return {"_error": f"Zameen returned status {resp.status_code} for that URL."}

    soup = BeautifulSoup(resp.text, "html.parser")
    og = soup.find("meta", property="og:image")
    image = og["content"] if og and og.get("content") else None

    ids = []
    for m in re.finditer(r'media\.zameen\.com/thumbnails/(\d+)-\d+x\d+\.jpe?g', resp.text):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    candidates = [f"https://media.zameen.com/thumbnails/{i}-800x600.jpeg" for i in ids[:10]]
    images = []
    for u in candidates:
        try:
            r = requests.head(u, headers=headers, timeout=5)
            if int(r.headers.get("Content-Length", 0)) > 10000:
                images.append(u)
        except requests.RequestException:
            pass

    def get_field(label):
        el = soup.find("span", attrs={"aria-label": label})
        return el.get_text(strip=True) if el else None

    title_h1 = soup.find("h1")
    title = title_h1.get_text(strip=True) if title_h1 else None

    price = get_field("Price")
    baths = get_field("Baths")
    beds = get_field("Beds")
    size = get_field("Area")
    property_type = get_field("Type")

    header_div = soup.find(attrs={"aria-label": "Property header"})
    location = header_div.get_text(strip=True) if header_div else None
    if not location:
        location_div = soup.find(attrs={"aria-label": "Location"})
        location = location_div.get_text(strip=True) if location_div else None

    desc_el = soup.find(attrs={"aria-label": "Property description"})
    description = desc_el.get_text(" ", strip=True) if desc_el else ""

    return {
        "title": title,
        "price": price,
        "beds": beds,
        "baths": baths,
        "size": size,
        "location": location,
        "property_type": property_type,
        "description": description,
        "image": image,
        "images": images,
    }


def parse_number(text):
    if not text:
        return None
    match = re.search(r"\d+\.?\d*", text)
    return float(match.group()) if match else None


def build_desc_features(description):
    """Same 17 text features the model was trained on."""
    text = description or ""
    feats = {"description_length": len(text)}
    low = text.lower()
    for key, words in DESC_KEYWORDS.items():
        feats["desc_" + key] = 1 if any(w in low for w in words) else 0
    return feats

def get_comparables(area, property_type, size_marla, min_comps=MIN_COMPS, block=None, url=None):
    """Actual listings of similar size, in the same area and of the same type.
    If block is given and the block pool is large enough, comparables are
    narrowed to that block. Otherwise falls back to area level."""
    if size_marla is None or area == "Other":
        return None
    lo, hi = size_marla * 0.7, size_marla * 1.3
    c = COMPS[
        (COMPS['area'] == area)
        & (COMPS['property_type'] == property_type)
        & (COMPS['size_marla'] >= lo)
        & (COMPS['size_marla'] <= hi)
    ]
    if url:
        c = c[c['url'] != url]

    scope = "area"
    if block:
        b = c[c['block'] == block]
        if len(b) >= MIN_BLOCK_COMPS:
            c = b
            scope = "block"

    if len(c) >= 20:
        ppm = c['price_numeric'] / c['size_marla']
        lo_ppm, hi_ppm = ppm.quantile(0.02), ppm.quantile(0.98)
        c = c[(ppm >= lo_ppm) & (ppm <= hi_ppm)]
    if len(c) < min_comps:
        return None
    p = c['price_numeric']

    # examples come from the block whenever one exists, even at area scope
    ex_pool = c
    if block and scope == "area":
        in_block = c[c['block'] == block]
        if len(in_block) > 0:
            ex_pool = in_block

    nearest = ex_pool.reindex(
        (ex_pool['size_marla'] - size_marla).abs().sort_values().index
    ).head(5)
    return {
        "count": int(len(c)),
        "scope": scope,
        "block": block if scope == "block" else None,
        "low": float(p.quantile(BAND_LO)),
        "typical": float(p.median()),
        "high": float(p.quantile(BAND_HI)),
        "min": float(p.min()),
        "max": float(p.max()),
        "size_range_marla": [round(lo, 1), round(hi, 1)],
        "examples": [
            {"title": r['title'], "url": r['url'],
             "price": float(r['price_numeric']), "size_marla": round(float(r['size_marla']), 1)}
            for _, r in nearest.iterrows()
        ],
    }

@app.post("/predict")
def predict_price(request: ListingRequest):
    raw = scrape_single_listing(request.url)

    if raw.get("_error"):
        return {"error": raw["_error"]}

    if not raw["price"] and not raw["title"]:
        return {"error": "Could not read this listing. It may have been removed, "
                         "or the URL may not be a Zameen property page."}

    print(raw, flush=True)

    asking_price = parse_price(raw["price"])
    size_marla = parse_size(raw["size"])
    beds = parse_number(raw["beds"])
    baths = parse_number(raw["baths"])
    raw_area, block = split_location(raw["location"])
    area = safe_area(raw_area)
    property_type = safe_property_type(raw["property_type"])
    floor = extract_floor(raw["title"])
    title_features = extract_title_features(raw["title"])
    if asking_price is None or size_marla is None:
        return {"error": "That page doesn't look like a property listing — "
                         "it may be a project or development page. Try a link "
                         "to a specific property."}

    if is_installment(raw["title"]):
        return {"error": "This listing quotes an installment or booking plan rather "
                         "than an outright sale price, so it can't be compared "
                         "against the sale listings in this dataset."}

    row = pd.DataFrame([{
        "size_marla": size_marla,
        "beds": beds,
        "baths": baths,
        "area": area,
        "property_type": property_type,
        "floor": floor,
        "is_new": title_features[0],
        "is_furnished": title_features[1],
        "is_luxury": title_features[2],
        "has_basement": title_features[3],
        "is_corner": title_features[4],
        "is_commercial": title_features[5],
        **build_desc_features(raw.get("description")),
    }])
    row["area"] = pd.Categorical(row["area"], categories=KNOWN_AREAS)
    row["property_type"] = pd.Categorical(row["property_type"], categories=KNOWN_PROPERTY_TYPES)
    row["floor"] = pd.to_numeric(row["floor"], errors="coerce")
    for c in ["size_marla", "beds", "baths"]:
        row[c] = pd.to_numeric(row[c], errors="coerce")

    predicted_price = float(np.expm1(model.predict(row)[0]))

    # --- comparables and verdict ---
    comps = get_comparables(area, property_type, size_marla, block=block, url=request.url)
    implausible = bool(
        comps and asking_price and comps["typical"]
        and asking_price / comps["typical"] < MIN_PRICE_RATIO
    )

    if comps is None:
        verdict = "Not enough comparable listings to judge this one."
        confidence = "none"
        position = None
    elif asking_price is None:
        verdict = "Could not read the asking price."
        confidence = "none"
        position = None
    else:
        if asking_price < comps["low"] * (1 - MARGIN):
            verdict = "Below the typical range for this area and size."
            position = "below"
        elif asking_price > comps["high"] * (1 + MARGIN):
            verdict = "Above the typical range for this area and size."
            position = "above"
        else:
            verdict = "In line with comparable listings."
            position = "within"
        confidence = "high" if comps["count"] >= 20 else "low"

    return {
        "url": request.url,
        "title": raw["title"],
        "image": raw.get("image"),
        "images": raw.get("images", []),
        "area": area,
        "property_type": property_type,
        "size_marla": size_marla,
        "asking_price": asking_price,
        "predicted_price": predicted_price,
        "comparables": comps,
        "verdict": verdict,
        "position": position,
        "confidence": confidence,
        "scraped_raw": raw,
        "block": block,
        "implausible": implausible,
    }


@app.get("/areas")
def list_areas():
    """Areas that have enough data to browse, with listing counts."""
    if DEVIATIONS.empty:
        return {"areas": []}
    counts = DEVIATIONS['area'].value_counts()
    return {"areas": [{"name": a, "count": int(n)} for a, n in counts.items()]}


@app.get("/listings")
def browse_listings(
        position: str = "above",  # above | below | within
        area: str = None,
        property_type: str = None,
        confidence: str = "high",  # high | any
        limit: int = 20,
):
    """Listings sorted by how far they sit outside the typical range."""
    if DEVIATIONS.empty:
        return {"error": "No precomputed data. Run precompute_deviations.py first."}

    d = DEVIATIONS
    if position in ("above", "below", "within"):
        d = d[d['position'] == position]
    if area:
        d = d[d['area'] == area]
    if property_type:
        d = d[d['property_type'] == property_type]
    if confidence == "high":
        d = d[d['confidence'] == "high"]

    d = d.sort_values('deviation', ascending=False).head(min(limit, 100))

    records = d.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if isinstance(v, float) and np.isnan(v):
                r[k] = None

    return {
        "count": int(len(d)),
        "filters": {"position": position, "area": area,
                    "property_type": property_type, "confidence": confidence},
        "listings": records,
    }


class EstimateRequest(BaseModel):
    area: str
    property_type: str
    size_marla: float
    beds: float | None = None
    baths: float | None = None


@app.post("/estimate")
def estimate_price(req: EstimateRequest):
    area = safe_area(req.area)
    property_type = safe_property_type(req.property_type)

    if area == "Other":
        return {"error": f"No data for that area. Pick one from the list."}
    if not req.size_marla or req.size_marla <= 0:
        return {"error": "Enter a size in marla."}

    # no listing text available, so the description features are all zero
    desc_feats = {"description_length": 0}
    for key in DESC_KEYWORDS:
        desc_feats["desc_" + key] = 0

    row = pd.DataFrame([{
        "size_marla": req.size_marla,
        "beds": req.beds,
        "baths": req.baths,
        "area": area,
        "property_type": property_type,
        "floor": None,
        "is_new": 0, "is_furnished": 0, "is_luxury": 0,
        "has_basement": 0, "is_corner": 0, "is_commercial": 0,
        **desc_feats,
    }])
    row["area"] = pd.Categorical(row["area"], categories=KNOWN_AREAS)
    row["property_type"] = pd.Categorical(row["property_type"], categories=KNOWN_PROPERTY_TYPES)
    row["floor"] = pd.to_numeric(row["floor"], errors="coerce")
    row["beds"] = pd.to_numeric(row["beds"], errors="coerce")
    row["baths"] = pd.to_numeric(row["baths"], errors="coerce")

    predicted_price = float(np.expm1(model.predict(row)[0]))
    comps = get_comparables(area, property_type, req.size_marla)

    if comps is None:
        verdict = "Not enough comparable listings to judge this one."
        confidence = "none"
    else:
        verdict = f"{comps['count']} comparable listings found."
        confidence = "high" if comps["count"] >= 20 else "low"

    return {
        "area": area,
        "property_type": property_type,
        "size_marla": req.size_marla,
        "asking_price": None,
        "predicted_price": predicted_price,
        "comparables": comps,
        "verdict": verdict,
        "position": None,
        "confidence": confidence,
    }



