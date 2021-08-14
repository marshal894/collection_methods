# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from pymongo import MongoClient
from hashlib import sha1
from pymongo.errors import DuplicateKeyError
import datetime

class JobparserPipeline:

    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client['vacancies']

    def process_item(self, item, spider):
        collection = self.mongo_base[spider.name]

        if spider.name == 'hhru':
            item['min_salary'] = int(item['min_salary']) if item['min_salary'] else None
            item['max_salary'] = int(item['max_salary']) if item['max_salary'] else None
            item['location'] = ' '.join(item['location']).replace(' ,', ',').replace(' \xa0', ',')
            try:
                collection.insert_one(item)
            except DuplicateKeyError:
                pass

        if spider.name == 'superjobru':
            item['link'] = 'https://www.superjob.ru' + item['link']
            raw_salary = item['currency']
            if raw_salary[0] == 'По договорённости':
                item['min_salary'] = None
                item['max_salary'] = None
                item['currency'] = None
            elif raw_salary[0] == 'до':
                item['min_salary'] = None
                item['max_salary'] = int(raw_salary[2].replace('\xa0', ''))
                item['currency'] = raw_salary[4].replace('₽', 'RUR')
            elif raw_salary[0] == 'от':
                item['min_salary'] = int(raw_salary[2].replace('\xa0', ''))
                item['max_salary'] = None
                item['currency'] = raw_salary[4].replace('₽', 'RUR')
            elif raw_salary[2] == '—':
                item['min_salary'] = int(raw_salary[0].replace('\xa0', ''))
                item['max_salary'] = int(raw_salary[4].replace('\xa0', ''))
                item['currency'] = raw_salary[6].replace('₽', 'RUR')
            else:
                item['min_salary'] = None
                item['max_salary'] = None
                item['currency'] = None

            if item['date_posted'] == 'вчера':
                yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
                item['date_posted'] = yesterday.date().isoformat()

        item['source'] = spider.name
        _sha_str = str(item['name']) + str(item['min_salary']) + str(item['max_salary'])
        item['_id'] = sha1(_sha_str.encode('utf-8')).hexdigest()

        try:
            collection.insert_one(item)
        except DuplicateKeyError:
            pass

        return item
