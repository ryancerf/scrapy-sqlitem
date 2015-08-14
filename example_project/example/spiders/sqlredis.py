from scrapy import Spider

from scrapy_sqlitem import SqlMixin
from scrapy_redis.spiders import RedisMixin

from example.items import ExampleLoader

from .. database import init_db


class MySpider(SqlMixin, RedisMixin, Spider):
    """Spider that saves items in sql database """
    name = 'mysqlredis_spider'

    start_urls = ['http://dmoz.org']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        init_db()

    def parse(self, response):
        el = ExampleLoader(response=response)
        el.add_xpath('name', '//title[1]/text()')
        el.add_value('url', response.url)
        return el.load_item()

    def _set_crawler(self, crawler):
        super(MySpider, self)._set_crawler(crawler)
        RedisMixin.setup_redis(self)
        SqlMixin.setup_sql(self)
