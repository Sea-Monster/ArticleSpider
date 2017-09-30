# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.response.html import HtmlResponse
import re
import json

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    headers = {
        'HOST':'www.zhihu.com',
        'Referer':'https://www.zhihu.com',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
    }

    def parse(self, response):
        pass

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
        for url in self.start_urls:
            yield self.make_requests_from_url(url)