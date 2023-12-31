import requests
from bs4 import BeautifulSoup as bs
import re
from pprint import pprint as pp
import json
import pandas as pd
import os


class HHruParser:
    def __init__(self, vacancy, max_page=1):
        self.vacancy = vacancy
        self.max_page = max_page
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36'
        }
        self.url = f'https://kazan.hh.ru/search/vacancy?no_magic=true&L_save_area=true&text={self.vacancy}&excluded_text=&area=88&salary=&' \
            f'currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=20'
        self.session = requests.Session()


    """получает статус код"""
    def get_status_code(self):
        response = self.session.get(self.url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False


    """функция постраничной обработки вакансий"""
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
                if 'до' in sal_raw and 'от' not in sal_raw:
                    salary_min, salary_max = None, salary[0]
                elif 'от' in sal_raw and 'до' not in sal_raw:
                    salary_min, salary_max = salary[0], None
                elif 'от' in sal_raw and 'до' in sal_raw and len(salary) > 1:
                    salary_min, salary_max = salary[0], salary[1]
                elif 'от' in sal_raw and 'до' in sal_raw and len(salary) < 2:
                    salary_min, salary_max = salary[0], None
                elif len(salary) > 1:
                    salary_min, salary_max = salary[0], salary[1]
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
        res = self.session.get(self.url, headers=self.headers, params=params)
        content = bs(res.text, 'html.parser')
        total_vacancies = content.find(
            'div', {"data-qa": "vacancies-search-header"}).findChild('h1').contents[0]

        for i in range(self.max_page):
            response = self.session.get(
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
        FILENAME = 'HH_ru_bs4/hhru.json'
        with open(FILENAME, 'w', encoding='utf-8') as file:
            json.dump(self.get_all_vacancies(), file,
                      ensure_ascii=False, indent=4)
        with open(FILENAME, 'r', encoding='utf-8') as file:
            data = len(json.load(file))
            return data


    """выводит результат через DataFrame pandas"""
    def to_pandas(self):
        FILENAME = 'HH_ru_bs4/hhru.json'
        if os.path.exists(FILENAME):
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return pd.DataFrame(data)

        else:
            self.write_json()
            with open(FILENAME, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return pd.DataFrame(data)


hhru = HHruParser('python', 11)
#pp(hhru.to_pandas())
hhru.write_json()
