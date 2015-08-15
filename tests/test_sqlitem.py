import unittest

from . database import engine, init_db

from . items import (UserItem,
        AddressItem,
        NewFieldItemUser,
        OverrideFieldItemUser)


class BaseTestCase(unittest.TestCase):
    def assertSortedEqual(self, first, second):
        return self.assertEqual(sorted(first), sorted(second))


class SqlAlchemyItemTestCase(BaseTestCase):
    def test_user(self):
        """ test that makes a user item with right fields"""
        u = UserItem()
        self.assertSortedEqual(u.fields.keys(), ['id', 'name', 'full_name'])

    def test_new_fields(self):
        """ test that the item makes a field for items not declared in the db model """
        u = NewFieldItemUser()
        self.assertSortedEqual(u.fields.keys(), ['id', 'name', 'full_name', 'first_joined'])

    def test_override_fields(self):
        """ test can override a field when defining a SqlAlchemyItem """
        u = OverrideFieldItemUser()
        self.assertSortedEqual(u.fields.keys(), ['id', 'name', 'full_name'])

    def test_has_keys(self):
        """ test make sure Has primary keys works, has not nullable columns works
        Test see if attributes that contain list of pks and not nullable columns"""
        u = UserItem()
        a = AddressItem()
        self.assertEqual(['id'], u.primary_keys)

        self.assertEqual(['id', 'email_address', 'time'], a.required_keys)
        self.assertEqual({'id', 'email_address'}, a.null_primary_key_fields)
        self.assertEqual({'id', 'email_address', 'time'}, a.null_required_fields)

        self.assertTrue(u.null_primary_key_fields)
        self.assertTrue(u.null_required_fields)

        a['id'] = 100
        a['email_address'] = "bigtime@thebigtime.come"
        self.assertFalse(a.null_primary_key_fields)

        self.assertEqual({'time'}, a.null_required_fields)
        a['time'] = 'one o clock'

        self.assertFalse(a.null_required_fields)


class SqlAlchemyItemDBTestCase(BaseTestCase):
    def setUp(self):
        init_db()

        engine.execute(""" CREATE TABLE IF NOT EXISTS user2
        (id INTEGER PRIMARY KEY,
        name VARCHAR,
        full_name VARCHAR)""")

        engine.execute("""INSERT INTO user2
        (id,name,full_name)
        VALUES ('1','ryan','ryan the rhino');""")

        engine.execute("""INSERT INTO user2
        (id,name)
        VALUES ('2','joe');""")

    def tearDown(self):
        engine.execute("delete from user2")

    def test_db_setup(self):
        """test database was setup properly"""
        self.assertSortedEqual((1, 'ryan', 'ryan the rhino'),
                engine.execute('select * from user2').fetchone())

    def test_commit_item(self):
        """test save fields into database """
        u = UserItem()
        u['id'] = 3
        u['name'] = 'bob'
        u['full_name'] = 'bob the bat'

        u.commit_item(engine=engine)
        self.assertSortedEqual([3, 'bob', 'bob the bat'],
                engine.execute("Select * from user2 where user2.id = 3").fetchone())

    def test_matching_dbrow_raises_nometadata(self):
        u = UserItem()
        u.table.metadata.bind = None
        with self.assertRaises(AttributeError):
            u.get_matching_dbrow()

    def test_matching_dbrow_raises_null_primary_key(self):
        u = UserItem()
        u.table.metadata.bind = 'sqlite:///'
        with self.assertRaises(ValueError):
            u.get_matching_dbrow()

    def test_matching_dbrow_pulls_matching_data(self):
        u = UserItem()
        u.table.metadata.bind = engine
        u['id'] = 2
        self.assertEqual((2, 'joe', None), u.get_matching_dbrow())

    def test_matching_dbrow_uses_cache(self):
        u = UserItem()
        u.table.metadata.bind = engine
        u['id'] = 2
        u.get_matching_dbrow()

        engine.execute("delete from user2")
        self.assertEqual((2, 'joe', None), u.get_matching_dbrow())
