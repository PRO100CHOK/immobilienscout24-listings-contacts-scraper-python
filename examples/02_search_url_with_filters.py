"""Scrape a search you built on immobilienscout24.de, filters and all.

Set up the search in your browser (city, price, rooms, features, sorting),
copy the address bar URL and paste it into `startUrls`. Listing URLs
(/expose/<id>) can be mixed in the same list.

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
import os

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

START_URLS = [
    # 2+ room flats for rent in Cologne up to 1,400 EUR
    "https://www.immobilienscout24.de/Suche/de/nordrhein-westfalen/koeln/wohnung-mieten?price=-1400&numberofrooms=2-",
    # houses for sale in Munich
    "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/haus-kaufen",
]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

try:
    run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
        "startUrls": [{"url": u} for u in START_URLS],
        "fetchDetails": True,
        "extractEmails": False,
        "language": "en",
        "maxItems": 60,
    })
except ApifyApiError as exc:
    raise SystemExit(f"Actor run failed: {exc}")

for x in client.dataset(run["defaultDatasetId"]).iterate_items():
    price = x.get("purchasePrice") or x.get("baseRent") or x.get("price")
    print(f"[{x.get('realEstateType')}] {price or '?':>9} EUR  {x.get('livingSpace') or '?':>5} m2  "
          f"built {x.get('yearConstructed') or '?'}  energy {x.get('energyEfficiencyClass') or '?'}  "
          f"{x.get('url')}")
