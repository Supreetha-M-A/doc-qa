import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://docqa:docqa_dev@localhost:5432/docqa",
)

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass