
from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
from pymongo import MongoClient
from pprint import pprint

vacancy = 'Python'
price = 90000
vacancy_mongodb = MongoClient('127.0.0.1', 27017)
db = vacancy_mongodb['hh']
vacancy_collection = db['vacancy']

def _parser_hh(vacancy):
    vacancy_date = []

    params = {
        'text': vacancy, \
        'search_field': 'name', \
        'items_on_page': '100', \
        'page': ''
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'
    }

    link = 'https://hh.ru/search/vacancy'


    html = requests.get(url=link, params=params, headers=headers)

    if html.ok:
        parsed_html = bs(html.text, 'html.parser')

        page_block = parsed_html.find('div', {'data-qa': 'pager-block'})
        if not page_block:
            last_page = '1'
        else:
            last_page = int(page_block.find_all('a', {'class': 'bloko-button'})[-2].getText())

    for page in range(0, last_page):
        params['page'] = page
        html = requests.get(link, params=params, headers=headers)

        if html.ok:
            parsed_html = bs(html.text, 'html.parser')

            vacancy_items = parsed_html.find('div', {'data-qa': 'vacancy-serp__results'}) \
                .find_all('div', {'class': 'vacancy-serp-item'})

            for item in vacancy_items:
                vacancy_date.append(_parser_item_hh(item))

    return vacancy_date


def _parser_item_hh(item):
    vacancy_date = {}
    vacancy_name = item.find('a', {'data-qa': 'vacancy-serp__vacancy-title'}) \
        .getText()
    vacancy_date['vacancy_name'] = vacancy_name
    company_name = item.find('div', {'class': 'vacancy-serp-item__meta-info-company'}) \
        .getText() \
        .replace(u'\xa0', u' ')
    vacancy_date['company_name'] = company_name

    city = item.find('span', {'data-qa': 'vacancy-serp__vacancy-address'}) \
        .getText() \
        .split(', ')[0]
    vacancy_date['city'] = city
    salary = item.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})

    if not salary:
        salary_min = None
        salary_max = None
        salary_currency = None
    else:
        salary = salary.getText() \
            .replace(u'\xa0', u'').replace(u' ', u' ')
        salary = re.split('-', salary)
        if len(salary) == 1:
            spam = re.split(' ', salary[0])
            if spam[0] == 'до':
                salary_min = None
                salary_max = "".join(map(str, spam[1])) if len(spam[1]) > 1  else spam[1]
                salary_currency = "".join(map(str, spam[2:])) if len(spam[2:]) > 1  else spam[2:]
            elif spam[0] == 'от':
                salary_min = "".join(map(str, spam[1])) if len(spam[1]) > 1  else spam[1]
                salary_max = None
                salary_currency = "".join(map(str, spam[2:])) if len(spam[2:]) > 1  else spam[2:]
            else:
                salary_min = "По договорённости"
                salary_max = "По договорённости"
                salary_currency = "-"
        else:
            spam1 = re.split(' ', salary[0])
            spam2 = re.split(' ', salary[1])
            salary_min = "".join(map(str, spam1[0])) if len(spam1[0]) > 1  else spam1[0]
            salary_max = "".join(map(str, spam2[0])) if len(spam2[0]) > 1  else spam2[0]
            salary_currency = "".join(map(str, spam2[1:])) if len(spam2[1:]) > 1  else spam2[1:]

    vacancy_date['salary_min'] = salary_min
    vacancy_date['salary_max'] = salary_max
    vacancy_date['salary_currency'] = salary_currency

    # link
    vacancy_link = item.find('div', {'class': 'vacancy-serp-item__row vacancy-serp-item__row_header'}) \
        .find('a')['href']

    vacancy_link = vacancy_link.split('?')[0]

    vacancy_date['vacancy_link'] = vacancy_link

    # site
    vacancy_date['site'] = 'www.hh.ru'

    vacancy_collection.update_one(
        {'name': vacancy_date['vacancy_name'], 'vacancy_link': vacancy_date['vacancy_link']},
        {'$set': vacancy_date},
        upsert=True)

    return vacancy_date

def parser_vacancy(vacancy):
    vacancy_date = []
    vacancy_date.extend(_parser_hh(vacancy))
    df = pd.DataFrame(vacancy_date)
    return df


find = vacancy_collection.find(
            {'$or': [
                {'compensation.min': {'$gt': price}},
                {'compensation.max': {'$gt': price}},
            ]})
for doc in find:
    pprint(doc)

