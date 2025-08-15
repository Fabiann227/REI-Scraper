import scrapy

class ListingDetailItem(scrapy.Item):
    listing_id = scrapy.Field()
    url = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    multilingual = scrapy.Field()
    buildingFeature = scrapy.Field()
    listhubFeature = scrapy.Field()
    realtorFeatures = scrapy.Field()
    geoLocation = scrapy.Field()
    agent = scrapy.Field()
    description = scrapy.Field()
    publishedAt = scrapy.Field()
    updatedAt = scrapy.Field()
    agency = scrapy.Field()
    landSize = scrapy.Field()
    buildingSize = scrapy.Field()
