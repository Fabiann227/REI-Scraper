import scrapy
import json
import requests
from parsel import Selector
from ..items import ListingDetailItem

class PropertySpider(scrapy.Spider):
    name = "service"
    allowed_domains = ["www.realestate.com.au"]

    def __init__(self, country_code="id", max_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country_code = country_code
        self.max_pages = int(max_pages) if max_pages is not None else None

    def start_requests(self):
        base_url = f"https://www.realestate.com.au/international/{self.country_code}"
        self.logger.info(f"Starting spider for country code: {self.country_code} and max pages: {self.max_pages}")
        if self.max_pages is None:
            # If max_pages is None, we need to find the last page dynamically
            yield scrapy.Request(base_url, callback=self.parse_last_page)
        else:
            # If max_pages is specified, we can directly generate the URLs
            for page in range(1, self.max_pages + 1):
                url = base_url if page == 1 else f"{base_url}/p{page}"
                yield scrapy.Request(url, callback=self.parse_listing)

    def parse_last_page(self, response):
        page_numbers = response.css("ul.ant-pagination li[title]:not([title='Previous Page']):not([title='Next Page'])::attr(title)").getall()
        if page_numbers:
            last_page = int(page_numbers[-1])
        else:
            last_page = 1

        self.logger.info(f"Last page found: {last_page}")
        
        base_url = f"https://www.realestate.com.au/international/{self.country_code}"
        for page in range(1, last_page + 1):
            url = base_url if page == 1 else f"{base_url}/p{page}"
            yield scrapy.Request(url, callback=self.parse_listing)

    def parse_listing(self, response):
        links = response.xpath('//a[.//*[@data-testid="standard-listing-card"]]/@href').getall()
        for link in links:
            abs_url = response.urljoin(link)
            yield scrapy.Request(abs_url, callback=self.parse_detail)

    def parse_detail(self, response):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(response.url, headers=headers, timeout=30)
        sel = Selector(text=r.text)

        apollo = {}
        scripts = sel.css('script[type="application/json"]::text').getall()
        for s in scripts:
            try:
                data = json.loads(s.strip())
                apollo.update(self._find_apollo(data))
            except:
                continue

        next_data = sel.css('script#__NEXT_DATA__::text').get()
        if next_data:
            try:
                nd = json.loads(next_data.strip())
                apollo.update(self._find_apollo(nd))
            except:
                pass

        # Get listing_id from Apollo state
        listing_id = None
        for key, val in apollo.items():
            if key.startswith("ListingDetail:") and isinstance(val, dict) and "id" in val:
                listing_id = val["id"]
                break

        if not listing_id:
            return

        item = ListingDetailItem()
        item["listing_id"] = listing_id
        item["url"] = response.url

        main_key = f"ListingDetail:{listing_id}"
        main_data = self._resolve_refs(apollo.get(main_key, {}), apollo)

        # Get main data
        item["price"] = main_data.get("price")
        item["location"] = self._resolve_refs(main_data.get("location"), apollo)
        item["multilingual"] = self._resolve_refs(main_data.get("multilingual"), apollo)

        building_feature = self._resolve_refs(main_data.get("buildingFeature"), apollo) or {}
        item["buildingFeature"] = {
            "indoorFeature": self._resolve_refs(building_feature.get("indoorFeature"), apollo),
            "outdoorFeature": self._resolve_refs(building_feature.get("outdoorFeature"), apollo),
            "energyEfficiencyFeature": self._resolve_refs(building_feature.get("energyEfficiencyFeature"), apollo),
        }

        item["listhubFeature"] = self._resolve_refs(main_data.get("listhubFeature"), apollo)
        item["realtorFeatures"] = self._resolve_refs(main_data.get("realtorFeatures"), apollo)
        item["geoLocation"] = self._resolve_refs(main_data.get("geoLocation"), apollo)

        item["publishedAt"] = main_data.get("publishedAt")
        item["updatedAt"] = main_data.get("updatedAt")

        agency_data = self._resolve_refs(main_data.get("agency"), apollo)
        item["agency"] = agency_data if agency_data else None

        item["landSize"] = main_data.get('landSize({"language":"en","unit":"SQUARE_METERS"})')
        item["buildingSize"] = main_data.get('buildingSize({"language":"en","unit":"SQUARE_METERS"})')

        # Agent
        agent_id = None
        for k in apollo.keys():
            if k.startswith("Agent:"):
                agent_id = k.split(":")[1]
                break
        if agent_id:
            agent_key = f"Agent:{agent_id}"
            agent_data = self._resolve_refs(apollo.get(agent_key, {}), apollo)
            item["agent"] = agent_data
        
        # Basic fields
        if not item["price"]:
            item["price"] = sel.css(".property-price::text").get()

        if not item["location"]:
            item["location"] = sel.css(".display-address::text").get()

        if not main_data.get("description"):
            item["description"] = " ".join(sel.css(".property-description *::text").getall()).strip()

        yield item


    def _find_apollo(self, obj):
        apollo_state = {}
        if isinstance(obj, dict):
            if "apolloState" in obj and isinstance(obj["apolloState"], dict):
                apollo_state.update(obj["apolloState"])
            for v in obj.values():
                apollo_state.update(self._find_apollo(v))
        elif isinstance(obj, list):
            for it in obj:
                apollo_state.update(self._find_apollo(it))
        return apollo_state

    def _resolve_refs(self, obj, apollo):
        if isinstance(obj, dict):
            if "id" in obj and obj["id"] in apollo:
                return self._resolve_refs(apollo[obj["id"]], apollo)
            return {k: self._resolve_refs(v, apollo) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_refs(v, apollo) for v in obj]
        return obj