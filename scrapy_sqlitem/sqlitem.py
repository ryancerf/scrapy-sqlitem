from scrapy.item import Field, Item, ItemMeta


class SqlAlchemyItemMeta(ItemMeta):

    def __new__(mcs, class_name, bases, attrs):
        cls = super(SqlAlchemyItemMeta, mcs).__new__(mcs, class_name, bases, attrs)

        if cls.sqlmodel is not None:
            if cls.sqlmodel.__class__.__name__ == 'Table':
                cls.table = cls.sqlmodel
            elif cls.sqlmodel.__class__.__name__ == 'DeclarativeMeta':
                cls.table = cls.sqlmodel.__dict__['__table__']

            cls.primary_keys = cls.table.primary_key.columns.keys()
            cls.required_keys = [col.name for col
                    in cls.table.columns.values()
                    if not col.nullable]
            cls._model_fields = []
            for col_name in cls.table.columns.keys():
                if col_name not in cls.fields:
                    cls.fields[col_name] = Field()
                    cls._model_fields.append(col_name)
        return cls


class SqlItem(Item):

    __metaclass__ = SqlAlchemyItemMeta

    sqlmodel = None

    def __init__(self, *args, **kwargs):
        super(SqlItem, self).__init__(*args, **kwargs)

    def commit_item(self, engine=None):
        """ Save to Database using given engine """
        with engine.begin() as conn:
            ins = self._generate_insert()
            pk = conn.execute(ins)
            return pk

    def _get_modelargs(self):
        return dict((k, self.get(k)) for k in self._values
                if k in self._model_fields)

    def _generate_insert(self):
        modelargs = self._get_modelargs()
        return self.table.insert().values(**modelargs)

    @property
    def null_primary_key_fields(self):
        """ set of all fields marked as primary keys in db model
        That are currently not defined """
        self._null_primary_key_fields = {pk for pk in self.primary_keys if self.get(pk) is None}
        return self._null_primary_key_fields

    @property
    def null_required_fields(self):
        """ set of all fields marked as not nullable in db model
        That are currently not defined """
        self._null_required_fields = {key for key in self.required_keys if self.get(key) is None}
        return self._null_required_fields

    def __getattr__(self, name):
        if name in self.fields:
            raise AttributeError("Use item[%r] to get field value" % name)
        #override this annoying error from scrapy.
        # raise AttributeError(name)
