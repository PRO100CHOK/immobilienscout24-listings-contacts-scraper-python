"""Weekly ImmoScout24 rent snapshot per postcode in a Google Sheet.

Uses the cheap list-only mode (fetchDetails: false): price, size, rooms and
address per listing, enough to track cold rent per m2 by postcode over time.

Setup:
  1. Google Cloud console -> create a service account -> download its JSON key.
  2. Save it as service_account.json next to this file (it is gitignored).
  3. Share the spreadsheet with the service account's e-mail address.

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
import os
from datetime import datetime, timezone

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

SPREADSHEET = "ImmoScout24 rent tracker"
WORKSHEET = "rents"
POSTCODES = ["10115", "10437", "10999", "12043"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
    "locations": POSTCODES,
    "realEstateType": "apartmentrent",
    "fetchDetails": False,
    "extractEmails": False,
    "maxItems": 400,
})

header = ["snapshot", "id", "zipCode", "price_eur", "living_space_m2", "rooms",
          "eur_per_m2", "address", "published", "url"]
stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
rows = []
for x in client.dataset(run["defaultDatasetId"]).iterate_items():
    price, space = x.get("price"), x.get("livingSpace")
    ppm = round(price / space, 2) if price and space else ""
    rows.append([stamp, x.get("id"), x.get("zipCode"), price, space, x.get("rooms"), ppm,
                 x.get("address"), x.get("publishedAgo"), x.get("url")])

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
book = gspread.authorize(creds).open(SPREADSHEET)
try:
    ws = book.worksheet(WORKSHEET)
except gspread.WorksheetNotFound:
    ws = book.add_worksheet(WORKSHEET, rows=20000, cols=len(header))
    ws.append_row(header)

ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} listings to {SPREADSHEET}/{WORKSHEET}")
