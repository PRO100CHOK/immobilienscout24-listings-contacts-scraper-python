# ImmobilienScout24 Listings & Agent Contacts Scraper in Python

> Export immobilienscout24.de rentals and sales to Python: Kaltmiete, Warmmiete, Nebenkosten, Kaution, Energieausweis, GPS, plus agent phones, Impressum and agency e-mails.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue)](https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Working Python examples for the [ImmobilienScout24 Scraper actor on Apify](https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python). Give it a city, a postcode or a search URL copied from your browser and you get **130+ fields per listing** back, including the contact details of the advertiser.

## What this does

ImmobilienScout24 (ImmoScout24) is Germany's largest property portal. Its official APIs are meant for estate agents managing their *own* listings. They do not give you search results across the market. If you need market data, there is no public endpoint for it.

This project uses a hosted scraper as an **unofficial ImmobilienScout24 API**. It handles German residential proxies, retries, pagination and de-duplication, and returns one clean row per listing (Exposé). Empty fields are dropped, so you don't get columns full of `null`.

Three ways to tell it what to scrape:

| Input | Example | Result |
|---|---|---|
| `locations` + `realEstateType` + filters | `["München Schwabing"]`, `apartmentrent` | All matching listings, no browser needed |
| `startUrls` with a search URL | `.../Suche/de/berlin/berlin/wohnung-mieten?price=-1500` | Every page of that search, all filters kept |
| `startUrls` with a listing URL | `https://www.immobilienscout24.de/expose/170528322` | That listing with full details |

All **19 property types** are available: apartments and houses to rent or buy, WG rooms (flatshares), furnished temporary living, plots, garages, offices and practices, retail, hospitality, halls and production, special commercial, commercial plots, investment properties, foreclosure auctions (Zwangsversteigerung), prefab houses and assisted living.

## Use cases

- **Rent benchmarks (Mietspiegel-style)** — median Kaltmiete per m² by district or postcode, which is exactly what `main.py` builds for Berlin.
- **Estate agent lead generation** — de-duplicated Makler lists with phones, Impressum e-mails and e-mails found on the agency website, ready for a CRM.
- **Investment screening** — `annualRentalIncome` and `priceToRentRatio` (x-fache Miete) on investment properties, and `marketValue` / `minimumBid` on foreclosure auctions.
- **Buy-side cost modelling** — `purchaseCosts` splits out land transfer tax, notary, land registry and broker commission, and `monthlyFinancingRate` is included where the listing shows it.
- **Relocation and student housing** — WG rooms and furnished temporary flats with rent, size, availability date and photos.
- **Energy and ESG analysis** — `energyEfficiencyClass`, `energyDemand`, `heatingType` and `energySources` across a whole city.
- **Commercial real estate scouting** — offices, retail units and halls with floor space, rent and broker contact.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up) — the monthly $5 credit covers a few thousand list-only rows to test with
- No ImmobilienScout24 account, login or API key

## Quick start

```bash
git clone https://github.com/pro100chok/immobilienscout24-listings-contacts-scraper-python.git
cd immobilienscout24-listings-contacts-scraper-python
pip install -r requirements.txt
cp .env.example .env
# paste your APIFY_API_TOKEN into .env
python main.py
```

`main.py` scrapes the 200 newest rental flats in Berlin (flat-swap offers excluded) with full details and agency e-mail lookup. It prints the median cold rent per m² and the typical Nebenkosten for each quarter. It also writes `agencies.csv`, with one row per agency: listing count, phones, e-mails, website and LinkedIn page if one was found. Raw rows go to `output.json` and `output.csv`.

