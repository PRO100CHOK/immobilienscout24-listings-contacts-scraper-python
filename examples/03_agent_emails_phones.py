"""Estate agent (Makler) contacts from ImmobilienScout24 houses for sale.

With fetchDetails + extractEmails the actor returns, per listing: contact
person, company, phone numbers, the Impressum with its e-mails and phones,
the agency website and the e-mails / social profiles found on that website.
Each agency website is visited once per run.

Actor: https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
    "locations": ["Stuttgart"],
    "realEstateType": "housebuy",
    "fetchDetails": True,
    "extractEmails": True,
    "maxItems": 50,
})

seen = set()
for x in client.dataset(run["defaultDatasetId"]).iterate_items():
    company = x.get("contactCompany")
    if x.get("privateOffer") or not company or company in seen:
        continue
    seen.add(company)
    phones = sorted(set((x.get("contactPhones") or []) + (x.get("imprintPhones") or [])))
    print(company)
    print(f"  contact : {x.get('contactName') or '-'}")
    print(f"  phones  : {', '.join(map(str, phones)) or '-'}")
    print(f"  e-mails : {', '.join(x.get('emails') or []) or '-'}")
    print(f"  website : {x.get('agencyWebsite') or '-'}")
    print(f"  social  : {', '.join((x.get('socialLinks') or {}).values()) or '-'}")
