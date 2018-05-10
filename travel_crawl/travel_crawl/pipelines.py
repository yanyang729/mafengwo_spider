# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from .items import GonglveItem, QAItem

class MongoDBPipeline(object):
    def __init__(self):
        clinet = pymongo.MongoClient("localhost", 27017)
        db = clinet["mfw2"]
        self.gonglve = db["gonglve"]
        self.qa = db['qa']

    def process_item(self, item, spider):
        """ 判断item的类型，并作相应的处理，再入数据库 """
        if isinstance(item, GonglveItem):
            try:
                self.gonglve.insert(dict(item))
                print "New added to MongoDB database!"
            except Exception:
                print 'Insert Exception'
        if isinstance(item, QAItem):
            try:
                self.qa.insert(dict(item))
                print "New added to MongoDB database!"
            except Exception:
                print 'Insert Exception'




