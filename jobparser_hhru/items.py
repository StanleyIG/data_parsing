# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import MapCompose, Compose, TakeFirst


class JobparserHhruItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    salary = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    currency = scrapy.Field()
    url = scrapy.Field()
    _id = scrapy.Field()


def process_price(price):
    if price:
        price = price[0].replace(" ", "")
        try:
            price = int(price)
            return price
        except Exception as e:
            return None
    return None

def process_currency(currency):
    if currency:
        currency[0].strip()
        return currency
    return None

def process_photo(photo):
    if photo.startswith('/'):
        photo = "https://www.castorama.ru" + photo
    else:
        photo = photo
    return photo

def process_name(name):
    name = name[0].strip()
    return name


class CastoramaGoodsItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field(input_processor=Compose(process_name), output_processor=TakeFirst())
    price = scrapy.Field(input_processor=Compose(process_price), output_processor=TakeFirst())
    currency = scrapy.Field(input_processor=Compose(process_currency), output_processor=TakeFirst())
    img = scrapy.Field(input_processor=MapCompose(process_photo))
    url = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()
