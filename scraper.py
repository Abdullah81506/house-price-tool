import requests
from bs4 import BeautifulSoup
import time
import csv

headers = {"User-Agent": "Mozilla/5.0"}

def scrape_page(url, max_retries=2):
    for attempt in range(max_retries+1):
        resp = requests.get(url, headers=headers)
        # print(url, "->", resp.status_code, len(resp.text))
        soup = BeautifulSoup(resp.text, "html.parser")
        # print("Does _5b98ebdf appear?", "_5b98ebdf" in resp.text)
        # print("Does aria-lab el=\"Listing\" appear?", 'aria-label="Listing"' in resp.text)
        listings = []

        cards = soup.find_all("li", attrs={"aria-label": "Listing"})
        for card in cards:
            # title_div = card.find("div", class_="d870ae17")
            # title = title_div["title"] if title_div else None
            title_h2 = card.find("h2", attrs={"aria-label": "Title"})
            title = title_h2.get_text(strip=True) if title_h2 else None

            location_div = card.find("div", attrs={"aria-label": "Location"})
            location = location_div.get_text(strip=True) if location_div else None

            currency = card.find("span", attrs={"aria-label": "Currency"})
            price = card.find("span", attrs={"aria-label": "Price"})
            currency_text = currency.get_text(strip=True) if currency else None
            price_text = price.get_text(strip=True) if price else None

            beds_span = card.find("span", attrs={"aria-label": "Beds"})
            baths_span = card.find("span", attrs={"aria-label": "Baths"})
            size_span = card.find("span", attrs={"aria-label": "Area"})

            beds = beds_span.get_text(strip=True) if beds_span else None
            baths = baths_span.get_text(strip=True) if baths_span else None
            size = size_span.get_text(strip=True) if size_span else None

            link = card.find("a", href=True)
            url = link["href"] if link else None
            if url and url.startswith("/"):
                url = "https://www.zameen.com" + url

            listings.append({
                "title": title, "location": location, "currency": currency_text, "price": price_text,
                "beds": beds, "baths": baths, "size": size, 'url': url
            })

        missing_titles = sum(1 for l in listings if l["title"] is None)
        if len(cards) > 0 and missing_titles / len(cards) > 0.5:
            print(f"Page looked degraded (attempt {attempt + 1}), retrying: {url}")
            time.sleep(3)
            continue
        print("Cards found:", len(cards))
        return listings
    print(f"Giving up on {url} after {max_retries + 1} attempts")
    return listings

def scrape_and_save(base_url, output_file, property_type, num_pages):
    fieldnames = ["title", "location", "currency", "price", "beds", "baths", "size", "page", "property_type", 'url']

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        total = 0
        for page_num in range(1, num_pages+1):
            url = base_url.format(page_num)
            try:
                page_listings = scrape_page(url)
                for l in page_listings:
                    l["page"] = page_num
                    l["property_type"] = property_type
                writer.writerows(page_listings)
                total += len(page_listings)
                print(f"Page {page_num}: {len(page_listings)} listings (total so far: {total})")
            except Exception as e:
                print(f"Page {page_num} failed: {e}")
            time.sleep(1.5)
    print(f"Done. Scraped {total} listings total.")

if __name__ == '__main__':
    scrape_and_save("https://www.zameen.com/Houses_Property/Lahore-1-{}.html", "listings_houses.csv", "House", 400)
    scrape_and_save("https://www.zameen.com/Flats_Apartments/Lahore-1-{}.html", "listings_flats.csv", "Flat", 131)
# if __name__ == '__main__':
#     test = scrape_page("https://www.zameen.com/Houses_Property/Lahore-1-1.html")
#     print(f"{len(test)} cards")
#     for l in test[:3]:
#         print(l["title"][:50], "->", l["url"])
#     print("missing urls:", sum(1 for l in test if not l["url"]))