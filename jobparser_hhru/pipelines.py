# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import re
import hashlib

import scrapy
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


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
            # выполнится и подключит регулярки только в крайнем случае, если все остальные условия не выполняются
            elif len(is_digit) > 1:
                currency = re.findall(
                    r'[₽$€]|[а-я]{3}|[A-Z]{3}', ''.join(match_salary))[0]
                salary_min, salary_max, currency = is_digit[0], is_digit[1], currency if currency else None
            # если ни одно условие не выполняется, то None
            else:
                salary_min, salary_max, currency = None, None, None
        # если ничего, то None
        else:
            salary_min, salary_max, currency = None, None, None

        return int(salary_min) if salary_min else None, int(salary_max) if salary_max else None, currency

    def save_to_mongodb(self, item):
        collection = self.mongobase['scrapy_hhru']
        collection.insert_one(item)


class CastoramaGoodsPipeline:
    def __init__(self):
        client = MongoClient(host='localhost', port=27017)
        self.mongobase = client.database

    def process_item(self, item, spider):
        #curr = item['currency'].strip()
        #item['currency'] = curr
        self.save_to_mongodb(item)
        return item

    def save_to_mongodb(self, item):
        collection = self.mongobase['scrapy_castorama']
        collection.insert_one(item)


class CastoramaGoodsPipelineImage(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['img']:
            for img in item['img']:
                try:
                    yield scrapy.Request(img, meta={'name': item['name']})
                except Exception as e:
                    print(e)
    
    def item_completed(self, results, item, info):
         if results:
            item['img'] = [itm[1] for itm in results if itm[0]]
         return item

    def file_path(self, request, response=None, info=None, *, item=None):
        name = request.meta['name']
        image_guid = hashlib.sha1(request.url.encode()).hexdigest()
        return f'{name}/{image_guid}.jpg'


