from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import json
from pprint import pprint as pp



class Model:
    class HHruVacancies:
        def __init__(self, name, salary_min, salary_max, currency, link):
            self.name = name
            self.salary_min = salary_min
            self.salary_max = salary_max
            self.currency = currency
            self.link = link
            self.date = datetime.datetime.now()
            self.id = None

    def __init__(self):
        self.database_engine = create_engine('sqlite:///hh_vacancies.db3', echo=False, pool_recycle=7200)

        self.metadata = MetaData()

        hhru_vacancies = Table('hh_vacancies', self.metadata, 
                               Column('id', Integer, primary_key=True),
                               Column('name', String),
                               Column('salary_min', Integer),
                               Column('salary_max', Integer),
                               Column('currency', String),
                               Column('link', String),
                               Column('date', DateTime)
                               )
        
        self.metadata.create_all(self.database_engine)
        mapper(self.HHruVacancies, hhru_vacancies)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        

    
    def sql_add_vacancies(self, data):
        """метод проверяет наличие вакансий в базе по ссылке, если записей нет, то добавляет новые"""
        for i in data:
            vacancy = self.session.query(self.HHruVacancies).filter_by(link=i['link'])
            if vacancy.count():
                return
            else:
                vacancies = self.HHruVacancies(i['name'], i['salary_min'], i['salary_max'], i['currency'], i['link'])
                self.session.add(vacancies)
                self.session.commit()

    
    def sql_get_vacancies(self):
        """возвращает все вакансии"""
        vacancies = self.session.query(self.HHruVacancies.id,
                                       self.HHruVacancies.name,
                                       self.HHruVacancies.salary_min,
                                       self.HHruVacancies.salary_max,
                                       self.HHruVacancies.currency,
                                       self.HHruVacancies.link,
                                       self.HHruVacancies.date).all()
        
        return vacancies
    

    """метод возвращает вакансии в которых минимальна ИЛИ максимальная зарплата больше запрашиваемой(salary)"""
    def sql_get_more(self, salary):
        vacancies = self.session.query(self.HHruVacancies.name,
                                       self.HHruVacancies.salary_min,
                                       self.HHruVacancies.salary_max,
                                       self.HHruVacancies.currency,
                                       self.HHruVacancies.link)
        vacancies = vacancies.filter((self.HHruVacancies.salary_min > salary) | (self.HHruVacancies.salary_max > salary))
        return vacancies.all()
    
        


if __name__ == '__main__':
    FILENAME = 'to_nosql_sql/hhru.json'
    with open(FILENAME, 'r', encoding='utf-8') as file:
        data = json.load(file)
    database = Model()
    database.sql_add_vacancies(data)
    pp(database.sql_get_vacancies())
    pp(database.sql_get_more(100000))