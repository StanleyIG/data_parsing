import requests
from bs4 import BeautifulSoup as bs
import re
from pprint import pprint as pp
import json
import pandas as pd
import os
from pymongo import MongoClient
from datetime import datetime
from databasesql import Model


class HHruParser(Model):
    def __init__(self, vacancy, max_page=1):
        super().__init__()
        self.vacancy = vacancy
        self.max_page = max_page
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36'
        }
        self.url = f'https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text={self.vacancy}&excluded_text=&area=88&salary=&' \
            f'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'
        self._session = requests.Session()

    """получает статус код"""

    def get_status_code(self):
        response = self._session.get(self.url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False

    """функция постраничной обработки вакансий c использованием матчинга
       что делает код более гибким к изменениям на сайте, и позволяет легко добавлять другие условия
    """

    def get_vacansy(self, content):
        soup = bs(content.content, 'html.parser')
        block = soup.find_all(
            'div', {'class': 'vacancy-serp-item-body__main-info'})
        vacancies = []
        for i in block:
            sal_raw = i.findChild(
                'span', {'class': 'bloko-header-section-2'})
            if sal_raw:
                sal_raw = sal_raw.text.replace('\u202f', '')
                currency = re.findall(r'[₽$€]|[а-я]{3}|[A-Z]{3}', sal_raw)[0]
                salary = re.findall('\d{1,6}', sal_raw)
                is_digit = [int(x) for x in salary]
                deduction, taxes = 'вычета', 'налогов'
                is_digit_min = str(min(is_digit))
                is_digit_max = str(max(is_digit))
                salary_min, salary_max = None, None
                match sal_raw.split():
                    case ['от', is_digit_min, currency] if is_digit_min and currency:
                        salary_min, salary_max = salary[0], None
                    case [is_digit_min, '–', is_digit_max, currency] if is_digit_min and is_digit_max and currency:
                        salary_min, salary_max = salary[0], salary[1]
                    case ['до', is_digit_max, currency] if is_digit_max and currency:
                        salary_min, salary_max = None, salary[0]
                    case ['от', is_digit_min, '–', 'до', is_digit_max, currency] if is_digit_min \
                            and is_digit_max and currency:
                        salary_min, salary_max = salary[0], salary[1]
                    case ['от', is_digit_min, currency, 'до', deduction, taxes] if is_digit_min and currency \
                            and deduction and taxes:
                        salary_min, salary_max = salary[0], None
                    case ['до', is_digit_max, currency, 'до', deduction, taxes] if is_digit_max and currency \
                            and deduction and taxes:
                        salary_min, salary_max = salary[0], None

            else:
                salary_min, salary_max = None, None
                currency = None

            vacancy_text = i.findChild(
                'a', {'class': 'serp-item__title'}).text
            vacancy_href = i.findChild(
                'a', {'class': 'serp-item__title'}).get('href')
            dct_block = {'name': vacancy_text,
                         'salary_min': int(salary_min) if salary_min is not None else salary_min,
                         'salary_max': int(salary_max) if salary_max is not None else salary_max,
                         'currency': currency,
                         'link': vacancy_href}

            vacancies.append(dct_block)
        return vacancies

    """получение всех вакансий"""

    def get_all_vacancies(self):
        status = self.get_status_code()
        vacancy_list = []
        params = {'page': 0}
        if not status:
            return {'vacancies': None, 'status_ok': self.get_status_code()}
        res = self._session.get(self.url, headers=self.headers, params=params)
        content = bs(res.text, 'html.parser')
        total_vacancies = content.find(
            'div', {"data-qa": "vacancies-search-header"}).findChild('h1').contents[0]

        for i in range(self.max_page):
            response = self._session.get(
                self.url, headers=self.headers, params=params)
            if not self.get_vacansy(response):
                break
            vacancy_list.extend(self.get_vacansy(response))
            params['page'] += 1

            print(f"обработано страниц: {params['page']}")
        print(f"всего вакансий: {total_vacancies}")
        return vacancy_list

    """записывает вакансии в json"""

    def write_json(self):
        FILENAME = 'to_nosql_sql/hhru.json'
        with open(FILENAME, 'w', encoding='utf-8') as file:
            json.dump(self.get_all_vacancies(), file,
                      ensure_ascii=False, indent=4)
        with open(FILENAME, 'r', encoding='utf-8') as file:
            data = len(json.load(file))
            return data

    """выводит результат через DataFrame pandas"""

    def to_pandas(self):
        FILENAME = 'to_nosql_sql/hhru.json'
        if os.path.exists(FILENAME):
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return pd.DataFrame(data)

        else:
            self.write_json()
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return pd.DataFrame(data)


    """добавляет только новые вакансии проверяя наличие вакансии поссылке, если таковой нет, то добавляет в базу новые, а также дату добавления 
       вакансии в MongoDB при вызове функции"""
    def add_to_mongodb(self):
        new_vacancies = self.get_all_vacancies()
        client = MongoClient('mongodb://localhost:27017/')
        db = client['database']
        vacancies = db['vacancies']
        for vacancy in new_vacancies:
            if vacancies.find_one({'link': vacancy['link']}) is None:
                vacancy['date_added'] = datetime.now().strftime("%d.%m.%Y")
                vacancies.insert_one(vacancy)
        return vacancies
    

    def get_more_salary_mongodb(self, salary):
        client = MongoClient('mongodb://localhost:27017/')
        db = client['database']
        
        if 'vacancies' in db.list_collection_names():
            vacancies = db['vacancies']
            result = vacancies.find({'$or': [
                {'salary_min': {'$gt': salary}},
                {'salary_max': {'$gt': salary}}
            ]})
            
            for vacancy in result:
                print("name:", vacancy['name'])
                print("salary min:", vacancy['salary_min'])
                print("salary max:", vacancy['salary_max'])
                print("currency:", vacancy['currency'])
                print("link:", vacancy['link'])
                print("date added:", vacancy['date_added'])
                print("-----------------------")
        else:
            self.add_to_mongodb()
            self.get_more_salary_mongodb(salary) 
    

    def sql_add_vacancies(self):
        FILENAME = 'to_nosql_sql/hhru.json'
        if os.path.exists(FILENAME):
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)        
        else:
            self.write_json()
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
        return super().sql_add_vacancies(data)
        
      

    
hhru = HHruParser('python', 11)
# метод sql_add_vacancies базового класса Model, создаёт базу и добавляет вакансии
# hhru.sql_add_vacancies()
# метод sql_get_vacancies()) базового класса Model, возвращает все вакансии
# pp(hhru.sql_get_vacancies())
# метод sql_get_more базового класса Model, метод возвращает вакансии в которых минимальна ИЛИ максимальная зарплата больше запрашиваемой(salary)
print('SQL DB с использованием ORM SQLAlchemy')
pp(hhru.sql_get_more(100000))
print(150*'/')
print('NoSQL MongoDB')
# метод get_more_salary_mongodb возвращает вакансии в которых минимальна ИЛИ максимальная зарплата больше запрашиваемой(salary)
hhru.get_more_salary_mongodb(100000)
# pp(hhru.get_all_vacancies())
# hhru.write_json()
# print(hhru.to_pandas())
# hhru.add_to_mongodb()