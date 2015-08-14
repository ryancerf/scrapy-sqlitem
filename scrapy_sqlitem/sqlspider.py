from collections import defaultdict
from scrapy import Spider, signals

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


class SqlMixin(object):
    """ Mixin to save sqlitems to database """

    def setup_sql(self):
        self.crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)
        self.crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)

        self._pending_db = defaultdict(list)
        self.engine = create_engine(self.settings.get('DATABASE_URI'))

    def _insert(self, insert_stmt):
        with self.engine.begin() as conn:
            conn.execute(insert_stmt)

    def _get_insert_stmt(self, table, to_insert):
        return table.insert().values(to_insert)

    def _bulk_insert(self, table, to_insert):
        try:
            ins_stmt = self._get_insert_stmt(table, to_insert)
            self._insert(ins_stmt)
        except SQLAlchemyError as e:
            self.log("Bulk insert of %s rows failed for table: %s will retry individually" % (str(len(to_insert)), table.name))
            for row in to_insert:
                try:
                    ins_stmt = self._get_insert_stmt(table, row)
                    self._insert(ins_stmt)
                except SQLAlchemyError as e:
                    self.log("Individual insert failed for table: %s  error: %s" % (table.name, str(e)))
        finally:
            self._pending_db[table] = []

    def item_scraped(self, item, response, spider):
        """ by default will save every item """
        try:
            super(SqlMixin, self).item_scraped(item, response, spider)
        except AttributeError:
            pass

        default_chunksize = self.settings.get('DEFAULT_CHUNKSIZE', 1)
        chunksize_by_table = self.settings.get('CHUNKSIZE_BY_TABLE', {})
        chunksize = chunksize_by_table.get(item.table.name, default_chunksize)

        if chunksize == 1:
            item.commit_item(self.engine)
        else:
            to_insert = self._pending_db[item.table]
            to_insert.append(item._get_modelargs())

            if len(to_insert) >= chunksize:
                self._bulk_insert(item.table, to_insert)
                self._pending_db.items()

    def spider_closed(self, spider, reason):
        try:
            super(SqlMixin, self).spider_closed(spider, reason)
        except AttributeError:
            pass

        for table, to_insert in self._pending_db.items():
            if to_insert:
                self._bulk_insert(table, to_insert)


class SqlSpider(SqlMixin, Spider):

    def _set_crawler(self, crawler):
        super(SqlSpider, self)._set_crawler(crawler)
        self.setup_sql()
