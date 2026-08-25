# import requests
# from bs4 import BeautifulSoup
# import re
#
# import pandas as pd
# df = pd.read_csv('listings_cleaned.csv')
# print(sorted(df['area'].unique()))
#
# headers = {"User-Agent": "Mozilla/5.0"}
#
# def scrape_single_listing(url):
#     resp = requests.get(url, headers=headers)
#     soup = BeautifulSoup(resp.text, "html.parser")
#
#     def get_field(label):
#         el = soup.find("span", attrs={"aria-label": label})
#         return el.get_text(strip=True) if el else None
#
#     title_h1 = soup.find("h1")
#     title = title_h1.get_text(strip=True) if title_h1 else None
#
#     price = get_field("Price")
#     baths = get_field("Baths")
#     beds = get_field("Beds")
#     size = get_field("Area")
#
#     location_div = soup.find(attrs={"aria-label": "Location"})
#     location = location_div.get_text(strip=True) if location_div else None
#
#     return {
#         "title": title,
#         "price": price,
#         "beds": beds,
#         "baths": baths,
#         "size": size,
#         "location": location,
#     }
#
# def parse_number(text):
#     if not text:
#         return None
#     match = re.search(r"\d+\.?\d*", text)
#     return float(match.group()) if match else None
#
# result = scrape_single_listing("https://www.zameen.com/Property/dha_defence_defence_raya_brand_new_fully_furnished_2_bed_maid_room_golf_facing_apartment_terrace_view_defence_raya_lahore-54602693-8172-1.html")
# print(result)
#
# beds_clean = parse_number(result['beds'])
# baths_clean = parse_number(result['baths'])
# print("beds:", beds_clean, "baths:", baths_clean)
# import pandas as pd
# from clean_data import extract_area
# df = pd.read_csv('listings_cleaned.csv')
#
# print((df['location'].str.contains('DHA', case=False, na=False) &
#        ~df['location'].str.contains('-', na=False)).sum())
# mask = df['location'].str.contains('DHA', case=False, na=False) & ~df['location'].str.contains('-', na=False)
# # print(df.loc[mask, 'location'].value_counts().head(20))
# sample_areas = df.loc[mask, 'location'].apply(extract_area)
# print(sample_areas.value_counts().head(20))
# print(df['area'].nunique())
# print(len(KNOWN_AREAS))
# import pandas as pd
# df = pd.read_csv('listings.csv')
# print(df['size'].str.extract(r'([A-Za-z.]+)$')[0].value_counts())
# import pandas as pd
# df = pd.read_csv('listings.csv')
# df['property_type'] = 'House'
# df.to_csv('listings_houses.csv', index=False)
import pandas as pd
# df_flats = pd.read_csv('listings_flats.csv')
# print(df_flats.shape)
# print(df_flats.isnull().sum())
# print(df_flats['size'].str.extract(r'([A-Za-z.]+)$')[0].value_counts())
# df_houses = pd.read_csv('listings_houses.csv')
# df_flats = pd.read_csv('listings_flats.csv')
# df = pd.concat([df_houses, df_flats], ignore_index=True)
# df_check = pd.read_csv('listings_cleaned.csv')
pd.set_option('display.max_columns', None)
# print(df_check[df_check['property_type'] == 'Flat'].nlargest(10, 'size_marla')[['title', 'size', 'size_marla']])
# print(df_check[df_check['property_type'] == 'Flat']['size_marla'].describe())
# suspect_flat = df_check[df_check['title'].str.contains('Indigo Heights', case=False, na=False)]
# print(suspect_flat[['title', 'size', 'price']])
# df_check = pd.read_csv('listings_cleaned.csv')
# flats = df_check[df_check['property_type'] == 'Flat']
# print(flats.nsmallest(10, 'size_marla')[['title', 'size', 'size_marla']])
# suspect2_flat = df_check[df_check['title'].str.contains('Luxury 2 bed Room Apartment', case=False, na=False)]
# print(suspect2_flat[['title', 'location', 'size', 'price']])
# print(df_check[df_check['title'].str.contains('6 Beds Luxurious Apartment', case=False, na=False)][['title', 'location', 'price', 'size']])
# df = pd.read_csv('listings_cleaned.csv')
# flats = df[df['property_type'] == 'Flat']
# print(flats[flats['title'].str.contains('floor', case=False, na=False)]['title'].sample(15).tolist())
# print(flats['title'].str.contains('floor', case=False, na=False).sum(), "out of", len(flats))
# print(df[(df['property_type'] == 'House') & (df['floor'].notnull())][['title', 'floor']])
# flats = df[df['property_type'] == 'Flat']
# has_floor_word = flats['title'].str.contains('floor', case=False, na=False)
# has_floor_extracted = flats['floor'].notnull()
#
# print("Contains 'floor' word:", has_floor_word.sum())
# print("Extracted a floor number:", has_floor_extracted.sum())

