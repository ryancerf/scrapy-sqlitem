from sqlalchemy import Table, Column, Integer, String

from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

import sys
sys.path.append("~/Projects/utils/sqlitem")
from scrapy_sqlitem import SqlItem

from . database import metadata


class ExampleItem(SqlItem):
    sqlmodel = Table('example_table', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('description', String),
            Column('link', String),
            Column('crawled', String),
            Column('spider', String),
            Column('url', String))


class ExampleLoader(ItemLoader):
    default_item_class = ExampleItem
    default_input_processor = MapCompose(lambda s: s.strip())
    default_output_processor = TakeFirst()
    description_out = Join()
