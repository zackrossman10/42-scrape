import scrapy, time
from datetime import datetime

class QuotesSpider(scrapy.Spider):
    name = "42floors"
    start_urls= [
        # "https://42floors.com/us/al"
        "https://42floors.com/markets/us"
    ]

    def parse(self, response):
        for href in response.css('.container h3 a::attr(href)'):
            yield response.follow(href, self.parse_market)

    def parse_market(self, response):
        time.sleep(2);
        for href in response.css('a.listing-row::attr(href)'):
            yield response.follow(href, self.parse_page)
        nextPage = response.css('ul.pagination a.next::attr(href)').extract_first()
        if(nextPage is not None):
            yield response.follow(nextPage, callback=self.parse_market)

    def parse_page(self, response):
        propInfo = {}
        #data pertaining to the overall property
        streetAddress = response.css('div.address meta[itemprop*="streetAddress"]::attr(content)').extract_first()
        locality = response.css('div.address meta[itemprop*="addressLocality"]::attr(content)').extract_first()
        state = response.css('div.address meta[itemprop*="addressRegion"]::attr(content)').extract_first()

        if(streetAddress is not None):
            propInfo['streetAddress'] = streetAddress.strip()
        if(locality is not None):
            propInfo['locality'] = locality.strip()
        if(state is not None):
            propInfo['state'] = state.strip()

        propertyDescription = ""
        propertyDescriptions = response.css('div.description p::text').extract()
        for text in propertyDescriptions:
            propertyDescription += text
        propInfo['propertyDescription'] = propertyDescription

        propertyFeatures = []
        propertyFeaturesSection = response.css('div.features div.margin-bottom')
        for propFeature in propertyFeaturesSection:
            #FIX TODO
            layer = propFeature.css('div div::text')
            icon = propFeature.css('div div span::attr("class")').extract()
            if(len(icon)>0):
                propertyFeatures.append(layer[0].extract().strip()+": "+icon[0])
            else:
                propertyFeatures.append(layer[0].extract().strip()+": "+ layer[1].extract().strip())
            propInfo['propertyFeatures'] = propertyFeatures

        #get data pertaining to a specific listing at property
        listings = response.css("div.uniformSection div.listing-card")
        listingArray = []
        for listing in listings:
            listingInfo = {}
            listingInfo['name'] = listing.css('div.grid-nest div.listing-name::text').extract_first().strip()
            listingInfo['size'] = listing.css('div.grid-nest div.listing-size::text').extract_first().strip()
            listingInfo['lastTouched'] = listing.css('div.grid-nest div.listing-touched_at::text').extract_first().strip()
            listingInfo['rate'] = listing.css('div.grid-nest div.listing-rate::text').extract_first().strip()
            typesArray = []
            types = listing.css('span[itemprop*="category"]::text').extract()
            for type in types:
                typesArray.append(type)
            listingInfo['type'] = typesArray

            mainFeatureList = {}
            mainFeatures = listing.css('div.features span')
            for x in range(0, len(mainFeatures), 2):
                text = mainFeatures.css('::text').extract()
                category = text[x]
                value = text[x+1]
                mainFeatureList[category] = value
            listingInfo['mainListingFeatures'] = mainFeatureList

            # otherFeatureList = {}
            # otherFeatures = mainFeatures.xpath('/following-sibling')
            # len(otherFeatures)
            # for x in range(0, len(features), 3):
            #     in = otherFeatures.css('span span::attr("category"').extract()
            #     icon = features.css('span::attr("class")').extract()[x]
            #     featuresList[category] = icon
            #
            # for x in featuresList:
            #     print x + featuresList[x]
            # listingInfo['otherListingFeatures'] = otherFeatureList

            description = ""
            descriptions = listing.css('div[itemprop*="description"] p::text').extract()
            for text in descriptions:
                description += ", "+text
            descriptions = listing.css('div[itemprop*="description"] li::text').extract()
            for text in descriptions:
                description += text+", "
            listingInfo['listingDescription'] = description

            agentInfo = listing.css('div[itemprop*="seller"] a::text').extract()
            listingInfo['lisitngAgent'] = agentInfo[0]
            listingInfo['listingCompany'] = agentInfo[1]

            photoList = []
            photos = listing.css('div.photos div[itemprop*="image"]::attr("data-lightbox")').extract()
            for photo in photos:
                photoList.append(photo)
            listingInfo['photos'] = photoList
            listingArray.append(listingInfo)

        propInfo['listings'] = listingArray

        #inlcude lisitng link and timestamp of scraping
        propInfo['listing_link'] = response.request.url
        timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.utcnow())
        propInfo['date_scraped'] = timestamp
        yield propInfo
