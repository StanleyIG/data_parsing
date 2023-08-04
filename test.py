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
            deduction, taxes = 'вычета', 'налогов'
            is_digit_min = str(min(is_digit))
            is_digit_max = str(max(is_digit))
            currency = re.findall(
                r'[₽$€]|[а-я]{3}|[A-Z]{3}', ''.join(match_salary))[0]
            salary_min, salary_max = None, None
            match match_salary:
                case['от', is_digit_min, currency, 'до', deduction, taxes]:  # if deduction and taxes \
                    # and is_digit_min and currency:
                    salary_min, salary_max = is_digit_min, None
                case['до', is_digit_max, currency, 'до', deduction, taxes]:  # if deduction and taxes \
                    # and is_digit_max and currency:
                    salary_min, salary_max = None, is_digit_max
                # if is_digit_min and is_digit_max and deduction and taxes and currency:
                case['от', is_digit_min, 'до', is_digit_max, currency, 'до', deduction, taxes]:
                    salary_min, salary_max = is_digit_min, is_digit_max
                case['от', is_digit_min, 'до', is_digit_max, currency]:  # if is_digit_min and is_digit_max \
                    # and currency:
                    salary_min, salary_max = is_digit_min, is_digit_max
                # if is_digit_min and is_digit_max:
                case[is_digit_min, '-', is_digit_max]:
                    salary_min, salary_max = is_digit_min, is_digit_max

                case['от', is_digit_min, 'до', is_digit_max, 'на', 'руки']:
                    salary_min, salary_max = is_digit_min, is_digit_max

                case['от', is_digit_min, currency, 'на', 'руки']:
                    salary_min, salary_max = is_digit_min, None
                
                case['до', is_digit_max, currency, 'на', 'руки']:
                    salary_min, salary_max = is_digit_max, None

        else:
            salary_min, salary_max, currency = None, None, None

        return salary_min, salary_max, currency

    def save_to_mongodb(self, item):
        collection = self.mongobase['scrapy_hhru']
        collection.insert_one(item)
