# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.images import ImagesPipeline
import pymysql  #mysqlclient装不上，只好用这个了
from twisted.enterprise import adbapi
from twisted.internet.defer import Deferred

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class MysqlPipeline(object):

    def __init__(self):
        self.conn = pymysql.connect('172.16.26.96', 'root', 'password', 'article_spider', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(url_object_id,title,url,create_date,fav_nums)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item['url_object_id'], item['title'], item['url'], item['create_date'], item['fav_nums']))
        self.conn.commit()


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host = settings['MYSQL_HOST'],
            db = settings['MYSQL_DBNAME'],
            user = settings['MYSQL_USER'],
            passwd = settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass = pymysql.cursors.DictCursor,
            use_unicode = True
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用Twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        if isinstance(query, Deferred):
            query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        """
        执行具体插入
        根据不同的item构建不同的sql语句并插入到mysql中
        :param cursor:
        :param item:
        :return:
        """
        insert_sql, params = item.get_insert_sql()

        cursor.execute(insert_sql, params)


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_path' in item:
            for ok,value in results:
                image_file_path = value['path']
            item['front_image_path'] = image_file_path  # 文件保存的实际位置, 以便以后保存到数据库或者其他地方
        return item

        # return super().item_completed(results, item, info)