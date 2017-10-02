# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.response.html import HtmlResponse
import re
import json
from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem
from scrapy.loader import ItemLoader
from datetime import datetime

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    # question的第一页answer的请求url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&&limit={1}&offset={2}&sort_by=default'
    headers = {
        'HOST':'www.zhihu.com',
        'Referer':'https://www.zhihu.com',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    def parse(self, response):
        """
        提取HTML页面中的所有url，并跟踪这些url进一步爬取
        如果提取的url中格式为/question/xxx 就下载之后直接进入解析函数
        :type response: HtmlResponse
        :param response:
        :return:
        """
        urls = response.css('a::attr(href)').extract()
        urls = [response.urljoin(url) for url in urls]
        all_urls = filter(lambda x: True if x.startswith('https') else False, urls)
        for url in all_urls:
            match_obj = re.match('(.*zhihu.com/question/(\d+).*)(/|$).*', url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url =match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers,
                                     meta={'question_id': question_id}, callback=self.parse_question)
            else:
                # 如果不是question页面则直接进一步跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)


    def parse_question(self, response):
        """
        处理question页面，从页面中提取出具体的question item
        :type response: HtmlResponse
        :param response:
        :return:
        """
        question_id = int(response.meta.get('question_id'))
        if "QuestionHeader-title" in response.text:
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            # item_loader.add_xpath('title',"//*[@id=')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_value('url', response.url)
            item_loader.add_value('zhihu_id', int(response.meta.get('question_id')))
            # item_loader.add_css('answer_num','.List-headerText span::text')
            item_loader.add_xpath('answer_num', '//*[@id="root"]/div/main/div/div[2]/div[1]/div[1]/a/text()|//*[@id="QuestionAnswers-answers"]/div/div/div[1]/h4/span/text()')
            item_loader.add_css('comments_num', '.QuestionHeaderActions button::text')
            # item_loader.add_xpath('comments_num','//*[@class="Button Button--plain"][1]/svg/text()')
            item_loader.add_css('watch_user_num', '.NumberBoard-value::text')
            item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')
            question_item = item_loader.load_item()

        # 请求问题的答案
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), callback=self.parse_answer, headers=self.headers)
        yield question_item

    def parse_answer(self, response):
        """
        处理question的answer
        :type response: HtmlResponse
        """
        ans_json = json.loads(response.text)
        is_end = ans_json['paging']['is_end']
        # totals_answer = ans_json['paging']['totals']
        next_url = ans_json['paging']['next']

        # 提取answer的具体字段
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id']= answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['create_time'] = answer['created_time']
            answer_item['update_time'] = answer['updated_time']
            answer_item['crawl_time'] = datetime.now()
            yield answer_item
        if not is_end:
            yield scrapy.Request(next_url, callback=self.parse_answer, headers=self.headers)

    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=self.headers)]

        # return super().start_requests()

    def login(self, response):
        """

        :type response: HtmlResponse
        """
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = match_obj.group(1)

        if xsrf:

            post_data = {
                '_xsrf':xsrf,
                'phone_num': '13570344464',
                'password': 'konayuki',
                'captcha':''
            }
            import time
            t = str(int(time.time() * 1000))
            captcha_url = 'https://www.zhihu.com/captcha.gif?r={0}&type=login'.format(t)
            yield scrapy.Request(captcha_url, headers=self.headers, meta={'post_data': post_data},callback=self.login_after_captcha)


    def login_after_captcha(self, response):
        """
        下载验证码图片，然后需手动输入
        :type response: HtmlResponse
        """
        with open('captcha.jpg','wb') as f:
            f.write(response.body)
        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass
        captchat = input('输入验证码\n>')
        post_data = response.meta.get('post_data',{})
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data['captcha'] = captchat
        return scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )

    def check_login(self, response):
        """
        验证服务器的返回数据判断是否登录成功
        :type response: HtmlResponse
        :param response:
        :return:
        """
        text_json = json.loads(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                # yield self.make_requests_from_url(url)
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)