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

    def fromGraphData(self, data):
        totalCount = 0
        if 'og_object' in data and 'engagement' in data['og_object']:
            self.likeCount = data['engagement']['count']
            totalCount += self.likeCount

        if 'share' in data:
            self.commentCount = data['share']['comment_count']
            self.shareCount = data['share']['share_count']
            totalCount += self.commentCount + self.shareCount

        self.totalCount = totalCount
