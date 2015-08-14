from scrapy import Field

from scrapy_sqlitem import SqlItem
from . models import User, Address


class UserItem(SqlItem):
    sqlmodel = User


class AddressItem(SqlItem):
    sqlmodel = Address


class NewFieldItemUser(SqlItem):
    sqlmodel = User
    first_joined = Field()


class OverrideFieldItemUser(SqlItem):
    sqlmodel = User
    id = Field()
