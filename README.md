---
title: House Price Tool
emoji: 🏠
colorFrom: blue
colorTo: green
sdk: gradio
app_file: app.py
pinned: false
---

# Is this Lahore listing priced like its neighbours?

Paste a Zameen.com listing link and get back what similar-sized properties in the same
area are asking, where this listing sits in that range, and the five closest comparable
listings so you can check the number yourself.

**Live:** https://huggingface.co/spaces/Abdullah81506/house-price-tool

---

## Why this exists

Pakistan has no public record of property sale prices. Transactions are officially
recorded at DC/FBR valuation rates, which are deliberately below market for tax reasons,
and much of the market is cash. So the ground truth that Zillow's Zestimate is built on
simply does not exist here.

Zameen publishes an area-level price index — "1-Kanal houses in DHA Phase 7 average
X" — but nothing that judges a *specific* listing. This tool does that, and shows the
comparable listings behind every number so the verdict is checkable rather than
authoritative.

## What it does

- **Paste a link** — scrapes the listing, compares it to similar properties, gives a verdict
- **Enter details** — area, type, size, beds, baths; shows the typical range without a listing
- **Browse** — the listings currently asking most and least relative to their area

## How it works

```
scraper.py              → scrapes Zameen search pages (13,216 Lahore listings)
scrape_details_bulk.py  → scrapes each listing's detail page (amenities, description, location)
clean_data.py           → parses prices/sizes, extracts areas, joins the two sources
train.py                → trains XGBoost on log price, evaluates on novel-listing subset
precompute_deviations.py→ scores every listing against its comparables
main.py                 → FastAPI: /predict, /estimate, /listings, /areas
app.py                  → Gradio front end
```

**Data:** 13,203 cleaned listings (10,000 houses, 3,216 flats) across 221 Lahore areas.

**Model:** XGBoost regression on log-transformed price. 29 features — size, beds, baths,
area, property type, floor, six title keyword flags, and seventeen description-derived
features.

**Verdict logic:** a listing is flagged when its asking price falls outside the
15th–85th percentile of genuinely comparable listings (same area, same property type,
within ±30% size), plus a 5% margin. That threshold was chosen by measuring the flag
rate across 600 random listings — it flags ~18%, split evenly between over and under.

## What I measured

### The model is close to the ceiling for its features

I computed the error a *perfect* model would still make — one that always predicted each
comparable group's exact median price:

| | |
|---|---|
| Perfect model's median error | **9.1%** |
| This model's median error | **~10.5%** |

Within any (area, size, type) group, actual asking prices vary enormously — DHA Phase 7
houses of 14–26 marla range from 5.75 to 25 crore. That spread is driven by construction
quality, age, finishing and seller motivation, none of which are in the data. It is
unlearnable from these features, by any model.

### 79% of my test set was memorizable

A random train/test split badly overstated performance. Because only ~12 features are
used, many genuinely different properties collapse to identical feature vectors, so most
test rows had a near-twin in training:

| | with a twin | genuinely novel |
|---|---|---|
| share of test set | 79.3% | 20.7% |
| median % error | 9.6% | **16.2%** |
| more than 30% off | 9.8% | **25.4%** |

The novel-listing figures match what the tool actually does on fresh listings. Everything
below is judged on that subset, not the headline number.

### What helped, and what didn't

| Change | Effect on novel listings |
|---|---|
| Fixing a training/serving location mismatch | 61.6% → 28.0% error on one listing; the single largest fix |
| Training on log price instead of raw | −1.2 MAPE, better on 7/7 seeds |
| Description keyword features | −0.7 median error, better on 4/5 seeds |
| Correcting area-name parsing | no measurable change |
| Scraping detail-page amenities | **no measurable change** |

The amenities scrape took 11 hours and produced nothing. `built_in_year` — the feature I
expected most from — turned out to be near-constant: 76.8% of listings with the field are
2024 or later, so it duplicated an existing "is new" flag. Feature importance ranked it
at 0.006 against `size_marla` at 0.75.

I kept the scrape anyway: it produced the listing URLs, the granular locations that fixed
the vocabulary mismatch, and the description features that did help.

## Known limitations

- Trained on **asking** prices, not sale prices. It measures whether a listing is out of
  line with its neighbours, not what a property is worth.
- ~15% median error on novel listings, so it can only flag listings that are clearly off.
- Cannot see condition, construction quality or finishing. A brand-new house in an older
  phase looks overpriced when it may not be.
- Lahore only.
- Source data is agent-entered and messy: installment plans quoted as full prices,
  commercial units typed as flats, relisted duplicates, occasional price typos. These are
  filtered, imperfectly.

## Running it locally

```bash
pip install -r requirements.txt
python app.py            # Gradio UI on :7860
uvicorn main:app --reload  # or the FastAPI version on :8000
```

To rebuild from scratch: `scraper.py` → `scrape_details_bulk.py` → `clean_data.py` →
`train.py` → `precompute_deviations.py`.