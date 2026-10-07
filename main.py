"""ImmobilienScout24 scraper — Berlin rent map + estate agent lead list.

Use case: a relocation agency wants two things from one run of fresh Berlin
rental listings on immobilienscout24.de:

  1. a rent benchmark: median cold rent (Kaltmiete) per m² for each district
     (quarter), plus the typical service charge (Nebenkosten);
  2. a de-duplicated lead list of the agencies (Makler) behind those listings,
     with phone numbers, Impressum e-mails and e-mails found on their website.

Outputs: output.json / output.csv (one row per listing) and agencies.csv.

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python main.py

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/immobilienscout24-scraper"
LOCATIONS = ["Berlin"]
MAX_LISTINGS = 200          # keep the first run cheap; raise it once you like the output
MIN_LISTINGS_PER_QUARTER = 3

LISTING_FIELDS = [
    "id", "url", "title", "quarter", "zipCode", "city", "baseRent", "totalRent",
    "serviceCharge", "deposit", "livingSpace", "rooms", "floor", "yearConstructed",
    "energyEfficiencyClass", "balcony", "builtInKitchen", "availableFrom",
    "privateOffer", "contactCompany", "contactPhone", "contactEmail", "lat", "lng",
]
AGENCY_FIELDS = ["company", "listings", "phones", "emails", "website", "linkedin", "profile"]


def scrape(client: ApifyClient) -> list[dict]:
    run = client.actor(ACTOR_ID).call(
        run_input={
            "locations": LOCATIONS,
            "realEstateType": "apartmentrent",
            "sorting": "-firstactivation",     # newest first
            "excludeSwapFlats": True,
            "fetchDetails": True,              # costs, Impressum, phones
            "extractEmails": True,             # visit agency websites for e-mails
            "language": "en",
            "maxItems": MAX_LISTINGS,
        },
        timeout_secs=3600,
    )
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def rent_per_sqm(item: dict) -> float | None:
    rent, space = item.get("baseRent"), item.get("livingSpace")
    if rent and space:
        return float(rent) / float(space)
    return None


def build_agencies(items: list[dict]) -> list[dict]:
    agencies: dict[str, dict] = {}
    for it in items:
        if it.get("privateOffer"):
            continue
        company = (it.get("contactCompany") or "").strip()
        if not company:
            continue
        a = agencies.setdefault(company, {
            "company": company, "listings": 0, "phones": set(), "emails": set(),
            "website": "", "linkedin": "", "profile": "",
        })
        a["listings"] += 1
        a["phones"].update(it.get("contactPhones") or [])
        a["phones"].update(it.get("imprintPhones") or [])
        a["emails"].update(it.get("emails") or [])
        a["emails"].update(it.get("imprintEmails") or [])
        a["website"] = a["website"] or it.get("agencyWebsite") or ""
        a["profile"] = a["profile"] or it.get("agentProfileUrl") or ""
        social = it.get("socialLinks") or {}
        if isinstance(social, dict):
            a["linkedin"] = a["linkedin"] or social.get("linkedin") or ""
    rows = []
    for a in sorted(agencies.values(), key=lambda x: -x["listings"]):
        rows.append({**a, "phones": "; ".join(sorted(map(str, a["phones"]))),
                     "emails": "; ".join(sorted(a["emails"]))})
    return rows


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing — copy .env.example to .env and paste your token.")

    client = ApifyClient(token)
    print(f"Scraping up to {MAX_LISTINGS} rental flats in {', '.join(LOCATIONS)} ...")
    try:
        items = scrape(client)
    except ApifyApiError as exc:
        sys.exit(f"Actor run failed: {exc}")
    if not items:
        sys.exit("No listings returned.")
    print(f"  {len(items)} listings")

    out = Path(__file__).parent
    (out / "output.json").write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "output.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LISTING_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(items)

    # 1) Rent benchmark per quarter
    per_quarter: dict[str, list[float]] = defaultdict(list)
    service: dict[str, list[float]] = defaultdict(list)
    for it in items:
        ppm = rent_per_sqm(it)
        q = it.get("quarter") or it.get("district")
        if ppm and q:
            per_quarter[q].append(ppm)
            if it.get("serviceCharge"):
                service[q].append(float(it["serviceCharge"]))

    print("\nMedian cold rent per m² by quarter")
    table = [(q, statistics.median(v), len(v)) for q, v in per_quarter.items()
             if len(v) >= MIN_LISTINGS_PER_QUARTER]
    for q, med, n in sorted(table, key=lambda t: -t[1]):
        nk = statistics.median(service[q]) if service[q] else None
        nk_txt = f"Nebenkosten ~{nk:,.0f} €" if nk else ""
        print(f"  {med:>6.2f} €/m²  {q[:30]:<30} ({n:>3} flats)  {nk_txt}")

    # 2) Agency lead list
    agencies = build_agencies(items)
    with (out / "agencies.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=AGENCY_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(agencies)

    with_email = sum(1 for a in agencies if a["emails"])
    with_phone = sum(1 for a in agencies if a["phones"])
    print(f"\n{len(agencies)} agencies — {with_email} with e-mail, {with_phone} with phone")
    for a in agencies[:10]:
        print(f"  {a['listings']:>3}×  {a['company'][:40]:<40} {a['emails'][:50]}")

    print("\nSaved output.json, output.csv and agencies.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
