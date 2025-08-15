# Real Estate International Property Scraper

This Scrapy spider scrapes property listings from the [realestate.com.au](https://www.realestate.com.au) **International** section for a given country.

It extracts data directly from the embedded Apollo GraphQL state in the HTML to retrieve complete and structured property details, with a fallback to HTML selectors when certain fields are missing.
The scraper supports selecting a target country, setting the number of pages to scrape, or running in automatic mode to fetch all available listing pages.

## How It Works

The spider:
1. Starts from a country-specific listing page (e.g., `/international/id` for Indonesia).
2. **If `max_pages` is provided**, it scrapes that number of pages.
3. **If `max_pages` is omitted**, it automatically detects the **last page** from the site's pagination and scrapes all pages up to that number.
4. Extracts individual property links from each listing page.
5. Visits each property detail page.
6. Extracts structured property data from embedded Apollo GraphQL state (`apolloState`) in the HTML.
7. Falls back to CSS selectors if some data is missing from Apollo state.

## Command Usage

```bash
scrapy crawl service -a country_code=sa -a max_pages=1
```

### Parameters (`-a`)

Scrapy's `-a` flag allows passing **spider arguments** at runtime:

- **`country_code`** — The country code for the property listings you want to scrape.  
  Examples:
  - `id` → Indonesia
  - `sa` → Saudi Arabia
  Default: `"id"`

- **`max_pages`** — (Optional) The maximum number of listing pages to crawl.
  - If provided, only that many pages will be scraped. 
  - If omitted, the spider automatically finds the last page number from the site's pagination and scrapes all pages.
  - Example: `max_pages=3` means page 1, page 2, and page 3 will be scraped.

## Example Commands

Scrape **1 page** of listings for **Saudi Arabia**:
```bash
scrapy crawl service -a country_code=sa -a max_pages=1
```

Scrape **all pages** for **Indonesia**:
```bash
scrapy crawl service -a country_code=id
```

## Data Extraction Details

The spider extracts the following fields: [sample data](./realestate_international/realestate_international/data/310096794391.json)

| Field              | Description |
|--------------------|-------------|
| `listing_id`       | Unique ID of the property listing |
| `url`              | Property page URL |
| `price`            | Property price |
| `location`         | Location data object |
| `multilingual`     | Multilingual descriptions if available |
| `buildingFeature`  | Dictionary containing `indoorFeature`, `outdoorFeature`, `energyEfficiencyFeature` |
| `listhubFeature`   | Listhub features object |
| `realtorFeatures`  | Realtor features object |
| `geoLocation`      | Latitude & longitude |
| `description`      | Property description (fallback to HTML if Apollo missing) |
| `publishedAt`      | Date the listing was published |
| `updatedAt`        | Date the listing was last updated |
| `agency`           | Agency information |
| `landSize`         | Land size in square meters |
| `buildingSize`     | Building size in square meters |
| `agent`            | Agent information |

## Implementation Details

- **`_find_apollo()`** recursively searches JSON structures in `<script>` tags for `apolloState` objects.
- **`_resolve_refs()`** resolves GraphQL object references using their `id` fields.
- Falls back to CSS selectors (`.property-price`, `.display-address`, `.property-description`) if Apollo data is incomplete.

## Requirements

- Python 3.8+
- Scrapy
- Requests

Install dependencies:
```bash
pip install scrapy requests
```

## Notes

- This spider accesses public data and respects the target website's `robots.txt` and terms of service.