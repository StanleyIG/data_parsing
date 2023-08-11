from scrapy.utils.reactor import install_reactor
from scrapy.crawler import CrawlerProcess

from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from spiders.avito import AvitoSpider


if __name__ == '__main__':
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    configure_logging()
    process = CrawlerProcess(get_project_settings())
    process.crawl(AvitoSpider)
    process.start()