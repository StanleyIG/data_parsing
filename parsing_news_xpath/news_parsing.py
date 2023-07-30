import json
import requests
from bs4 import BeautifulSoup as bs
import os
from databasesql import Model
from datetime import datetime
from pymongo import MongoClient
from pprint import pprint as pp
from lxml import html


class Base(Model):
    def __init__(self, news_service):
        super().__init__()
        self.news_service = news_service
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36'
        }
        self._session = requests.Session()
        self.service_init()

    """получает статус код"""

    def get_status_code(self, url):
        response = self._session.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False

    def service_init(self):
        if self.news_service.lower().startswith('mail'):
            self.method = self.news_mail
        elif self.news_service.lower().startswith('lenta'):
            self.method = self.news_lenta

    def news_lenta(self):
        top_news_lst = []
        url = 'https://lenta.ru/'
        status = self.get_status_code(url)
        if not status:
            return {'vacancies': None, 'status_ok': self.get_status_code()}
        response = self._session.get(url, headers=self.headers)
        root = html.fromstring(response.text)
        mini_top_news = root.xpath(
            '//div[@class="main-page"]//a[@class="card-mini _topnews"]')
        # главная топ новость в верхушке сайта
        big_top_news = root.xpath(
            '//div[@class="main-page"]//a[@class="card-big _topnews _news"]')
        big_title = big_top_news[0].xpath('.//h3[@class="card-big__title"]')
        big_link = big_top_news[0].get('href')
        publication_time = big_top_news[0].xpath(
            './/time[@class="card-big__date"]')
        big_date = datetime.now().strftime("%d.%m.%Y")
        top_news_lst.append({'news_service': url,
                             'title': big_title[0].text.strip() if big_title else None,
                             'link': url + big_link,
                             'publication_time': publication_time[0].text.strip() if publication_time else None,
                             'date': big_date
                             })

        # главные мини новости
        for link in mini_top_news:
            dct = {}
            href = link.get('href')
            dct['news_service'] = url
            title = link.xpath('.//h3[@class="card-mini__title"]')
            dct['title'] = title[0].text.strip() if title else None
            dct['link'] = href if href.startswith('https') else url + href
            time = link.xpath('.//time[@class="card-mini__info-item"]')
            dct['publication_time'] = time[0].text.strip() if time else None
            date = datetime.now().strftime("%d.%m.%Y")
            dct['date'] = date
            top_news_lst.append(dct)

        # длинная сетка новостей
        longgrid_mini_news = root.xpath(
            '//div[@class="longgrid-feature-list"]//a[@class="card-mini _longgrid"]')
        for news in longgrid_mini_news:
            dct = {}
            href = news.get('href')
            dct['news_service'] = url
            title = news.xpath('.//h3[@class="card-mini__title"]')
            dct['title'] = title[0].text.strip() if title else None
            dct['link'] = href if href.startswith('https') else url + href
            time = news.xpath('.//time[@class="card-mini__info-item"]')
            dct['publication_time'] = time[0].text.strip() if time else None
            dct['date'] = datetime.now().strftime("%d.%m.%Y")
            top_news_lst.append(dct)
        return top_news_lst

    def news_mail(self):
        news_lst = []
        url = 'https://news.mail.ru/'
        status = self.get_status_code(url)
        if not status:
            return {'vacancies': None, 'status_ok': self.get_status_code()}
        response = self._session.get(url, headers=self.headers)
        root = html.fromstring(response.text)
        # новости в верхней части сайта, главные новости
        main_news = root.xpath(
            '//div[@class="cols cols_margin cols_percent"]//a[@class="newsitem__title link-holder"]')
        for news in main_news:
            dct = {}
            title = news.xpath('.//span[@class="newsitem__title-inner"]')
            href = news.get('href')
            dct['news_service'] = url
            dct['title'] = title[0].text.strip() if title else None
            dct['link'] = href if href.startswith('https') else url + href
            dct['date'] = datetime.now().strftime("%d.%m.%Y")
            news_lst.append(dct)
        return news_lst

    def write_json(self):
        if self.method.__name__ == 'news_lenta':
            FILENAME = 'parsing_news_xpath/lenta_news.json'
        else:
            FILENAME = 'parsing_news_xpath/mail_news.json'
        with open(FILENAME, 'w', encoding='utf-8') as file:
            json.dump(self.method(), file,
                      ensure_ascii=False, indent=4)
            

    def add_to_mongodb(self):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['database']
        if self.method.__name__ == 'news_lenta':
            new_news = self.method()    
            db_news = db['lenta_news']
        else:
            new_news = self.method()
            db_news = db['mail_news']
        for news in new_news:
            if db_news.find_one({'link': news['link']}) is None:
                db_news.insert_one(news)
        return db_news
            

    def sql_add_news(self):
        if self.method.__name__ == 'news_lenta':
            method_name = 'news_lenta'
            FILENAME = 'parsing_news_xpath/lenta_news.json'
        else:
            method_name = 'news_mail'
            FILENAME = 'parsing_news_xpath/mail_news.json'
        if os.path.exists(FILENAME):
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            self.write_json()
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
        return super().sql_add_news(data, method_name)


news = Base('mail')
#news.sql_add_news()
pp(news.sql_get_news())
#news.add_to_mongodb()

