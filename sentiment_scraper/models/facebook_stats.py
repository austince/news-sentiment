"""

"""
import os
import facebook
from datetime import datetime
from sentiment_scraper import db

FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN', '')


class FacebookStats(db.EmbeddedDocument):
    date = db.DateTimeField(default=datetime.utcnow)
    likeCount = db.IntField(default=0)
    commentCount = db.IntField(default=0)
    shareCount = db.IntField(default=0)
    totalCount = db.IntField(default=0)

    def fromGraphData(self, data):
        if 'og_object' in data and 'engagement' in data['og_object']:
            self.likeCount = data['og_object']['engagement']['count']
            totalCount = self.likeCount # If for some reason share wasn't returned

        if 'share' in data:
            self.commentCount = data['share']['comment_count']
            # The share count is an approx aggregation of comments + likes + shares, misleadingly so.
            # shareCount == totalCount
            totalCount = data['share']['share_count']
            self.shareCount += (totalCount - self.commentCount - self.likeCount)

            # Not a fan of  this graph API vs the old REST one. Less accurate.
            if self.shareCount < 0:
                self.shareCount = 0

        self.totalCount = totalCount

    @staticmethod
    def fromUrl(url):
        # Old Rest API deprecated :(
        try:
            graph = facebook.GraphAPI(access_token=FB_ACCESS_TOKEN, version='2.7')
            data = graph.get_object(id=url, fields=\
                'id,'
                'share,'    # Ask for share object
                'og_object{engagement{count}}'   # Specifically as for like count
            )
        except facebook.GraphAPIError as ex:
            print('Graph API Error!')
            print(ex)
            return None

        stats = FacebookStats()
        stats.fromGraphData(data)
        return stats
