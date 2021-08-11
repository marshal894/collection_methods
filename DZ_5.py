from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from hashlib import sha1
import json
from pymongo.errors import DuplicateKeyError

chrome_options = Options()
chrome_options.add_argument("start-maximized")

driver = webdriver.Chrome(executable_path='./chromedriver.exe', options=chrome_options)

url = 'https://www.mvideo.ru/?cityId=CityCZ_975'
driver.get(url)

btn_wait = WebDriverWait(driver, 5)
actions = ActionChains(driver)
block_new_products = driver.find_element_by_xpath('//div[contains(h2, "Новинки")]')
actions.move_to_element(block_new_products).perform()
while True:
    try:
        btn_next = btn_wait.until(EC.element_to_be_clickable(
 (By.XPATH, '//div[contains(h2, "Новинки")]/../..//a[contains(@class, "next-btn")]')))
    except TimeoutException:
        break
    except ElementClickInterceptedException:
        break
    else:
        btn_next.click()

products = driver.find_elements_by_xpath( '//div[contains(h2, "Новинки")]/../..//a[contains(@class, "fl-product-tile-picture")]')

data = [{} for _ in products]
for hit, dat in zip(products, data):
    json_hit = json.loads(hit.get_attribute('data-product-info'))
    dat['name'] = json_hit['productName']
    dat['price'] = json_hit['productPriceLocal']
    dat['category'] = json_hit['productCategoryName']
    dat['vendor'] = json_hit['productVendorName']
    dat['link'] = hit.get_attribute('href')
    dat['_id'] = sha1((dat['name']+dat['link']+dat['price']).encode('utf-8')).hexdigest()
    dat['price'] = float(dat['price'])

print(data)

client = MongoClient('localhost', 27017)
for item in data:
    try:
        client['products'].insert_one(item)
    except DuplicateKeyError:
        pass