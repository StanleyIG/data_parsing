import sys
import scrapy
from scrapy_selenium import SeleniumRequest
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
sys.path.append('./')
from items import AvitoparserItem
from pprint import pprint as pp
import time


class AvitoSpider(scrapy.Spider):
    name = "avito"
    allowed_domains = ["avito.ru"]
    start_urls = ["https://www.avito.ru/kazan?q=iphone+14"]
    wait_time = 10  # Дополнительная задержка в секундах

    def start_requests(self):
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse)

    def parse(self, response: HtmlResponse):
        links = response.xpath("//a[@data-marker='item-title']/@href").getall()
        for link in links:
            url = "https://avito.ru" + link
            yield SeleniumRequest(url=url, callback=self.parse_ads, wait_time=self.wait_time)

    def parse_ads(self, response: HtmlResponse):
        # print()
        loader = ItemLoader(item=AvitoparserItem(), response=response)
        loader.add_xpath('name', '//span[@data-marker="item-view/title-info"]//text()')
        loader.add_xpath('price', '//span[@data-marker="item-view/item-price"]//text()')
        loader.add_xpath('description', '//div[@data-marker="item-view/item-description"]//p//text()')
        loader.add_xpath('img', '//div[@data-marker="image-frame/image-wrapper"]/img/@src')
        loader.add_value('url', response.url)

