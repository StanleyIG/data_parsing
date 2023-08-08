import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
# from spiders.hhrujob import HhrujobSpider раскоментировать если потребуется
from spiders.castorama import CastoramaSpider


if __name__ == '__main__':
    """Точка входа в программу."""
    install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
    """Устанавливает асинхронный реактор для работы сетевых запросов."""
    configure_logging()
    """Настройка логирования для Scrapy."""
    process = CrawlerProcess(get_project_settings())
    """Создание экземпляра класса CrawlerProcess с настройками проекта Scrapy."""
    # process.crawl(HhrujobSpider)
    # quary = input()
    process.crawl(CastoramaSpider, quary='чайник')
    """Добавление паука HhruSpider в процесс сканирования."""
    process.start()
    """Запуск процесса сканирования."""



    