"""

"""
import json
from flask import Flask
from flask_restful import Api, Resource, reqparse
from flask_restful.utils import cors
from flask_mongoengine import MongoEngine
from config import Config
from news_sentiment.models.article import Article

app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
db = MongoEngine(app)

api.decorators = [cors.crossdomain(origin='*', headers=['Content-Type'])]

class ArticleRes(Resource):
    """

    """
    parser = reqparse.RequestParser()
    parser.add_argument('start', type=int)
    parser.add_argument('maxReturn', type=int)
    parser.add_argument('startDate', type=str)
    parser.add_argument('endDate', type=str)
    parser.add_argument('orderBy', type=str)
    parser.add_argument('sortOrder', type=str)

    def get(self):
        """"""
        args = self.parser.parse_args()
        start = 0
        if args.start is not None and args.start >= 0:
            start = args.start

        # default return is 50
        maxReturn = 100
        if args.maxReturn is not None:
            maxReturn = args.maxReturn

        sortOrder = '-'  # Defaults to descending
        if args.sortOrder is not None:
            if args.sortOrder == "ascending":
                sortOrder = "+"
            # Else descending

        orderBy = 'date'
        if args.orderBy is not None:
            orderBy = args.orderBy

        # Start query / filtering
        articles = Article.objects.get_returnable()

        if args.startDate is not None:
            pass

        if args.endDate is not None:
            pass

        if orderBy == 'date':
            articles = articles.get_returnable().order_by(sortOrder + 'date')
        else:
            articles = articles

        # articles = articles.get_returnable().get_linked()

        articleCount = len(articles)

        toReturn = {
            'count': articleCount,
            'start': start,
            'numReturned': maxReturn,
            'result': articles[start:start+maxReturn].to_json()
        }

        return json.dumps(toReturn), 200


api.add_resource(ArticleRes, '/articles')

if __name__ == "__main__":
    app.run()
