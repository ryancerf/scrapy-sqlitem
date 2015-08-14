import os

from sqlalchemy import create_engine, MetaData

engine = create_engine(os.getenv('DATABASE_URI'))
metadata = MetaData()


def init_db():
    metadata.create_all(engine)
