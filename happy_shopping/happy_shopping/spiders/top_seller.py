import scrapy
import json
from ..items import TopSellerItem


class NoonSpider(scrapy.Spider):
    url = 'https://www.noon.com/uae-en/p-14890'
    last_page = 10
    starting_page = 1
    limit = 200

    name = "top_seller"
    pre = 'https://www.noon.com/_svc/catalog/api/u/'
    start_urls = [
        f"{url}?&limit={limit}&page={starting_page}"
    ]

    def parse(self, response):
        for link in response.xpath("//div[contains(@class,'productContainer')]/a/@href").extract():
            product_url = f"{self.pre}{link}"
            yield response.follow(product_url, callback=self.parse_product)

        self.starting_page += 1
        next_page = f'{self.url}?&limit={self.limit}&page={self.starting_page}'
        if self.starting_page <= self.last_page:
            yield scrapy.Request(url=next_page, callback=self.parse)

    def parse_product(self, response):
        items = TopSellerItem()
        data = json.loads(response.body)['product']
        sale_price = data['variants'][0]['offers'][0]['sale_price']
        regular_price = data['variants'][0]['offers'][0]['price']

        if data['variants'][0]['offers'][0]['is_fbn'] == 1:
            items['Express_or_Market'] = 'Express'
        else:
            items['Express_or_Market'] = 'Market'

        if sale_price:
            items['BuyBox_Seller_Offer'] = sale_price
        else:
            items['BuyBox_Seller_Offer'] = regular_price

        for offer in data['variants'][0]['offers']:
            if offer['store_name'] == 'Happy.Shopping':
                if offer['sale_price']:
                    items['Our_Offer'] = offer['sale_price']
                else:
                    items['Our_Offer'] = offer['price']

        try:
            for spec in data['specifications']:
                if spec['code'] == 'model_number':
                    items['Model_Number'] = spec['value']
        except UnboundLocalError:
            items['Model_Number'] = ''

        try:
            if data['variants'][0]['offers'][1]['sale_price']:
                items['Difference_with_Other_Offer'] = data['variants'][0]['offers'][1]['sale_price'] - items['Our_Offer']
            else:
                items['Difference_with_Other_Offer'] = data['variants'][0]['offers'][1]['price'] - items['Our_Offer']
        except IndexError:
            items['Difference_with_Other_Offer'] = ''

        items['SKU'] = data['sku']
        items['Title'] = data['product_title']
        items['First_Image_Link'] = f'https://k.nooncdn.com/t_desktop-pdp-v1/{data["image_keys"][0]}.jpg'
        items['BuyBox_Seller_Store_Name'] = data['variants'][0]['offers'][0]['store_name']
        items['Difference_with_BuyBox_Seller'] = items['BuyBox_Seller_Offer'] - items['Our_Offer']

        yield items
