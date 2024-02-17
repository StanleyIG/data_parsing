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
from scrapy_selenium import SeleniumRequest


class AvitoparserPipeline:
    def __init__(self):
        client = MongoClient(host='localhost', port=27017)
        self.mongobase = client.database

    def process_item(self, item, spider):
        #curr = item['currency'].strip()
        #item['currency'] = curr
        self.save_to_mongodb(item)
        return item

    def save_to_mongodb(self, item):
        collection = self.mongobase['scrapy_avito']
        collection.insert_one(item)


class AvitoImgPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['img']:
            for img in item['img']:
                try:
                    yield SeleniumRequest(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
         if results:
            item['img'] = [itm[1] for itm in results if itm[0]]
         return item

    def file_path(self, request, response=None, info=None, *, item):
        name = item['name']
        image_guid = hashlib.sha1(request.url.encode()).hexdigest()
        return f'{name}/{image_guid}.jpg'