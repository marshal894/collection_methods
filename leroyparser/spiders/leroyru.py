import scrapy
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader

from leroyparser.items import LeroyparserItem


class LeroyruSpider(scrapy.Spider):
    name = 'leroyru'
    allowed_domains = ['leroymerlin.ru']
    start_urls = ['https://leroymerlin.ru/search/?q=ламинат&family=laminat-201709&suggest=true']

    def parse(self, response: HtmlResponse):
        next_page_link = response.xpath("//a[contains(@aria-label, 'Следующая страница:')]/@href").extract_first()
        if next_page_link:
            yield response.follow(next_page_link, self.parse)

        links = response.xpath("//div[@data-qa-product]/a/@href").extract()
        for link in links:
            yield response.follow(link, self.leroy_parse)

    def leroy_parse(self, response: HtmlResponse):
        loader = ItemLoader(item=LeroyparserItem(), response=response)
        loader.add_xpath("name", "//h1/text()")
        loader.add_xpath("images", "//picture[@slot='pictures']/source/@data-origin")
        loader.add_xpath("characteristics_keys", "//dl/div/dt/text()")
        loader.add_xpath("characteristics_values", "//dl/div/dd/text()")
        loader.add_value("link", response.url)
        loader.add_xpath("price", "//span[@slot='price']/text()")

        yield loader.load_item()