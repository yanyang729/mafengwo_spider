# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class GonglveItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    keyword = scrapy.Field()
    time = scrapy.Field()
    view = scrapy.Field()
    images = scrapy.Field()
    body = scrapy.Field()
    subtitle = scrapy.Field()
    id = scrapy.Field()
    comments = scrapy.Field()

class QAItem(scrapy.Item):
    url = scrapy.Field()
    owner = scrapy.Field()
    view = scrapy.Field()
    time = scrapy.Field()
    title = scrapy.Field()
    question = scrapy.Field()
    answers = scrapy.Field()
