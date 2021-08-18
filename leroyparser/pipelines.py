# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import scrapy
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


class LeroyparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)
        self.mongo_db = client['Leroy']

    def process_item(self, item, spider):
        item['characteristics'] = dict(zip(item['characteristics_keys'], item['characteristics_values']))
        del item['characteristics_keys']
        del item['characteristics_values']

        collection = self.mongo_db[spider.name]
        collection.update_one(item, {'$set': item}, upsert=True)

        return item


class LeroyparserImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['images']:
            for image in item['images']:
                try:
                    yield scrapy.Request(image)
                except Exception as e:
                    print(e)
        return item

    def item_completed(self, results, item, info):
        if results:
            item['images'] = [itm[1] for itm in results if itm[0]]
        return item