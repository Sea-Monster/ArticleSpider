# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http.response.html import HtmlResponse


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    # start_urls = ['http://blog.jobbole.com/']
    start_urls = ['http://blog.jobbole.com/110287/']

    def parse(self, response):
        '''

        :type response: HtmlResponse
        :param response:
        :return:
        '''

        # 通过css选择器提取字段
        a = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip()
        title = response.css(".entry-header h1::text").extract()
        create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·","").strip()
        praise_nums = response.css(".vote-post-up h10::text").extract()[0]
        praise_nums2 = response.css(".vote-post-up>h10::text").extract()[0]
        fav_nums = response.css(".bookmark-btn::text").extract()[0]
        match_re = re.match(".*?(\d+).*", fav_nums)
        if match_re:
            fav_nums = match_re.group(1)
        content = response.css("div.entry").extract()[0]
        tags = response.css("p.entry-meta-hide-on-mobile a::text").extract_first()
    