# titles that contain "floor" but where extraction still failed
# mismatch = flats[has_floor_word & ~has_floor_extracted]
# print(mismatch['title'].tolist())
# print(df.duplicated().sum())
# dupes = df[df.duplicated(keep=False)].sort_values('title')
# print(dupes[['title', 'location', 'price']].head(20))
# df = pd.read_csv('listings_cleaned.csv')
# print(sorted(df['area'].unique()))
# print(len(df['area'].unique()))
# import requests
# from bs4 import BeautifulSoup
# headers = {"User-Agent": "Mozilla/5.0"}
# url = r'https://www.zameen.com/Property/dha_defence_defence_raya_fully_furnished_dha_raya_apartment_2_bedrooms_ground_floor_semi_golf_view-54184254-8172-1.html'
# resp = requests.get(url, headers=headers)
# soup = BeautifulSoup(resp.text, "html.parser")
# type_el = soup.find("span", attrs={"aria-label": "Type"})
# print(type_el.get_text(strip=True) if type_el else "not found")
#
# df = pd.read_csv('listings_cleaned.csv')
# flats = df[df['property_type'] == 'Flat']
# print(flats['price_numeric'].describe())
# print((flats['price_numeric'] > 80_000_000).sum())
# df = pd.read_csv('listings_cleaned.csv')
# print(((df['size_marla'] >= 20) & (df['beds'] >= 5)).sum())
# import pandas as pd
#
# df = pd.read_csv("listings_cleaned.csv")
#
# # ---- PART A: does KNOWN_AREAS match what's actually in the training data? ----
# # Paste your current KNOWN_AREAS list from main.py here:
# KNOWN_AREAS = [
#     'AWT Phase 2', 'Abdalians Cooperative Housing Society', 'Air Avenue Luxury Apartments',
#     'Airline Housing Society', 'Al', 'Al Hafeez Garden', 'Al Hafeez Gardens', 'Al Haram Garden',
#     'Al Jalil Garden', 'Al Noor Park Housing Society', 'Al Rehman Garden Phase 2',
#     'Al Rehman Garden Phase 4', 'Al Rehman Phase 2', 'Ali Park', 'Ali Town', 'Allama Iqbal Town',
#     'Architects Engineers Housing Society', 'Askari 1', 'Askari 10', 'Askari 11', 'Askari 12',
#     'Askari 2', 'Askari 5', 'Audit & Accounts Phase 1', 'Awami Villas', 'BOR',
#     'Bahria Homes, Bahria Town', 'Bahria Nasheman', 'Bahria Orchard', 'Bahria Orchard Phase 1',
#     'Bahria Orchard Phase 2', 'Bahria Orchard Phase 4', 'Bahria Town', 'Bankers Avenue',
#     'Bankers Avenue Cooperative Housing Society', 'Beacon House Society', 'Bedian Road',
#     'Bismillah Housing Scheme', 'CBD Punjab (PCBDDA)', 'Canal Bank Housing Scheme', 'Canal Garden',
#     'Canal Valley', 'Cantt', 'Cavalry Extension', 'Cavalry Ground', 'Central Park',
#     'Central Park Housing Scheme', 'Chinar Bagh', 'Chungi Amar Sadhu', 'DHA 11 Rahbar',
#     'DHA 11 Rahbar Sector 1', 'DHA 11 Rahbar Sector 2', 'DHA 11 Rahbar Sector 2 Extension',
#     'DHA 9 Town', 'DHA Phase 1', 'DHA Phase 2', 'DHA Phase 3', 'DHA Phase 4', 'DHA Phase 5',
#     'DHA Phase 6', 'DHA Phase 7', 'DHA Phase 8', 'DHA Phase\xa06', 'Defence Raya',
#     'Defence View Apartments', 'Divine Gardens', 'Dream Gardens', 'Dream Gardens Phase 1',
#     'Dream Gardens Phase 2', 'Dream Housing Society', 'EME Society', 'Eden Boulevard Housing Scheme',
#     'Eden City', 'Eden Lane Villas 2', 'Eden Residencia', 'Edenabad', 'Etihad Town',
#     'Etihad Town Phase 1', 'Faisal Town', 'Fateh Garh', 'Fazaia Housing Scheme Phase 1',
#     'Ferozepur Road', 'Formanites Housing Scheme', 'Formanities Housing Scheme', 'Gajju Matah',
#     'Garden Town', 'Ghous Garden', 'Goldcrest Mall & Residency', 'Golf View Residencia',
#     'Green Cap Housing Society', 'Green City', 'Gulberg', 'Gulberg 2', 'Gulberg 3', 'Gulshan',
#     'Hamza Town Phase 2', 'High Court Society', 'Hyde Park', 'IEP Engineers Town', 'Ichhra',
#     'Icon Valley Phase 1', 'Icon Valley Phase 2', 'Icon Valley Townhouses', 'Imperial Garden Homes',
#     'Indigo Boutique Apartments', 'Indigo Heights', 'Izmir Town', 'J Heights', 'Jail Road',
#     'Johar Town', 'Johar Town Phase 1', 'Johar Town Phase 2', 'Jubilee Town', 'Kahna', 'Khayaban',
#     'Khuda Buksh Colony', 'Kings Town', 'LDA Avenue', 'Lahore Motorway City', 'Lake City',
#     'Lake City Meadows', 'Lake City Meadows Phase 1', 'Lalazaar Garden', 'Low Cost', 'MM Alam Road',
#     'Main Boulevard Gulberg', 'Main Canal Bank Road', 'Marbella Drive Residency',
#     'Marghzar Officers Colony', 'Midway Commercial', 'Military Accounts Housing Society',
#     'Model Town', 'Mohlanwal Scheme', 'Mustafa Town', 'NFC 1', 'NSIT City', 'Nasheman',
#     'Nasheman Iqbal Phase 2', 'Nawab Town', 'Nespak Scheme Phase 3', 'New Lahore City',
#     'New Super Town', 'OLC', 'OPF Housing Scheme', 'Other', 'Oyster Court Luxury Residences',
#     'P & D Housing Society', 'PAF Falcon Complex', 'PCSIR Housing Scheme Phase 2',
#     'PCSIR Staff Colony', 'PGECHS Phase 2', 'PIA Housing Scheme', 'Pak Arab Housing Society',
#     'Pak Arab Housing Society Phase 1', 'Pak Arab Housing Society Phase 2',
#     'Pak Arab Society Phase 1', 'Pak Arab Society Phase 2', 'Palm City', 'Palm Villas',
#     'Palm Vista', 'Paragon City', 'Park View City', 'Pearl One Residencies',
#     'Pearl One Tower, Bahria Town', 'Penta Square By DHA Lahore', 'Pine Avenue',
#     'Punjab Coop Housing', 'Punjab Coop Housing Society', 'Punjab Small Industries Colony',
#     'Raiwind Road', 'Rehan Garden Phase 2', 'Revenue Society', 'Ring Road', 'SA Gardens Phase 2',
#     'Sabzazar Scheme', 'Samanabad', 'Sarwar Road', 'Shadab Garden', 'Shadman', 'Shah Jamal',
#     'Shami Road', 'Shershah Colony', 'Spanish Homes by Icon', 'Sui Gas Society Phase 1',
#     'Sukh Chayn Gardens', 'Super Town', 'Swiss Mall Gulberg', 'TIP Housing Society',
#     'Taj Bagh Scheme', 'Tajpura', 'Tariq Gardens', 'The Opus Luxury Residence',
#     'The Spring Apartment Homes', 'Township', 'Tricon Village', 'UET Housing Society',
#     'Union Green', 'Union Town', 'Valencia', 'Valencia Housing Society', 'Vital Homes DD',
#     'Walton Road', 'Wapda Town', 'Wapda Town Phase 1', 'Zahoor Elahi Road', 'Zameen Arx',
#     'Zameen Aurum, Gulberg 3', 'Zameen EON', 'Zameen Hive', 'Zameen Jade', 'Zameen NEO',
#     'Zameen Opal', 'Zameen Phoenix', 'Zameen Quadrangle', 'Zameen Vault', 'Zee Avenue'
# ]
#
#
# trained_areas = set(df["area"].unique())
# known_areas_set = set(KNOWN_AREAS)
#
# missing_from_known = trained_areas - known_areas_set
# extra_in_known = known_areas_set - trained_areas
#
# print("=== KNOWN_AREAS sync check ===")
# print(f"Areas in training data but MISSING from KNOWN_AREAS: {len(missing_from_known)}")
# print(missing_from_known)
# print(f"\nAreas in KNOWN_AREAS but NOT in training data (stale entries): {len(extra_in_known)}")
# print(extra_in_known)
#
# # ---- PART B: run the raw location strings from the 3 bad listings through extract_area ----
# def extract_area(location_text):
#     if not location_text:
#         return 'Other'
#     if '-' in location_text:
#         text = location_text.split('-')[0]
#     else:
#         text = location_text.split(',')[0]
#     return text.strip()
#
# bad_listings_raw_location = {
#     "DHA Phase 7 house":     "DHA Defence, Lahore, Punjab",
#     "Nespak Phase 3 house":  "Defence Road, Lahore, Punjab",
#     "Bahria Orchard flat":   "Bahria Orchard, Lahore, Punjab",
# }
#
# print("\n=== What extract_area() actually produces for the 3 bad listings ===")
# for name, loc in bad_listings_raw_location.items():
#     extracted = extract_area(loc)
#     in_training = extracted in trained_areas
#     in_known = extracted in known_areas_set
#     n_rows = len(df[df["area"] == extracted])
#     print(f"{name}:")
#     print(f"  raw location    : {loc}")
#     print(f"  extracted area  : '{extracted}'")
#     print(f"  rows in training with this area: {n_rows}")
#     print(f"  present in KNOWN_AREAS: {in_known}")
#     print()
# import pandas as pd
#
# df = pd.read_csv("listings_cleaned.csv")
#
# for keyword in ["DHA", "Defence"]:
#     matches = df[df["area"].str.contains(keyword, case=False, na=False)]["area"].unique()
#     print(f"=== area values containing '{keyword}' ===")
#     for m in matches:
#         count = len(df[df["area"] == m])
#         print(f"  '{m}'  ({count} rows)")
#     print()
# import requests
# from bs4 import BeautifulSoup
#
# # Use the DHA Phase 7 listing URL that gave the 61.6% error
# URL = "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html"
#
# headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
# resp = requests.get(URL, headers=headers, timeout=20)
# soup = BeautifulSoup(resp.text, "html.parser")
#
# print("=== 1. <nav> elements ===")
# for nav in soup.find_all("nav"):
#     text = nav.get_text(" > ", strip=True)
#     if text:
#         print(f"  {text[:300]}")
#
# print("\n=== 2. Anything with 'breadcrumb' in class/id/aria-label ===")
# for el in soup.find_all(attrs={"aria-label": True}):
#     if "breadcrumb" in el.get("aria-label", "").lower():
#         print(f"  aria-label={el.get('aria-label')}: {el.get_text(' > ', strip=True)[:300]}")
# for el in soup.select("[class*=breadcrumb], [id*=breadcrumb]"):
#     print(f"  {el.name}: {el.get_text(' > ', strip=True)[:300]}")
#
# print("\n=== 3. JSON-LD structured data (often has full address) ===")
# for script in soup.find_all("script", type="application/ld+json"):
#     print(f"  {script.string[:600] if script.string else ''}")
#     print("  ---")
#
# print("\n=== 4. Every element whose text mentions 'Phase' ===")
# seen = set()
# for el in soup.find_all(string=lambda s: s and "Phase" in s):
#     t = el.strip()
#     if t and t not in seen and len(t) < 150:
#         seen.add(t)
#         parent = el.parent
#         print(f"  <{parent.name} class={parent.get('class')} aria-label={parent.get('aria-label')}>: {t}")
#
# print("\n=== 5. All aria-labels on the page (for reference) ===")
# labels = {el.get("aria-label") for el in soup.find_all(attrs={"aria-label": True})}
# for l in sorted(x for x in labels if x):
#     print(f"  {l}")
# import requests
# from bs4 import BeautifulSoup
#
# URL = "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html"
#
# for label, ua in [
#     ("main.py UA", "Mozilla/5.0"),
#     ("full browser UA", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
# ]:
#     resp = requests.get(URL, headers={"User-Agent": ua}, timeout=20)
#     soup = BeautifulSoup(resp.text, "html.parser")
#
#     header = soup.find(attrs={"aria-label": "Property header"})
#     location = soup.find(attrs={"aria-label": "Location"})
#
#     print(f"--- {label} ---")
#     print(f"  status: {resp.status_code}, html length: {len(resp.text)}")
#     print(f"  'Property header' found: {header is not None}")
#     if header:
#         print(f"     -> {header.get_text(strip=True)!r}")
#     print(f"  'Location' found: {location is not None}")
#     if location:
#         print(f"     -> {location.get_text(strip=True)!r}")
#     print()
# import pandas as pd
# from clean_data import parse_price
#
# df = pd.read_csv("listings_cleaned.csv")
#
# print("=== columns and dtypes ===")
# print(df.dtypes)
# print()
#
# # Find the numeric price column, or build one
# if pd.api.types.is_numeric_dtype(df.get("price")):
#     price_col = "price"
# else:
#     numeric_candidates = [
#         c for c in df.columns
#         if "price" in c.lower() and pd.api.types.is_numeric_dtype(df[c])
#     ]
#     if numeric_candidates:
#         price_col = numeric_candidates[0]
#         print(f"Using existing numeric column: '{price_col}'\n")
#     else:
#         df["price_pkr"] = df["price"].apply(parse_price)
#         price_col = "price_pkr"
#         print("No numeric price column found — parsed 'price' into 'price_pkr'\n")
#
# df = df[df[price_col].notna() & df["size_marla"].notna() & (df["size_marla"] > 0)]
#
# flats = df[df["property_type"] == "Flat"]
# houses = df[df["property_type"] == "House"]
#
# print("=== 1. Size distribution by property type ===")
# print("FLATS:")
# print(flats["size_marla"].describe())
# big_flats = flats[flats["size_marla"] >= 10]
# print(f"  flats with size_marla >= 10: {len(big_flats)} ({100*len(big_flats)/len(flats):.1f}%)")
# print("\nHOUSES:")
# print(houses["size_marla"].describe())
#
# print("\n=== 2. Price per marla by type ===")
# for name, sub in [("Flats", flats), ("Houses", houses)]:
#     ppm = sub[price_col] / sub["size_marla"]
#     print(f"{name}: median price/marla = {ppm.median():,.0f}   (n={len(sub)})")
#
# print("\n=== 3. For the problem areas: house vs flat mix ===")
# for area in ["Askari 10", "Bahria Orchard Phase 4", "Bahria Orchard"]:
#     sub = df[df["area"] == area]
#     if len(sub) == 0:
#         print(f"'{area}': not present")
#         continue
#     f = sub[sub["property_type"] == "Flat"]
#     h = sub[sub["property_type"] == "House"]
#     print(f"'{area}': {len(sub)} rows -> {len(h)} houses, {len(f)} flats")
#     if len(f):
#         print(f"    flat  median price: {f[price_col].median():,.0f}")
#     if len(h):
#         print(f"    house median price: {h[price_col].median():,.0f}")
#
# print("\n=== 4. How many areas have ZERO flats? ===")
# mix = df.groupby("area")["property_type"].apply(lambda s: (s == "Flat").sum())
# print(f"  areas with 0 flats:   {(mix == 0).sum()} of {len(mix)}")
# print(f"  areas with 1-4 flats: {((mix >= 1) & (mix <= 4)).sum()}")
# import pandas as pd
#
# df = pd.read_csv("listings_cleaned.csv")
# df = df[df["price_numeric"].notna() & df["size_marla"].notna() & (df["size_marla"] > 0)]
# df["ppm"] = df["price_numeric"] / df["size_marla"]
#
# # (label, area, property_type, size, asking, predicted)
# cases = [
#     ("Askari 10 flat",        "Askari 10",              "Flat",  10.0, 34_500_000, 50_871_408),
#     ("Bahria Orchard flat",   "Bahria Orchard Phase 4", "Flat",   5.0,  6_700_000, 10_060_660),
#     ("DHA Phase 7 house",     "DHA Phase 7",            "House", 20.0, 79_900_000, 102_252_640),
#     ("Nespak Phase 3 house",  "Nespak Scheme Phase 3",  "House", 20.0, 44_000_000, 64_173_828),
# ]
#
# for label, area, ptype, size, asking, predicted in cases:
#     print(f"########## {label} ##########")
#     print(f"  asking {asking:,}  |  predicted {predicted:,}  |  {size} marla")
#
#     same = df[(df["area"] == area) & (df["property_type"] == ptype)]
#     print(f"  {ptype}s in '{area}': {len(same)}")
#     if len(same) == 0:
#         print("  no comparables at all\n")
#         continue
#
#     # comparables: within +/- 30% of the size
#     lo, hi = size * 0.7, size * 1.3
#     comps = same[(same["size_marla"] >= lo) & (same["size_marla"] <= hi)]
#     print(f"  comparables ({lo:.1f}-{hi:.1f} marla): {len(comps)}")
#     if len(comps) > 0:
#         print(f"    price   min/med/max: {comps['price_numeric'].min():,.0f} / "
#               f"{comps['price_numeric'].median():,.0f} / {comps['price_numeric'].max():,.0f}")
#         print(f"    ppm     median:      {comps['ppm'].median():,.0f}")
#         print(f"    asking is at percentile: "
#               f"{(comps['price_numeric'] < asking).mean()*100:.0f}%")
#         print(f"    predicted is at percentile: "
#               f"{(comps['price_numeric'] < predicted).mean()*100:.0f}%")
#     else:
#         print("    NONE — no training rows near this size in this area")
#
#     # how ppm varies with size within this area+type
#     print(f"  ppm by size band (all {ptype}s in this area):")
#     bands = [(0, 3), (3, 6), (6, 10), (10, 15), (15, 25), (25, 1000)]
#     for b_lo, b_hi in bands:
#         band = same[(same["size_marla"] >= b_lo) & (same["size_marla"] < b_hi)]
#         if len(band) > 0:
#             print(f"    {b_lo:>3}-{b_hi:<4} marla: n={len(band):<4} "
#                   f"median ppm={band['ppm'].median():,.0f}")
#     print()
# print(pd.read_csv('listings_cleaned.csv')['area'].nunique())
# import pandas as pd
# import numpy as np
#
# df = pd.read_csv('listings_cleaned.csv')
# df = df[df['price_numeric'].notna() & df['size_marla'].notna() & (df['size_marla'] > 0)]
#
# # Bucket size so "similar" properties land in the same cell
# bins = [0, 3, 5, 7, 10, 15, 20, 30, 50, 1e9]
# df['size_band'] = pd.cut(df['size_marla'], bins=bins)
#
# # A "cell" = same area, same property type, same size band, same bedroom count.
# # Any model using only these features MUST give one answer per cell.
# cells = df.groupby(['area', 'property_type', 'size_band', 'beds'], observed=True)
#
# results = []
# for key, g in cells:
#     if len(g) < 8:          # need enough rows for the spread to mean anything
#         continue
#     med = g['price_numeric'].median()
#     # if the model predicted the cell median, how wrong would it be per listing?
#     err = np.abs(g['price_numeric'] - med) / g['price_numeric']
#     results.append({
#         'n': len(g),
#         'median_price': med,
#         'spread_ratio': g['price_numeric'].max() / g['price_numeric'].min(),
#         'median_err_if_perfect': err.median(),
#         'mean_err_if_perfect': err.mean(),
#     })
#
# r = pd.DataFrame(results)
# print(f"cells with >=8 listings: {len(r)}  (covering {r['n'].sum():,} listings)\n")
#
# print("If a PERFECT model predicted each cell's median price:")
# print(f"  median error across cells : {r['median_err_if_perfect'].median():.1%}")
# print(f"  mean   error across cells : {r['mean_err_if_perfect'].mean():.1%}")
# print(f"  worst cell median error   : {r['median_err_if_perfect'].max():.1%}")
#
# print(f"\nWithin-cell price spread (max/min):")
# print(f"  median cell: {r['spread_ratio'].median():.1f}x")
# print(f"  75th pct   : {r['spread_ratio'].quantile(0.75):.1f}x")
# print(f"  worst cell : {r['spread_ratio'].max():.1f}x")
#
# print("\nShare of cells where a perfect model still misses by more than:")
# for t in [0.10, 0.20, 0.30, 0.50]:
#     print(f"  {t:.0%}: {(r['median_err_if_perfect'] > t).mean():.1%} of cells")
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
#
# df = pd.read_csv('listings_cleaned.csv')
#
# features = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# x = df[features].copy()
# y = df['price_numeric']
# x['area'] = x['area'].astype('category')
# x['property_type'] = x['property_type'].astype('category')
#
# x_tr, x_te, y_tr, y_te = train_test_split(x, y, test_size=0.2, random_state=42)
#
# model = xgb.XGBRegressor(enable_categorical=True).fit(x_tr, np.log1p(y_tr))
# pred = np.expm1(model.predict(x_te))
# err = np.abs(pred - y_te) / y_te
#
# # A "twin" = a training row with identical area, type, size, beds, baths.
# # The model has effectively already seen this property.
# key_cols = ['area', 'property_type', 'size_marla', 'beds', 'baths']
# train_keys = set(map(tuple, x_tr[key_cols].astype(str).values))
# test_keys = list(map(tuple, x_te[key_cols].astype(str).values))
# has_twin = np.array([k in train_keys for k in test_keys])
#
# print(f"test listings: {len(x_te):,}")
# print(f"  WITH a near-twin in training: {has_twin.sum():,} ({has_twin.mean():.1%})")
# print(f"  WITHOUT (genuinely novel)   : {(~has_twin).sum():,} ({(~has_twin).mean():.1%})\n")
#
# for label, mask in [("with twin (memorizable)", has_twin), ("no twin (truly novel)", ~has_twin)]:
#     if mask.sum() == 0:
#         continue
#     e = err[mask]
#     print(f"{label}:")
#     print(f"  median % error: {np.median(e):.1%}")
#     print(f"  mean   % error: {np.mean(e):.1%}")
#     print(f"  share over 30% error: {(e > 0.30).mean():.1%}")
#     print()
#
# print("If the 'no twin' number is much worse than 'with twin', your test")
# print("metrics were partly measuring recall, and the no-twin figure is the")
# print("honest estimate of live performance.")
# import requests
# from bs4 import BeautifulSoup
# import json
#
# URLS = {
#     "DHA Phase 7 house": "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html",
#     "Bahria Orchard flat": "https://www.zameen.com/Property/bahria_orchard_bahria_orchard_phase_4_5_marla_brand_new_ground_floor_flat_available_for_sale_in_bahria_orchard_raiwind_road_lahore-54631583-11201-1.html",
# }
#
# headers = {"User-Agent": "Mozilla/5.0"}
#
# for name, url in URLS.items():
#     print("=" * 70)
#     print(name)
#     print("=" * 70)
#     soup = BeautifulSoup(requests.get(url, headers=headers, timeout=20).text, "html.parser")
#
#     # 1. The structured details block
#     details = soup.find(attrs={"aria-label": "Property details"})
#     if details:
#         print("\n--- 'Property details' block (raw text) ---")
#         print(details.get_text(" | ", strip=True)[:2000])
#     else:
#         print("\n--- no 'Property details' block found ---")
#
#     # 2. Look for label/value pairs anywhere
#     print("\n--- possible label:value pairs (spans in pairs) ---")
#     seen = set()
#     for li in soup.find_all(["li", "div"]):
#         spans = li.find_all("span", recursive=False)
#         if len(spans) == 2:
#             k = spans[0].get_text(strip=True)
#             v = spans[1].get_text(strip=True)
#             if k and v and len(k) < 40 and len(v) < 60 and (k, v) not in seen:
#                 seen.add((k, v))
#                 print(f"  {k:<32} = {v}")
#
#     # 3. JSON-LD blocks other than breadcrumbs
#     print("\n--- JSON-LD (non-breadcrumb) ---")
#     for s in soup.find_all("script", type="application/ld+json"):
#         if not s.string:
#             continue
#         try:
#             data = json.loads(s.string)
#         except Exception:
#             continue
#         if isinstance(data, dict) and data.get("@type") != "BreadcrumbList":
#             print(f"  keys: {list(data.keys())}")
#             print(f"  {json.dumps(data)[:800]}")
#
#     # 4. Description length (how much prose is there to mine?)
#     desc = soup.find(attrs={"aria-label": "Property description"})
#     if desc:
#         text = desc.get_text(" ", strip=True)
#         print(f"\n--- description: {len(text)} chars ---")
#         print(text[:500])
#     print("\n")
# import requests
# from bs4 import BeautifulSoup
# import re
#
# URL = "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html"
#
# html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
# print(f"html length: {len(html):,}\n")
#
# # --- 1. Are the amenity strings present in the raw server HTML at all? ---
# markers = ["Built in year", "Servant Quarter", "Parking Spaces", "Double Glazed",
#            "Electricity Backup", "Central Air Conditioning", "Waste Disposal",
#            "Flooring", "Main Features", "Amenities"]
# print("=== marker present in raw HTML? ===")
# for m in markers:
#     print(f"  {m:<28} {'YES' if m in html else 'no'}")
#
# soup = BeautifulSoup(html, "html.parser")
#
# # --- 2. If present, find where 'Built in year' lives and dump its neighbourhood ---
# node = soup.find(string=re.compile("Built in year"))
# if node:
#     print("\n=== structure around 'Built in year' ===")
#     el = node.parent
#     for depth in range(5):
#         if el is None:
#             break
#         print(f"  depth {depth}: <{el.name} class={el.get('class')} aria-label={el.get('aria-label')}>")
#         el = el.parent
#
#     # walk up to a container holding several amenities, then list them all
#     container = node.parent
#     for _ in range(6):
#         if container is None:
#             break
#         text = container.get_text(" | ", strip=True)
#         if text.count("|") > 10:
#             print("\n=== all amenity text in that container ===")
#             print(text[:1500])
#             break
#         container = container.parent
# else:
#     print("\n'Built in year' NOT in server HTML -> it is JavaScript-rendered.")
#     print("Scraping it would need Playwright/Selenium, not requests.")
#
# # --- 3. Covered area appears in the description prose ---
# desc = soup.find(attrs={"aria-label": "Property description"})
# if desc:
#     text = desc.get_text(" ", strip=True)
#     m = re.search(r"([\d,\.]+)\s*sq\s*\.?\s*ft", text, re.I)
#     print(f"\n=== covered area regex on description ===")
#     print(f"  match: {m.group(0) if m else 'none'}")
# import requests
# from bs4 import BeautifulSoup
# import re
#
# # HEADERS = {"User-Agent": "Mozilla/5.0"}
# #
# # # Boolean amenities worth flagging
# BOOL_FEATURES = [
#     "Double Glazed Windows", "Central Air Conditioning", "Central Heating",
#     "Electricity Backup", "Waste Disposal", "Flooring", "Swimming Pool",
#     "Lawn or Garden", "Service Elevators", "Security Staff",
# ]
#
# # Numeric amenities of the form "Label: N"
# NUM_FEATURES = ["Built in year", "Parking Spaces", "Floors",
#                 "Servant Quarters", "Bedrooms", "Bathrooms", "Store Rooms"]
#
#
# def parse_detail_page(url):
#     """Return a dict of extra features from a Zameen detail page."""
#     out = {}
#     try:
#         html = requests.get(url, headers=HEADERS, timeout=20).text
#     except Exception as e:
#         return {"_error": str(e)}
#
#     soup = BeautifulSoup(html, "html.parser")
#
#     # --- amenities: anchor on the text, not the hashed class names ---
#     # Grab the whole page text once; amenity labels are distinctive enough.
#     page_text = soup.get_text(" | ", strip=True)
#
#     for feat in NUM_FEATURES:
#         m = re.search(re.escape(feat) + r"\s*\|?\s*:\s*\|?\s*(\d+)", page_text)
#         key = feat.lower().replace(" ", "_")
#         out[key] = int(m.group(1)) if m else None
#
#     for feat in BOOL_FEATURES:
#         key = "has_" + feat.lower().replace(" ", "_")
#         out[key] = 1 if feat in page_text else 0
#
#     # --- covered area from the description prose ---
#     desc_el = soup.find(attrs={"aria-label": "Property description"})
#     desc = desc_el.get_text(" ", strip=True) if desc_el else ""
#     out["description_length"] = len(desc)
#
#     m = re.search(r"([\d,]+(?:\.\d+)?)\s*sq\s*\.?\s*(?:ft|feet)", desc, re.I)
#     out["covered_area_sqft"] = float(m.group(1).replace(",", "")) if m else None
#
#     # --- a few quality keywords from the description ---
#     d = desc.lower()
#     out["desc_marble"] = 1 if "marble" in d else 0
#     out["desc_imported"] = 1 if "imported" in d else 0
#     out["desc_solar"] = 1 if "solar" in d else 0
#     out["desc_renovat"] = 1 if "renovat" in d else 0
#     out["desc_grey_structure"] = 1 if "grey structure" in d else 0
#
#     return out
#
#
# if __name__ == "__main__":
#     tests = {
#         "DHA Phase 7 house": "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html",
#         "Bahria Orchard flat": "https://www.zameen.com/Property/bahria_orchard_bahria_orchard_phase_4_5_marla_brand_new_ground_floor_flat_available_for_sale_in_bahria_orchard_raiwind_road_lahore-54631583-11201-1.html",
#         "Park View City house": "https://www.zameen.com/Property/lahore_park_view_city_3_years_installment_plan_luxury_10_marla_brand_new_house_in_park_view_city_lahore-54640302-1466-1.html",
#     }
#     for name, url in tests.items():
#         print(f"=== {name} ===")
#         for k, v in parse_detail_page(url).items():
#             print(f"  {k:<28} {v}")
#         print()
#
#
# """
# Coverage pilot: how often are the new detail-page fields actually filled in?
# Scrapes a few SEARCH pages for listing URLs, then parses N detail pages.
# """
# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import time
# import re
# # reuse the parser
#
# HEADERS = {"User-Agent": "Mozilla/5.0"}
#
# # A few search-result pages (houses and flats, mixed areas)
# SEARCH_PAGES = [
#     "https://www.zameen.com/Houses_Property/Lahore-1-1.html",
#     "https://www.zameen.com/Houses_Property/Lahore-1-2.html",
#     "https://www.zameen.com/Houses_Property/Lahore-1-3.html",
#     "https://www.zameen.com/Homes/Lahore-1-1.html",
#     "https://www.zameen.com/Homes/Lahore-1-2.html",
# ]
#
# N_LISTINGS = 100      # keep the pilot small
# DELAY = 1.5           # be polite; avoids getting blocked
#
#
# def collect_urls(search_url):
#     """Pull detail-page links off one search-results page."""
#     try:
#         html = requests.get(search_url, headers=HEADERS, timeout=20).text
#     except Exception as e:
#         print(f"  failed: {e}")
#         return []
#     soup = BeautifulSoup(html, "html.parser")
#     urls = set()
#     for a in soup.find_all("a", href=True):
#         href = a["href"]
#         if "/Property/" in href and href.endswith(".html"):
#             if href.startswith("/"):
#                 href = "https://www.zameen.com" + href
#             urls.add(href)
#     return list(urls)
#
#
# all_urls = []
# for sp in SEARCH_PAGES:
#     print(f"collecting from {sp}")
#     found = collect_urls(sp)
#     print(f"  {len(found)} listing urls")
#     all_urls.extend(found)
#     time.sleep(DELAY)
#
# all_urls = list(dict.fromkeys(all_urls))[:N_LISTINGS]
# print(f"\ntotal unique urls to check: {len(all_urls)}\n")
#
# rows = []
# for i, url in enumerate(all_urls, 1):
#     feats = parse_detail_page(url)
#     feats["url"] = url
#     rows.append(feats)
#     if i % 10 == 0:
#         print(f"  parsed {i}/{len(all_urls)}")
#     time.sleep(DELAY)
#
# df = pd.DataFrame(rows)
# df.to_csv("pilot_details.csv", index=False)
# print(f"\nsaved pilot_details.csv ({len(df)} rows)\n")
#
# print("=== FILL RATE: how often is each field actually present? ===")
# key_fields = ["built_in_year", "covered_area_sqft", "parking_spaces",
#               "floors", "servant_quarters", "store_rooms"]
# for f in key_fields:
#     if f in df.columns:
#         filled = df[f].notna().mean()
#         print(f"  {f:<22} {filled:6.1%}")
#
# print("\n=== boolean amenities: share marked present ===")
# for c in sorted(c for c in df.columns if c.startswith("has_")):
#     print(f"  {c:<34} {df[c].mean():6.1%}")
#
# print("\n=== description length ===")
# print(df["description_length"].describe())
# import pandas as pd
# d = pd.read_csv("pilot_details.csv")
# print("rows:", len(d))
# if "_error" in d.columns:
#     print("errors:", d["_error"].notna().sum())
#     print(d["_error"].dropna().head())
# ok = d[d["description_length"].notna()]
# print("successful:", len(ok))
# print("built_in_year fill among successful:", ok["built_in_year"].notna().mean())
# print("desc length > 0:", (ok["description_length"] > 0).mean())
# """Is the 25% fill rate concentrated on expensive listings (where our errors are worst)?"""
# import pandas as pd
# import numpy as np
# import re
# import time
# import requests
# from bs4 import BeautifulSoup
#
# HEADERS = {"User-Agent": "Mozilla/5.0"}
# d = pd.read_csv("pilot_details.csv")
# d = d[d["description_length"].notna()]          # drop the mailto junk
# print(f"working with {len(d)} real listings\n")
#
#
# def get_price_size(url):
#     try:
#         soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=20).text, "html.parser")
#     except Exception:
#         return None, None, None
#     txt = soup.get_text(" | ", strip=True)
#
#     price = None
#     m = re.search(r"PKR\s*\|?\s*([\d.]+)\s*(Crore|Lakh|Arab)", txt)
#     if m:
#         mult = {"Lakh": 1e5, "Crore": 1e7, "Arab": 1e9}[m.group(2)]
#         price = float(m.group(1)) * mult
#
#     size = None
#     m = re.search(r"Area\s*\|?\s*([\d.]+)\s*(Marla|Kanal)", txt)
#     if m:
#         size = float(m.group(1)) * (20 if m.group(2) == "Kanal" else 1)
#
#     ptype = "Flat" if re.search(r"Type\s*\|?\s*Flat", txt) else "House"
#     return price, size, ptype
#
#
# rows = []
# for i, url in enumerate(d["url"], 1):
#     p, s, t = get_price_size(url)
#     rows.append({"url": url, "price": p, "size_marla": s, "ptype": t})
#     if i % 15 == 0:
#         print(f"  {i}/{len(d)}")
#     time.sleep(1.0)
#
# meta = pd.DataFrame(rows)
# m = d.merge(meta, on="url")
# m["has_amenities"] = m["built_in_year"].notna()
#
# print("\n=== fill rate by price quartile ===")
# m2 = m[m["price"].notna()].copy()
# m2["price_q"] = pd.qcut(m2["price"], 4, labels=["cheapest", "low-mid", "high-mid", "priciest"])
# print(m2.groupby("price_q", observed=True).agg(
#     n=("has_amenities", "size"),
#     fill_rate=("has_amenities", "mean"),
#     median_price=("price", "median"),
# ).to_string())
#
# print("\n=== fill rate by property type ===")
# print(m.groupby("ptype").agg(
#     n=("has_amenities", "size"),
#     fill_rate=("has_amenities", "mean"),
# ).to_string())
#
# print("\n=== fill rate by size band ===")
# m3 = m[m["size_marla"].notna()].copy()
# m3["band"] = pd.cut(m3["size_marla"], [0, 5, 10, 20, 1e9],
#                     labels=["<=5", "5-10", "10-20", "20+"])
# print(m3.groupby("band", observed=True).agg(
#     n=("has_amenities", "size"),
#     fill_rate=("has_amenities", "mean"),
# ).to_string())

