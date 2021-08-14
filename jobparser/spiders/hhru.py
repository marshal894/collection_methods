import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem

class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://izhevsk.hh.ru/search/vacancy?area=&fromSearchLine=true&st=searchVacancy&text=python']

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//a[@data-qa='pager-next']/@href").extract_first()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        links = response.xpath("//a[@data-qa='vacancy-serp__vacancy-title']/@href").extract()
        for link in links:
            yield response.follow(link, callback=self.vacancy_parse)


    def vacancy_parse(self, response:HtmlResponse):
        vac_name = response.xpath("//h1/text()").extract_first()
        vac_salary = response.css("p.vacancy-salary span::text").extract_first()
        vac_url = response.url
        location = response.xpath("//div[contains(@class, 'vacancy-company')]/p//text()").extract()


        def meta(itemprop):
            return response.xpath(f"//meta[contains(@itemprop,'{itemprop}')]/@content").extract_first()

        currency = meta('currency')
        min_salary = meta('minValue')
        max_salary = meta('maxValue')
        date_posted = meta('datePosted')



        yield JobparserItem(name=vac_name, salary=vac_salary, url=vac_url, location=location, currency=currency,
                            min_salary=min_salary, max_salary=max_salary, date_posted=date_posted)

