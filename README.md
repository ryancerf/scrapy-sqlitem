scrapy-sqlitem
=========

scrapy-sqlitem allows you to define scrapy items using 
Sqlalchemy models or tables. It also provides an easy way to save to the database in chunks.

This project is in beta.  Pull requests and feedback are welcome.
The regular caveats of using a sql database backend for a write heavy application still apply.


Inspiration from [scrapy-redis](https://github.com/darkrho/scrapy-redis) and [scrapy-djangoitem](https://github.com/scrapy-plugins/scrapy-djangoitem)

Quickstart
=========
###Install with pip
```
pip install scrapy_sqlitem
```

###[Define items using Sqlalchemy ORM](http://docs.sqlalchemy.org/en/rel_1_0/orm/tutorial.html#declare-a-mapping)

```python
from scrapy_sqlitem import SqlItem

class MyModel(Base):
    __tablename__ = 'mytable'
    id = Column(Integer, primary_key=True)
    name = Column(String)

class MyItem(SqlItem):
    sqlmodel = MyModel

```
###[Or Define Items using Sqlalchemy Core](http://docs.sqlalchemy.org/en/rel_1_0/core/metadata.html)

```python
from scrapy_sqlitem import SqlItem

class MyItem(SqlItem):
    sqlmodel = Table('mytable', metadata
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False))

```

If tables have not been created yet make sure to create them.
See sqlalchemy docs and the example spider.

###Use SqlSpider to automatically save database

settings.py
```python
DATABASE_URI = "sqlite:///"
```

###Define your spider

```python
from scrapy_sqlitem import SqlSpider

class MySpider(SqlSpider):
   name = 'myspider'

   start_urls = ('http://dmoz.org',)

   def parse(self, response):
        selector = Selector(response)
        item = MyItem()
        item['name'] = selector.xpath('//title[1]/text()').extract_first()
        yield item

```

###Run the spider

```sh
scrapy crawl myspider
```

###Query the database

```sql
Select * from mytable;

 id |               name                |
----+-----------------------------------+
  1 | DMOZ - the Open Directory Project |
```

Other Information
=========

###Do Not want to use SqlSpider?  Write a pipeline instead.

```python

from sqlalchemy import create_engine

class CommitSqlPipeline(object):
        
        def __init__(self):
                self.engine = create_engine("sqlite:///")

        def process_item(self, item, spider):
                item.commit_item(engine=self.engine)
```


###Drop items missing required primary key data before saving to the db

```python

from scrapy.exceptions import DropItem

class DropMissingDataPipeline(object):
        def process_item(self, item, spider):
                if item.null_required_fields:
                        raise DropItem
                else:
                        return item
# Watch out for Serial primary keys that are considered null.
```

###Save to the database in chunks rather than item by item

Inherit from SqlSpider and..

In settings

```python
DEFAULT_CHUNKSIZE = 500

CHUNKSIZE_BY_TABLE = {'mytable': 1000, 'othertable': 250}
```

If an error occurs while saving a chunk to the db it will try and save
each item one at a time


Gotchas
========

###If you subclass either item_scraped or spider_closed make sure to call super!

```python

class MySpider(SqlSpider):
        
        def parse(self, response):
                pass

        def spider_closed(self, spider, reason):
                super(MySpider, self).spider_closed(spider, reason)
                self.log("Log some really important custom stats")
```

Be Careful with other Mixins.  The inheritance structure can get a little messy. If a class early in the mro subclasses item_scraped
and does not call super the item_scraped method of SqlSpider will never get called.


Other Methods of sqlitem
========

###sqlitem.null_required_fields

* returns a set of the database key names that are are marked not nullable
 and the corresponding data in the item is null.

###sqlitem.null_primary_key_fields

* returns a set of the primary key names
where the corresponding data in the item is null.

###sqlitem.primary_keys

###sqlitem.required_keys


ToDo
=======
* Continuous integration Tests
