"""

"""
from sentiment_scraper import db
from datetime import datetime


class FacebookStats(db.EmbeddedDocument):
    date = db.DateTimeField(default=datetime.utcnow)
    likeCount = db.IntField()
    commentCount = db.IntField()
    shareCount = db.IntField()
    totalCount = db.IntField()

    def __init__(self, data=None):
        super().__init__()
        if data is not None:
            totalCount = 0
            if 'engagement' in data['og_object']:
                self.likeCount = data['engagement']['count']
                totalCount += self.likeCount

            if 'share' in data:
                self.commentCount = data['share']['comment_count']
                self.shareCount = data['share']['share_count']
                totalCount += self.commentCount + self.shareCount

            self.totalCount = totalCount
