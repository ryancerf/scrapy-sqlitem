import time

from collections import defaultdict
from scrapy import Spider, signals

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


class SqlMixin(object):
    """ Mixin to save sqlitems to database """

    def setup_sql(self):
        self.crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)
        self.crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        self.crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)

        self._pending_db = defaultdict(list)
        self.engine = create_engine(self.settings.get('DATABASE_URI'))

        self._save_frequency = self.settings.get('SAVE_FREQUENCY_SECONDS', None)
        if self._save_frequency:
            now = time.time()
            self._next_save = defaultdict(lambda: now + self._save_frequency)

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
            self.logger.warning("Bulk insert of %s rows failed for table: %s will retry individually, error: %s " % (str(len(to_insert)), table.name, str(e)))
            for row in to_insert:
                try:
                    ins_stmt = self._get_insert_stmt(table, row)
                    self._insert(ins_stmt)
                except SQLAlchemyError as e:
                    self.logger.error("Individual insert failed for table: %s  error: %s" % (table.name, str(e)))
        finally:
            self._pending_db.pop(table, None)
            if self._save_frequency:
                self._next_save[table] = time.time() + self._save_frequency

    def spider_idle(self):
        """ Set SAVE_FREQUENCY_SECONDS and
        spider will save unsaved items to the database after that many seconds
        regardless how recently items were saved
        useful with redis spider (because redis spider does not close)"""
        if self._save_frequency:
            for table in self._pending_db.keys():
                if time.time() > self._next_save[table]:
                    self._save_pending(table)

        try:
            super(SqlMixin, self).spider_idle()
        except AttributeError:
            pass

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
                self._save_pending(item.table)

    def _save_pending(self, table):
        to_insert = self._pending_db[table]
        if to_insert:
            self._bulk_insert(table, to_insert)

    def spider_closed(self, spider, reason):
        try:
            super(SqlMixin, self).spider_closed(spider, reason)
        except AttributeError:
            pass

        for table in self._pending_db.keys():
            self._save_pending(table)


class SqlSpider(SqlMixin, Spider):

    def _set_crawler(self, crawler):
        super(SqlSpider, self)._set_crawler(crawler)
        self.setup_sql()
