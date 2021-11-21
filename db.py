from peewee import SqliteDatabase, Model, AutoField, CharField
from peewee import DateTimeField
from playhouse.sqlite_ext import JSONField
from tools import *
import datetime

db = SqliteDatabase('database.db', pragmas={'foreign_keys': 1})

class BaseModel(Model):

    @classmethod
    def contains(cls, condition=None, **kwargs):
        if condition is None:
            return cls.get_or_none(**kwargs) is not None
        return cls.get_or_none(condition) is not None

    class Meta:
        database = db


class History(BaseModel):
    id = AutoField()
    image_name = CharField(8)
    datetime = DateTimeField(default=datetime.datetime.now)
    boxes = JSONField(default=[])
    
db.connect()
db.create_tables([History])


if __name__ == '__main__':
    pass
