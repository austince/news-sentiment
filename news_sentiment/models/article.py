"""

"""

from news_sentiment import db
from facebook_stats import FacebookStats
from text_analysis import TextAnalysis
import unirest
from datetime import datetime
from ssl import SSLError
from urllib2 import URLError


class ArticleQuerySet(db.QuerySet):
    def get_linked(self, numLinks=1):
        return self.filter(relatedArticles__size=numLinks)

    def get_returnable(self):
        return self.exclude('rawPage').exclude('visibleTexts').exclude('relatedLinks')

    def get_without_raw(self):
        return self.exclude('rawPage')

    def get_before(self, date, sortOrder='-'):
        return self.filter(date__lte=date).order_by(sortOrder+'date')

    def get_after(self, date, sortOrder='-'):
        return self.filter(date__gte=date).order_by(sortOrder+'date')

    def get_positive(self, orderBy='date', sortOrder='-'):
        return self.filter(fbIsAnalyzed=True).order_by(sortOrder + orderBy)


class Article(db.DynamicDocument):
    meta = {
        'queryset_class': ArticleQuerySet,
        'indexes': [
            'title',
            '#date'
        ]
    }
    title = db.StringField(unique=True)
    # Defaults to right now. Should scrape the exact date/time
    date = db.DateTimeField(default=datetime.utcnow)
    url = db.URLField()
    site = db.StringField()
    relatedLinks = db.ListField(db.URLField())
    relatedArticles = db.ListField(db.ReferenceField('Article', reverse_delete_rule=db.PULL), default=[])
    newsEdition = db.StringField()
    visibleTexts = db.ListField(db.StringField())
    rawPage = db.StringField()

    textAnalysis = db.EmbeddedDocumentField(TextAnalysis, default=None)
    fbStats = db.EmbeddedDocumentListField(FacebookStats, default=[])
    textIsAnalyzed = db.BooleanField(default=False)
    fbIsAnalyzed = db.BooleanField(default=False)
    relatedAnalyzed = db.BooleanField(default=False)

    # @db.queryset_manager
    # def by_date(doc_cls, queryset):
    #     return queryset.order_by('-date')

    @staticmethod
    def by_date():
        articles = list(Article.objects())
        articles.sort(key=lambda x: x.date)
        return articles

    def analyzeSentiment(self, saveOnFinish=False):
        """
        -- Uses https://market.mashape.com/japerk/text-processing for sentiment.
            45000 / mo --
        Uses https://market.mashape.com/sentinelprojects/skyttle2-0 for tags.
            500 / day LIMIT
        :return:
        """
        print "Analyzing sentiment for " + self.title

        # Buffer each text with a space
        # Create a copy
        textToProcess = list(self.visibleTexts)
        # Add a single space to buffer each text
        for i in range(0, len(textToProcess)):
            textToProcess[i] += ' '
        # Create one long string of all the visible text on the page for processing
        textToProcess = ''.join(textToProcess)

        unirest.timeout(5)
        try:
            response = unirest.post(
                "https://sentinelprojects-skyttle20.p.mashape.com/",
                headers={
                    "X-Mashape-Key": "aT640lneftmshsi5erOiJq4hxgQIp1Tdrimjsn4NpRuAEJcPzy",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                params={
                    "annotate": 1,
                    "keywords": 1,
                    "lang": "en",
                    "sentiment": 1,
                    "text": textToProcess
                }
            )
        except SSLError as ex:
            print "SSLError " + ex.message
            # Must break out if we cannot get a response :(
            return

        # Break into terms and sentiment
        if response.code == 200:
            warnings = response.body['warnings']
            # The meat of the response
            data = response.body['docs'][0]
            for term in data['terms']:
                del term['id']  # No one wants yo id CT

            analysis = TextAnalysis(
                pos=float(data['sentiment_scores']['pos']),
                neutral=float(data['sentiment_scores']['neu']),
                neg=float(data['sentiment_scores']['neg']),
                terms=data['terms'],
                warnings=warnings
            )
            try:
                analysis.validate()
                self.textAnalysis = analysis
                self.textIsAnalyzed = True

                if saveOnFinish:
                    self.save()
            except db.ValidationError:
                print "Validation error"
        else:
            print "Error w/ Sentiment Analysis request."
            print response.code
            print response.body

    def analyzeFacebook(self, saveOnFinish=False):
        """
        Uses http://api.facebook.com/restserver.php?method=links.getStats&format=json&urls={articleUrl}
        Assumes the Article is unique in the database
        :return:
        """
        print "Analyzing facebook for " + self.title
        unirest.timeout(5)
        # Could also send a list of urls off to process all at once
        try:
            response = unirest.get(
                'http://api.facebook.com/restserver.php?method=links.getStats&format=json&urls=' + str(self.url)
            )
        except URLError as ex:
            print 'Failed to analyze facebook for ' + self.title
            print 'URLError: ' + str(ex)
            print 'Articles url: ' + self.url
            return

        if response.code == 200:
            # The meat of the response
            data = response.body[0]

            fbStats = FacebookStats(
                likeCount=int(data['like_count']),
                commentCount=int(data['comment_count']),
                clickCount=int(data['click_count']),
                shareCount=int(data['share_count']),
                totalCount=int(data['total_count'])
            )

            try:
                fbStats.validate()
                self.fbStats.append(fbStats)
                self.fbIsAnalyzed = True

                if saveOnFinish:
                    self.save()
            except db.ValidationError:
                print "Validation error"

        else:
            print "Error w/ Facebook Link Analysis request."
            print response.code
            print response.body
