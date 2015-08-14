from scrapy_sqlitem import SqlSpider

from example.items import ExampleLoader

from .. database import init_db


class MySpider(SqlSpider):
    """Spider that saves items in sql database """
    name = 'mysql_spider'

    start_urls = ['http://dmoz.org']

    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        init_db()

    def parse(self, response):
        el = ExampleLoader(response=response)
        el.add_xpath('name', '//title[1]/text()')
        el.add_value('url', response.url)
        return el.load_item()
