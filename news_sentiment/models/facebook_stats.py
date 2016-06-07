"""

"""
from news_sentiment import db
from datetime import datetime


class FacebookStats(db.EmbeddedDocument):
    date = db.DateTimeField(default=datetime.utcnow)
    likeCount = db.IntField(required=True)
    commentCount = db.IntField()
    clickCount = db.IntField()
    shareCount = db.IntField()
    totalCount = db.IntField()
