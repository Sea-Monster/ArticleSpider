# -*- coding: utf-8 -*-
# 调试Spider用
from scrapy.cmdline import execute
import sys
import os

print(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 启动Spider： 在命令行，scrapy crawl jobbole
# JobboleSpider中的name：jobbole
# execute(['scrapy', 'crawl', 'jobbole'])
execute(['scrapy', 'crawl', 'zhihu'])