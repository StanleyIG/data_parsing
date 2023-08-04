import sys
import scrapy
from scrapy.http import HtmlResponse
sys.path.append('./')
from items import JobparserHhruItem
from pprint import pprint as pp



class HhrujobSpider(scrapy.Spider):
    name = "hhrujob"
    allowed_domains = ["hh.ru"]
    start_urls = ["https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text=python&excluded_text=&area=88&salary=&'\
            'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'",
                  "https://kazan.hh.ru/search/vacancy?area=2&metro=16.604&metro=14.203&metro=14.206&metro=18.258&metro=14.192&\
                metro=14.196&metro=15.216&metro=17&metro=14.198&metro=18.248&metro=15.222&metro=15.214&search_field=name&\
                    search_field=company_name&search_field=description&enable_snippets=false&\
                        salary=120000&text=python&no_magic=true&L_save_area=true&items_on_page=20"]

    def parse(self, response: HtmlResponse):
        links = response.xpath('//a[@class="serp-item__title"]/@href').getall()
        next_page = response.xpath('//a[@data-qa="pager-next"]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        for link in links:
            yield response.follow(link, callback=self.vacancy_parse)

    def vacancy_parse(self, response: HtmlResponse):
        name = response.xpath('//h1/text()').get()
        salary = response.xpath(
            '//div[@data-qa="vacancy-salary"]/span//text()').getall()
        url = response.url
        yield JobparserHhruItem(name=name, salary=salary, url=url)
