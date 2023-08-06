# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from itemadapter import ItemAdapter
from pymongo import MongoClient


class JobparserHhruPipeline:
    def __init__(self):
        client = MongoClient(host='localhost', port=27017)
        self.mongobase = client.database

    def process_item(self, item, spider):
        salary = item['salary']
        salary_min, salary_max, currency = self.process_salary(salary)
        item['salary_min'] = salary_min
        item['salary_max'] = salary_max
        item['currency'] = currency
        del item['salary']
        self.save_to_mongodb(item)
        return item

    def process_salary(self, salary):
        if salary:
            match_salary = ''.join(salary).replace('\xa0', '').split()
            is_digit = [int(x) for x in match_salary if x.isdigit()]
            if len(is_digit) < 2 and 'от' in match_salary:
                salary_min, salary_max, currency = match_salary[1], None, match_salary[2]
            elif len(is_digit) < 2 and 'до' in match_salary:
                salary_min, salary_max, currency = None, match_salary[1], match_salary[2]
            elif len(is_digit) > 1 and 'от' in match_salary and 'до' in match_salary:
                salary_min, salary_max, currency = match_salary[1], match_salary[3], match_salary[4]

        else:
            salary_min, salary_max, currency = None, None, None

        return int(salary_min) if salary_min else None, int(salary_max) if salary_max else None, currency

    def save_to_mongodb(self, item):
        collection = self.mongobase['scrapy_hhru']
        collection.insert_one(item)
