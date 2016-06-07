"""

"""
from news_sentiment import db


class TextAnalysis(db.EmbeddedDocument):
    neg = db.FloatField()
    neutral = db.FloatField()
    pos = db.FloatField()
    terms = db.ListField(db.DictField())
    warnings = db.ListField(db.StringField())
