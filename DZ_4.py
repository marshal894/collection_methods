import requests
from lxml import html
from pymongo import MongoClient
from pprint import pprint

client = MongoClient('localhost', 27017)

db = client['News']
lenta = db.lenta


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'
}

response = requests.get('https://lenta.ru/',
                        headers=headers)
dom = html.fromstring(response.text)
data_lenta = []
items = dom.xpath("//section[contains(@class, 'top7')]//div[contains(@class, 'item')]")

for item in items:
    data = {}
    source = 'https://lenta.ru'
    name = item.xpath(".//h2//a//text | .//a//text()")
    date = item.xpath(".//h2//a//time//@datetime | .//a//time//@datetime")

    link = item.xpath(".//h2//a//@href | .//a//@href")
    if link[0][0] == '/':
        link = source + link[0]
    else:
        link = link[0]

    data['name'] = name[1].replace('\xa0', ' ')
    data['source'] = source
    data['link'] = link
    data['date'] = date[0]
    data_lenta.append(data)

pprint(data_lenta)
