import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class SjruSpider(scrapy.Spider):
    name = 'sjru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=python&geo%5Bc%5D%5B0%5D=1']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//a[@rel='next']/@href").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        vacansy = response.css('a.icMQ_::attr(href)').extract()

        for link in vacansy:
            yield response.follow(link, callback=self.vacansy_parse, cb_kwargs=dict(link=link))


    def vacansy_parse(self, response: HtmlResponse):
        name = response.xpath("//h1[@class='_1h3Zg rFbjy _2dazi _2hCDz']/text()").extract_first()
        location = response.xpath("//span[@class='_1h3Zg _1TK9I _2hCDz']/text()").extract_first()
        currency = response.xpath("//span[@class='_1h3Zg _2Wp8I _2rfUm _2hCDz']//text()").extract()
        url = response.url
        date_posted = response.xpath("//div[@class='f-test-title _183s9 _3wZVt OuDXD _1iZ5S']"
                                     "/div[2]/span/text()").extract_first()


        yield JobparserItem(name=name, location=location, currency=currency, url=url, date_posted=date_posted)