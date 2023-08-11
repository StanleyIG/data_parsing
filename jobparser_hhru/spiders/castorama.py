import sys
import scrapy
from scrapy.http import HtmlResponse
sys.path.append('./')
from items import CastoramaGoodsItem
from scrapy.loader import ItemLoader
from pprint import pprint as pp



class CastoramaSpider(scrapy.Spider):
    name = "castorama"
    allowed_domains = ["castorama.ru"]

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.start_urls = [f"https://www.castorama.ru/catalogsearch/result/?q={kwargs.get('quary')}"]
        

    def parse(self, response: HtmlResponse):
        next_page = response.xpath('//a[@class="next i-next"]/@href').get()
        print()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        links = response.xpath('//a[@class="product-card__img-link"]')
        if links:
            for link in links:
                yield response.follow(link, callback=self.parse_goods)
    
    def parse_goods(self, response: HtmlResponse):
        
        loader = ItemLoader(item=CastoramaGoodsItem(), response=response)
        loader.add_xpath('name', '//h1[@class="product-essential__name hide-max-small"]//text()')
        loader.add_xpath('price', '//span[@class="price"]//span/span/text()')
        loader.add_xpath('currency', '//span[@class="price"]//span[@class="currency"]//text()')
        loader.add_xpath('img', '//div[@class="js-zoom-container"]\
                             //img[contains(@class, "top-slide__img")]/@data-src')
        loader.add_value('url', response.url)

        yield loader.load_item()


        # name = response.xpath('//h1[@class="product-essential__name hide-max-small"]//text()').get()
        # price = response.xpath('//span[@class="price"]//span/span/text()').get()
        # currency = response.xpath('//span[@class="price"]//span[@class="currency"]//text()').get()
        # img = response.xpath('//div[@class="js-zoom-container"]\
        #                     //img[contains(@class, "top-slide__img")]/@data-src').getall()
        # url = response.url
        
        # yield CastoramaGoodsItem(name=name,
        #                         price=price,
        #                         currency=currency,
        #                         img=img,
        #                         url=url)
        
    
        
    

