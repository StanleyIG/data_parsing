from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import json
from pprint import pprint as pp


class Model:
    class LentaNews:
        def __init__(self, news_service, title, link, publication_time):
            self.news_service = news_service
            self.title = title
            self.link = link
            self.publication_time = publication_time
            self.date = datetime.datetime.now()
            self.id = None

    class MailNews:
        def __init__(self, news_service, title, link):
            self.news_service = news_service
            self.title = title
            self.link = link
            self.date = datetime.datetime.now()
            self.id = None

    def __init__(self):
        self.database_engine = create_engine(
            'sqlite:///parsing_news_xpath/news.db3', echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        lenta_news = Table('lenta_news', self.metadata,
                           Column('id', Integer, primary_key=True),
                           Column('news_service', String),
                           Column('title', String),
                           Column('link', String, unique=True),
                           Column('publication_time', String),
                           Column('date', DateTime)
                           )

        mail_news = Table('mail_news', self.metadata,
                          Column('id', Integer, primary_key=True),
                          Column('news_service', String),
                          Column('title', String),
                          Column('link', String, unique=True),
                          Column('date', DateTime)
                          )

        self.metadata.create_all(self.database_engine)
        mapper(self.LentaNews, lenta_news)
        mapper(self.MailNews, mail_news)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

    def sql_add_news(self, method, method_name):
        """метод проверяет наличие новостей в базе по ссылке, если записей нет, то добавляет новые"""
        if method_name == 'news_lenta':
            for i in method:
                news = self.session.query(
                    self.LentaNews).filter_by(link=i['link'])
                if news.count():
                    return
                else:
                    news = self.LentaNews(
                        i['news_service'], i['title'], i['link'], i['publication_time'])
                    self.session.add(news)
                    self.session.commit()
        else:
            for i in method:
                news = self.session.query(
                    self.MailNews).filter_by(link=i['link'])
                if news.count():
                    return
                else:
                    news = self.MailNews(
                        i['news_service'], i['title'], i['link'])
                    self.session.add(news)
                    self.session.commit()

    def sql_get_news(self):
        """возвращает все новости"""
        lenta_news = self.session.query(self.LentaNews.id,
                                              self.LentaNews.title,
                                              self.LentaNews.link,
                                              self.LentaNews.date)

        mail_news = self.session.query(self.MailNews.id,
                                             self.MailNews.title,
                                             self.MailNews.link,
                                             self.MailNews.date)
        
        all_news_query = lenta_news.union(mail_news)
        all_news = all_news_query.all()
        return all_news
