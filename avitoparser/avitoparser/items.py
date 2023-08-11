# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import MapCompose, Compose, TakeFirst


def process_price(price):
    if price:
        price = price[0].replace("\xa0", "")
        try:
            price = int(price)
            return price
        except Exception as e:
            return None
    return None


def process_photo(photo):
    if photo:
        if photo.startswith('/'):
            photo = "https://www.avito.ru" + photo
        else:
            photo = photo
        return photo
    return None

def process_description(desc):
    if desc:
        return '\n'.join(line for line in desc)
    return None


class AvitoparserItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    price = scrapy.Field(input_processor=Compose(
        process_price), output_processor=TakeFirst())
    description = scrapy.Field(input_processor=MapCompose(process_description))
    img = scrapy.Field(input_processor=MapCompose(process_photo))
    url = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()
