"""Energy-efficient flats for sale in Leipzig -> CSV with pandas.

Filters on the actor side (energy class A+ to B, 2-4 rooms), then computes the
purchase price per m2 and the full purchase-cost total (Kaufnebenkosten) in
pandas and writes output.csv, cheapest per m2 first.

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
import os

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
    "locations": ["Leipzig"],
    "realEstateType": "apartmentbuy",
    "energyEfficiencyClasses": ["a_plus", "a", "b"],
    "minRooms": 2,
    "maxRooms": 4,
    "fetchDetails": True,
    "extractEmails": False,
    "language": "en",
    "maxItems": 150,
})

items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
df = pd.json_normalize(items)

cols = ["id", "url", "title", "quarter", "zipCode", "purchasePrice", "livingSpace", "rooms",
        "yearConstructed", "energyEfficiencyClass", "buyerCommission",
        "purchaseCosts.totalCosts", "monthlyFinancingRate", "contactCompany"]
df = df[[c for c in cols if c in df.columns]]

if {"purchasePrice", "livingSpace"} <= set(df.columns):
    df["eur_per_m2"] = (df["purchasePrice"] / df["livingSpace"]).round(0)
    df = df.sort_values("eur_per_m2")

df.to_csv("output.csv", index=False, encoding="utf-8")
print(f"Wrote {len(df)} listings to output.csv")
print(df.head(10).to_string(index=False))
