from collections import defaultdict
import unittest
import time

from scrapy_sqlitem import SqlMixin

from . database import engine, init_db

from . items import AddressItem, UserItem


class SqlMixinTestCase(unittest.TestCase):

    def setUp(self):
        init_db()

        class Logger():
            def warn(self, message):
                print(message)

            def error(self, message):
                print(message)

        def log(message):
            print message

        self.spider = SqlMixin()
        self.spider.engine = engine
        self.spider.settings = {}
        self.spider._pending_db = defaultdict(list)
        self.spider._save_frequency = 0.5
        self.now = time.time()
        self.spider._next_save = defaultdict(lambda: self.now + self.spider._save_frequency)
        self.spider.logger = Logger()

    def tearDown(self):
        engine.execute(""" delete from user2""")
        engine.execute(""" delete from address""")

    def test_individual_insert(self):
        for i in range(10):
            item = UserItem(dict(id=i))
            self.spider.item_scraped(item, None, None)

        self.assertEqual((10,), engine.execute(""" select count(*) from user2 """).fetchone())

    def test_bulk_insert(self):
        self.spider.settings['DEFAULT_CHUNKSIZE'] = 6
        for i in range(14):
            item = UserItem(dict(id=i))
            self.spider.item_scraped(item, None, None)

        self.assertEqual((12,), engine.execute(""" select count(*) from user2 """).fetchone())
        self.assertEqual(2, len(self.spider._pending_db[item.table]))

    def test_bulk_insert_failure(self):
        self.spider.settings['DEFAULT_CHUNKSIZE'] = 6
        for i in range(14):

            if i == 6:
                i = 5

            item = UserItem(dict(id=i))
            self.spider.item_scraped(item, None, None)
        self.assertEqual((11,), engine.execute(""" select count(*) from user2 """).fetchone())
        self.assertEqual(2, len(self.spider._pending_db[item.table]))

    def test_custom_chunksize(self):
        self.spider.settings['CHUNKSIZE_BY_TABLE'] = dict(address=10)
        for i in range(14):
            item = UserItem(dict(id=i))
            self.spider.item_scraped(item, None, None)

            item2 = AddressItem(dict(id=i, email_address='non_nullemail', time='atime'))
            self.spider.item_scraped(item2, None, None)

        self.assertEqual((14,), engine.execute(""" select count(*) from user2 """).fetchone())

        self.assertEqual((10,), engine.execute(""" select count(*) from address """).fetchone())
        self.assertEqual(4, len(self.spider._pending_db[item2.table]))

    def test_save_frequency_settings(self):
        time.sleep(.1)
        self.spider.settings['CHUNKSIZE_BY_TABLE'] = dict(address=10)
        for i in range(4):
            item2 = AddressItem(dict(id=i, email_address='non_nullemail', time='atime'))
            self.spider.item_scraped(item2, None, None)

        #should not do anything not enough time passed
        self.spider.spider_idle()
        self.assertEqual(4, len(self.spider._pending_db[item2.table]))

        #should have saved to db and updated next save
        time.sleep(0.5)
        self.spider.spider_idle()

        # pending db clened out
        self.assertEqual([], self.spider._pending_db.keys())

        last_save = time.time()
        self.assertEqual(0, len(self.spider._pending_db[item2.table]))
        self.assertEqual((4,), engine.execute(""" select count(*) from address """).fetchone())

        #check that next save time is relative to last save
        self.assertAlmostEqual(last_save + 0.5, self.spider._next_save[item2.table], places=3)

        # check next save time for a non existant item is relative to original time
        self.assertEqual(self.now + 0.5, self.spider._next_save['non_existant_table'])
