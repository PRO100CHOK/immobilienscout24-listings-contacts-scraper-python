"""Minimal ImmobilienScout24 search: 25 newest rental flats in Hamburg.

Type a city, district or postcode into `locations` and pick a property type.

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
    "locations": ["Hamburg"],
    "realEstateType": "apartmentrent",
    "sorting": "-firstactivation",
    "extractEmails": False,
    "maxItems": 25,
})

for x in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"{x.get('baseRent') or x.get('price') or '?':>6} EUR cold  "
          f"{x.get('totalRent') or '?':>6} EUR warm  {x.get('livingSpace') or '?':>5} m2  "
          f"{x.get('rooms') or '?'} rooms  {(x.get('address') or '')[:50]}")