# import pandas as pd
# import requests, re
# from bs4 import BeautifulSoup
#
# HEADERS = {"User-Agent": "Mozilla/5.0"}
# d = pd.read_csv("pilot_details.csv")
# d = d[d["description_length"].notna()]
#
# d["has_amen"] = d["built_in_year"].notna()
# good = d[d["has_amen"]]
# bad = d[~d["has_amen"]]
#
# print(f"with amenities: {len(good)}   without: {len(bad)}\n")
#
# print("=== 5 URLs WITHOUT amenities ===")
# for u in bad["url"].head(5):
#     print(" ", u)
#
# print("\n=== 5 URLs WITH amenities ===")
# for u in good["url"].head(5):
#     print(" ", u)
#
# # Fetch one of each and compare what's actually on the page
# for label, url in [("NO AMENITIES", bad["url"].iloc[0]), ("HAS AMENITIES", good["url"].iloc[0])]:
#     print(f"\n{'='*60}\n{label}\n{url}\n{'='*60}")
#     html = requests.get(url, headers=HEADERS, timeout=20).text
#     soup = BeautifulSoup(html, "html.parser")
#     print(f"  html length : {len(html):,}")
#     print(f"  <h1>        : {soup.find('h1').get_text(strip=True)[:90] if soup.find('h1') else 'NONE'}")
#     for marker in ["Amenities", "Main Features", "Built in year", "Property details",
#                    "Property header", "Property description", "Purpose"]:
#         print(f"  {marker:<22} {'YES' if marker in html else 'no'}")
#     hdr = soup.find(attrs={"aria-label": "Property header"})
#     print(f"  header text : {hdr.get_text(strip=True)[:80] if hdr else 'NONE'}")
# """Coverage pilot, corrected: only genuine zameen.com/Property/ pages."""
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse
# import pandas as pd
# import time
#
# HEADERS = {"User-Agent": "Mozilla/5.0"}
#
# SEARCH_PAGES = [
#     "https://www.zameen.com/Houses_Property/Lahore-1-1.html",
#     "https://www.zameen.com/Houses_Property/Lahore-1-2.html",
#     "https://www.zameen.com/Houses_Property/Lahore-1-3.html",
#     "https://www.zameen.com/Homes_Flats/Lahore-1-1.html",
#     "https://www.zameen.com/Homes_Flats/Lahore-1-2.html",
# ]
#
# N_LISTINGS = 100
# DELAY = 1.5
#
#
# def is_real_listing(href):
#     """Only accept genuine Zameen property pages on the zameen.com host."""
#     p = urlparse(href)
#     if p.netloc and p.netloc not in ("www.zameen.com", "zameen.com"):
#         return False                      # kills facebook/twitter/mailto
#     if p.query:
#         return False                      # share links carry query strings
#     return p.path.startswith("/Property/") and p.path.endswith(".html")
#
#
# def collect_urls(search_url):
#     try:
#         html = requests.get(search_url, headers=HEADERS, timeout=20).text
#     except Exception as e:
#         print(f"  failed: {e}")
#         return []
#     soup = BeautifulSoup(html, "html.parser")
#     out = set()
#     for a in soup.find_all("a", href=True):
#         if is_real_listing(a["href"]):
#             href = a["href"]
#             if href.startswith("/"):
#                 href = "https://www.zameen.com" + href
#             out.add(href)
#     return list(out)
#
#
# all_urls = []
# for sp in SEARCH_PAGES:
#     found = collect_urls(sp)
#     print(f"{sp} -> {len(found)} listings")
#     all_urls.extend(found)
#     time.sleep(DELAY)
#
# all_urls = list(dict.fromkeys(all_urls))[:N_LISTINGS]
#
# # SANITY CHECK before spending 5 minutes fetching
# print(f"\n=== {len(all_urls)} urls collected. First 5: ===")
# for u in all_urls[:5]:
#     print("  ", u)
# bad = [u for u in all_urls if not u.startswith("https://www.zameen.com/Property/")]
# print(f"non-listing urls that slipped through: {len(bad)}")
# if bad:
#     print("ABORTING - filter still broken")
#     raise SystemExit(1)
#
# rows = []
# for i, url in enumerate(all_urls, 1):
#     f = parse_detail_page(url)
#     f["url"] = url
#     rows.append(f)
#     if i % 20 == 0:
#         print(f"  parsed {i}/{len(all_urls)}")
#     time.sleep(DELAY)
#
# df = pd.DataFrame(rows)
# df.to_csv("pilot_details_v2.csv", index=False)
#
# fetched = df[df["description_length"].notna()]
# print(f"\nfetched OK: {len(fetched)}/{len(df)}")
# if "_error" in df.columns and df["_error"].notna().any():
#     print(f"errors: {df['_error'].notna().sum()}")
#     print(df["_error"].dropna().iloc[0][:120])
#
# print("\n=== FILL RATE (genuine listings only) ===")
# for f in ["built_in_year", "covered_area_sqft", "parking_spaces",
#           "floors", "servant_quarters", "store_rooms"]:
#     if f in fetched.columns:
#         print(f"  {f:<22} {fetched[f].notna().mean():6.1%}")
#
# print(f"\n  description present     {(fetched['description_length'] > 0).mean():6.1%}")
# print(f"  median description len  {fetched['description_length'].median():.0f}")
# import pandas as pd
# d = pd.read_csv('detail_features.csv')
# print(d.shape)
# print("detail_location fill:", d['detail_location'].notna().mean())
# print("description present:", (d['description_length'] > 0).mean())
# print(d[['url','detail_location','built_in_year']].head(3).to_string())
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# import xgboost as xgb
#
# df = pd.read_csv('listings_cleaned.csv')
#
# # --- 1. Does built_in_year actually vary? ---
# print("=== built_in_year distribution ===")
# print(df['built_in_year'].value_counts().head(10).to_string())
# print(f"\nfill: {df['built_in_year'].notna().mean():.1%}")
# print(f"unique values: {df['built_in_year'].nunique()}")
# b = df['built_in_year'].dropna()
# if len(b):
#     print(f"share 2024 or later: {(b >= 2024).mean():.1%}")
#     print(f"share 2020 or later: {(b >= 2020).mean():.1%}")
#
# # --- 2. Ablation: old 12 features vs all 44, same data, same splits ---
# AMENITY_BOOLS = [c for c in df.columns if c.startswith("has_") and c != "has_basement"]
# NUMERIC_AMENITIES = ["built_in_year", "parking_spaces", "floors",
#                      "servant_quarters", "store_rooms"]
# no_block = df[NUMERIC_AMENITIES].isna().all(axis=1)
# df.loc[no_block, AMENITY_BOOLS] = np.nan
# DESC_FLAGS = [c for c in df.columns if c.startswith("desc_")]
#
# ORIGINAL = ['size_marla', 'beds', 'baths', 'area', 'property_type', 'floor',
#             'is_new', 'is_furnished', 'is_luxury', 'has_basement', 'is_corner', 'is_commercial']
# ALL_FEATS = ORIGINAL + NUMERIC_AMENITIES + AMENITY_BOOLS + ['description_length'] + DESC_FLAGS
# DESC_ONLY = ORIGINAL + ['description_length'] + DESC_FLAGS
#
# y = df['price_numeric']
# SEEDS = [0, 7, 21, 42, 99]
# KEY = ['area', 'property_type', 'size_marla', 'beds', 'baths']
#
# results = {}
# for name, feats in [("original 12", ORIGINAL), ("+ desc only", DESC_ONLY), ("all 44", ALL_FEATS)]:
#     x = df[feats].copy()
#     x['area'] = x['area'].astype('category')
#     x['property_type'] = x['property_type'].astype('category')
#     novel_meds, novel_over30 = [], []
#     for s in SEEDS:
#         xtr, xte, ytr, yte = train_test_split(x, y, test_size=0.2, random_state=s)
#         m = xgb.XGBRegressor(enable_categorical=True, random_state=s).fit(xtr, np.log1p(ytr))
#         pred = np.expm1(m.predict(xte))
#         tk = set(map(tuple, xtr[KEY].astype(str).values))
#         novel = ~np.array([tuple(k) in tk for k in xte[KEY].astype(str).values])
#         err = np.abs(pred[novel] - yte[novel]) / yte[novel]
#         novel_meds.append(np.median(err) * 100)
#         novel_over30.append((err > 0.30).mean() * 100)
#     results[name] = (novel_meds, novel_over30)
#     print(f"\n--- {name} ({len(feats)} features) ---")
#     print(f"  NOVEL median % error per seed: {['%.1f' % v for v in novel_meds]}")
#     print(f"  mean: {np.mean(novel_meds):.2f}%   |  >30% off mean: {np.mean(novel_over30):.1f}%")
#
# print("\n=== paired: all 44 minus original 12, per seed ===")
# diff = np.array(results["all 44"][0]) - np.array(results["original 12"][0])
# print("  " + "  ".join(f"{d:+.2f}" for d in diff))
# print(f"  mean {diff.mean():+.2f} pp   (negative = new features helped)")
#
# """What fraction of real listings would each threshold flag?"""
# import pandas as pd
# import numpy as np
#
# df = pd.read_csv('listings_cleaned.csv')
# df = df[df['price_numeric'].notna() & df['size_marla'].notna() & (df['size_marla'] > 0)]
#
# def comps_for(row, band_lo, band_hi, min_comps=5):
#     lo, hi = row['size_marla'] * 0.7, row['size_marla'] * 1.3
#     c = df[(df['area'] == row['area'])
#            & (df['property_type'] == row['property_type'])
#            & (df['size_marla'] >= lo) & (df['size_marla'] <= hi)]
#     c = c[c.index != row.name]          # exclude the listing itself
#     if len(c) >= 20:
#         ppm = c['price_numeric'] / c['size_marla']
#         c = c[(ppm >= ppm.quantile(0.02)) & (ppm <= ppm.quantile(0.98))]
#     if len(c) < min_comps:
#         return None
#     p = c['price_numeric']
#     return p.quantile(band_lo), p.quantile(band_hi)
#
# sample = df.sample(n=600, random_state=42)
#
# print(f"{'band':<14}{'margin':<9}{'no comps':<11}{'below':<9}{'above':<9}{'flagged'}")
# for band_lo, band_hi in [(0.25, 0.75), (0.15, 0.85), (0.10, 0.90)]:
#     for margin in [0.0, 0.05, 0.08]:
#         n_none = n_below = n_above = 0
#         for _, row in sample.iterrows():
#             res = comps_for(row, band_lo, band_hi)
#             if res is None:
#                 n_none += 1
#                 continue
#             lo_p, hi_p = res
#             ask = row['price_numeric']
#             if ask < lo_p * (1 - margin):
#                 n_below += 1
#             elif ask > hi_p * (1 + margin):
#                 n_above += 1
#         judged = len(sample) - n_none
#         flagged = (n_below + n_above) / judged * 100 if judged else 0
#         print(f"{band_lo:.2f}-{band_hi:.2f}   {margin:<9.0%}{n_none/len(sample):<11.0%}"
#               f"{n_below/judged:<9.0%}{n_above/judged:<9.0%}{flagged:.0f}%")
# import requests, re
# html = requests.get(
#     "https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html",
#     headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
#
# imgs = re.findall(r'https://media\.zameen\.com/thumbnails/[\w\-]+\.jpe?g', html)
# uniq = list(dict.fromkeys(imgs))
# print(f"{len(uniq)} unique images")
# for u in uniq[:10]:
#     print(" ", u)
# import requests, re
# def ids(u):
#     h = requests.get(u, headers={"User-Agent":"Mozilla/5.0"}, timeout=20).text
#     return set(re.findall(r'media\.zameen\.com/thumbnails/(\d+)-\d+x\d+\.jpe?g', h))
#
# a = ids("https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html")
# b = ids("https://www.zameen.com/Property/lahore_park_view_city_3_years_installment_plan_luxury_10_marla_brand_new_house_in_park_view_city_lahore-54640302-1466-1.html")
# print("shared (likely placeholders):", a & b)
# import requests, re
# html = requests.get("https://www.zameen.com/Property/dha_defence_dha_phase_7_ultra_luxury_1_kanal_brand_new_fully_furnished_bungalow_15_kv_solar_top-notch_construction_dha_phase_7_100_original_deal-51524283-1450-1.html",
#     headers={"User-Agent":"Mozilla/5.0"}, timeout=20).text
# ids = []
# for m in re.finditer(r'media\.zameen\.com/thumbnails/(\d+)-\d+x\d+\.jpe?g', html):
#     if m.group(1) not in ids: ids.append(m.group(1))
# for i, pid in enumerate(ids[:10]):
#     print(i, pid, f"https://media.zameen.com/thumbnails/{pid}-800x600.jpeg")
# import requests
# for pid in ["305705429", "305300463"]:   # a real photo, and the placeholder
#     u = f"https://media.zameen.com/thumbnails/{pid}-800x600.jpeg"
#     r = requests.head(u, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
#     print(pid, r.status_code, r.headers.get("Content-Length"))