The smallest possible call:

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_API_TOKEN")
run = client.actor("pro100chok/immobilienscout24-scraper").call(run_input={
    "locations": ["10115"],
    "realEstateType": "apartmentrent",
    "maxItems": 20,
})
for row in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(row.get("baseRent"), row.get("livingSpace"), row.get("url"))
```

## How it works

1. **Location lookup.** Free text such as `Köln Ehrenfeld` or `80331` is resolved through ImmoScout24's own location autocomplete. Search URLs are translated directly, including radius searches, sorting and filter parameters.
2. **Result pages.** Every page of the search is followed and duplicates are removed. Rows stream into the dataset, so a stopped run keeps what it already collected.
3. **Full details** (`fetchDetails`, on by default). Each Exposé is opened for all cost lines, the energy certificate, features, photos, floor plans, videos, 3D tours, the full address with coordinates, and the contact block with phone and Impressum.
4. **Agency e-mails** (`extractEmails`, on by default). When the advertiser links a website, the actor checks its homepage, Impressum and Kontakt pages for e-mail addresses and social profiles (LinkedIn, Facebook, Instagram, XING, YouTube). Each website is visited once per run, however many listings that agency has.
5. **List-only mode.** Turn `fetchDetails` off for a fast scan of price, size, rooms, address and photo at a lower price per row.

## Example output

A rental flat with full details (shortened, from the actor's documentation):

```json
{
  "id": "170528322",
  "url": "https://www.immobilienscout24.de/expose/170528322",
  "realEstateType": "apartmentrent",
  "baseRent": 1355,
  "totalRent": 1460,
  "serviceCharge": 105,
  "deposit": 4065,
  "livingSpace": 27.04,
  "rooms": 1,
  "floor": 6,
  "yearConstructed": 2026,
  "energyEfficiencyClass": "A+",
  "balcony": true,
  "builtInKitchen": true,
  "zipCode": "10243",
  "city": "Berlin",
  "quarter": "Friedrichshain",
  "lat": 52.5089,
  "lng": 13.44967,
  "contactName": "Herr Adem Dauti",
  "contactCompany": "Livory Development GmbH",
  "imprintPhones": ["030 3199870"],
  "agencyWebsite": "https://livory-group.de/",
  "contactEmail": "letting@livory-group.de",
  "emails": ["letting@livory-group.de", "berlin@livory-group.de"],
  "privateOffer": false
}
```

The dataset has three table views in the Apify Console: **Overview**, **Contacts** and **Property details**.

## German terms → output fields

| On the site | Field |
|---|---|
| Kaltmiete / Warmmiete | `baseRent` / `totalRent` |
| Nebenkosten / Heizkosten | `serviceCharge` / `heatingCosts` |
| Kaution | `deposit`, `depositMonths`, `depositText` |
| Kaufpreis / Provision | `purchasePrice` / `buyerCommission`, `tenantCommission` |
| Wohnfläche / Grundstück | `livingSpace` / `plotArea` |
| Baujahr / Energieausweis | `yearConstructed` / `energyCertificateType`, `energyEfficiencyClass` |
| Impressum | `imprint`, `imprintEmails`, `imprintPhones` |

## Input parameters

| Key | Description |
|---|---|
| `startUrls` | Search URLs and/or listing URLs (`/expose/<id>`) |
| `locations` | Cities, districts or postcodes |
| `realEstateType` | One of 19 types, e.g. `apartmentrent`, `apartmentbuy`, `housebuy`, `flatshareroom`, `office`, `investment`, `compulsoryauction` |
| `maxItems` | Maximum listings across all searches (default 100) |
| `fetchDetails` | Full listing details (default `true`) |
| `extractEmails` | Collect e-mails from agency websites (default `true`) |
| `language` | `de` or `en` labels |
| `minPrice` / `maxPrice` | Price or cold rent in EUR (Locations only) |
| `minRooms` / `maxRooms` | Room count |
| `minLivingSpace` / `maxLivingSpace` | Living space in m² |
| `minPlotArea` / `maxPlotArea` | Plot size in m² |
| `minConstructionYear` / `maxConstructionYear` | Year built |
| `equipment` | `balcony`, `builtinkitchen`, `garden`, `lift`, `cellar`, `guesttoilet`, `parking`, `handicappedaccessible` |
| `energyEfficiencyClasses` | `a_plus`, `a`, `b` … `h` |
| `newBuildOnly` / `excludeSwapFlats` | New builds only / hide Tauschwohnung offers |
| `sorting` | `standard`, `-firstactivation` (newest), `price`, `-price`, `livingspace`, `-livingspace` |

## More examples

| File | What it shows |
|---|---|
| [`examples/01_basic_usage.py`](examples/01_basic_usage.py) | 25 newest rentals in Hamburg, cold vs warm rent |
| [`examples/02_search_url_with_filters.py`](examples/02_search_url_with_filters.py) | Paste Cologne and Munich search URLs with their filters |
| [`examples/03_agent_emails_phones.py`](examples/03_agent_emails_phones.py) | One contact card per Stuttgart estate agency |
| [`examples/04_export_to_csv.py`](examples/04_export_to_csv.py) | Energy class A+–B flats in Leipzig, € per m² in pandas |
| [`examples/05_export_to_google_sheets.py`](examples/05_export_to_google_sheets.py) | Weekly list-only rent snapshot per Berlin postcode |

## Pricing

Pay per result, with proxies included:

- **Listing with full details:** $1.10 per 1,000 on the free plan, down to $0.80 on higher plans
- **List-only listing** (`fetchDetails: false`): $0.50 per 1,000, down to $0.35
- **Agency e-mails:** charged once per agency website per run, and only when e-mails were found ($3.00 per 1,000 websites on the free plan, down to $2.20)

There is also a tiny per-run start fee. See the [actor page](https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) for current prices.

## FAQ

**Is there an official ImmobilienScout24 API for search results?**
Not for market-wide searches. The official APIs are for agents publishing their own listings. This actor reads the public portal and returns structured data, with no login or API key.

**Why do some rows have no phone or e-mail?**
Private landlords and advertisers who only accept messages through the portal don't publish contact data. Those rows still have the contact name. `privateOffer` tells you whether a listing is from a private seller or an agent (Makler).

**Do my website filters carry over when I paste a URL?**
Yes. Price, rooms, space, features, energy class, new-build flag, radius and sorting are all read from the URL.

**Can I get English labels?**
Set `language: "en"`. Labels in `criteria` and values like condition and heating type come back in English. Listing descriptions stay in the language the advertiser used.

**How do I keep costs down while testing?**
Use a small `maxItems`, turn off `extractEmails`, and use list-only mode (`fetchDetails: false`) if price, size, rooms and address are enough.

**Can I schedule it?**
Yes. Use an Apify schedule, or run any script here from cron. `examples/05_export_to_google_sheets.py` is designed to be run once a week.

## Related actors

More real estate and lead-gen scrapers from the same developer:

- [Idealista Scraper](https://apify.com/pro100chok/idealista-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) — property listings and agencies in Spain, Italy and Portugal
- [Zillow Scraper](https://apify.com/pro100chok/zillow-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) — US listings, Zestimate and agent leads
- [Realtor.com Scraper](https://apify.com/pro100chok/realtor-com-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) — US property data and agents
- [Website Contact Scraper](https://apify.com/pro100chok/extract-emails?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) — bulk e-mails, phones and social links from any list of agency websites
- [Google Maps Scraper](https://apify.com/pro100chok/google-maps-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python) — every Immobilienmakler in a city with reviews and contacts

## License

MIT — see [LICENSE](LICENSE).

---

Built by [pro100chok](https://apify.com/pro100chok/immobilienscout24-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=immobilienscout24-listings-contacts-scraper-python). Not affiliated with ImmobilienScout24 / Scout24 SE.
