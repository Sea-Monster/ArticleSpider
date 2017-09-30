# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http.response.html import HtmlResponse
from scrapy.http import Request
from scrapy.selector.unified import Selector
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem, ArticleItemLoader
from ArticleSpider.utils.common import get_md5
from datetime import datetime
from scrapy.loader import ItemLoader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    # start_urls = ['http://blog.jobbole.com/']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        '''
        1 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2 获取下一页的url并交给scrapy进行下载，下载完成后交给parse
        :type response: HtmlResponse
        :param response:
        :return:
        '''
        # 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            if isinstance(post_node, Selector):
                print(type(post_node))
                image_url = post_node.css("img::attr(src)").extract_first("")
                post_url = post_node.css("::attr(href)").extract_first("")
                # Request(url=post_url, callback=self.parse_detail)
                yield Request(url=parse.urljoin(response.url, post_url),
                              meta={"front_image_url":parse.urljoin(response.url, image_url)},
                              callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        """
        提取文章的具体字段
        :type response: HtmlResponse
        :param response:
        :return:
        """
        # 通过Item loader加载item
        item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
        item_loader.add_value('url_object_id', get_md5(response.url))
        item_loader.add_css('title', '.entry-header h1::text')
        item_loader.add_value('url', response.url)
        item_loader.add_css('create_date', 'p.entry-meta-hide-on-mobile::text')
        item_loader.add_value('front_image_url', response.meta.get("front_image_url",""))
        item_loader.add_css('praise_nums', '.vote-post-up h10::text')
        item_loader.add_css('comment_nums', "a[href='#article-comment'] span::text")
        item_loader.add_css('fav_nums', '.bookmark-btn::text')
        item_loader.add_css('tags', 'p.entry-meta-hide-on-mobile a::text')
        item_loader.add_css('content', 'div.entry')
        article_item = item_loader.load_item()

        yield article_item  # 传递到pipelines.py


