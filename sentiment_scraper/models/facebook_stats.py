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

    @staticmethod
    def from_graph_data(data):
        """

        :param data: Facebook GraphObject
        :return: FacebookStats
        """
        stats = FacebookStats()
        total_count = 0

        if 'og_object' in data and 'engagement' in data['og_object']:
            stats.likeCount = data['og_object']['engagement']['count']
            total_count = stats.likeCount  # If for some reason share wasn't returned
        # Should always be true
        if 'share' in data:
            stats.commentCount = data['share']['comment_count']
            # The share count is an approx aggregation of comments + likes + shares, misleadingly so.
            # shareCount == total_count
            total_count = data['share']['share_count']
            stats.shareCount += (total_count - stats.commentCount - stats.likeCount)

            # Not a fan of  this graph API vs the old REST one. Less accurate.
            if stats.shareCount < 0:
                stats.shareCount = 0

        stats.totalCount = total_count
        return stats

    @staticmethod
    def from_url(url):
        """

        :param url: str
        :return: FacebookStats
        """
        # Old Rest API deprecated :(
        try:
            graph = facebook.GraphAPI(access_token=FB_ACCESS_TOKEN, version='2.7')
            data = graph.get_object(id=url, fields=
                                    'id,'
                                    'share,'    # Ask for share object
                                    'og_object{engagement{count}}'   # Specifically as for like count
                                    )
        except facebook.GraphAPIError as ex:
            print('Graph API Error!')
            print(ex)
            return None

        return FacebookStats.from_graph_data(data)
