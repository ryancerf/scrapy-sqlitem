from sqlalchemy import Column, Integer, String

from tests.database import Base


class User(Base):
    __tablename__ = 'user2'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    full_name = Column(String)

class Address(Base):
    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    email_address = Column(String, primary_key=True, nullable=False)
    time = Column(String, nullable=False)
    link_text = Column(String)
