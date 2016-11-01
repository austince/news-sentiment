"""

"""
import requests
from datetime import datetime
from ssl import SSLError
import boto3
import facebook
from sentiment_scraper import db
from sentiment_scraper.models.facebook_stats import FacebookStats
from sentiment_scraper.models.text_analysis import TextAnalysis

ARTICLE_BUCKET_NAME = 'scraped-articles'
ARTICLE_RAW_PREFIX = 'raw/'
ARTICLE_TEXTS_PREFIX = 'texts/'
TEXT_SEPARATOR = ' % '


class ArticleQuerySet(db.QuerySet):
    def get_linked(self, numLinks=1):
        return self.filter(relatedArticles__size=numLinks)

    def get_returnable(self):
        return self.exclude('relatedLinks')

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
    # These have been deprecated because they bloat the database
    # Should be moved into a static storage service (s^3???)
    # visibleTexts = db.ListField(db.StringField())
    # rawPage = db.StringField()

    textAnalysis = db.EmbeddedDocumentField(TextAnalysis, default=None)
    fbStats = db.EmbeddedDocumentListField(FacebookStats, default=[])
    textIsAnalyzed = db.BooleanField(default=False)
    fbIsAnalyzed = db.BooleanField(default=False)
    relatedAnalyzed = db.BooleanField(default=False)

    def saveRawPage(self, rawPage):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(ARTICLE_BUCKET_NAME)
        bucket.put_object(
            Body=str(rawPage),
            Key=str(ARTICLE_RAW_PREFIX + str(self.id))
        )

    def getArticleText(self):
        s3 = boto3.resource('s3')
        fileObj = s3.Object(ARTICLE_BUCKET_NAME, ARTICLE_TEXTS_PREFIX + str(self.id))
        fileReq = fileObj.get()
        return fileReq['Body'].read()

    def saveArticleText(self, articleTexts):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(ARTICLE_BUCKET_NAME)
        bucket.put_object(
            Body=str(TEXT_SEPARATOR.join(articleTexts)),
            Key=str(ARTICLE_TEXTS_PREFIX + str(self.id))
        )

    @staticmethod
    def by_date():
        articles = list(Article.objects())
        articles.sort(key=lambda x: x.date)
        return articles

    def analyzeSentiment(self, text=None, saveOnFinish=False):
        """
        -- Uses https://market.mashape.com/japerk/text-processing for sentiment.
            45000 / mo --
        Uses https://market.mashape.com/sentinelprojects/skyttle2-0 for tags.
            500 / day LIMIT
        :return:
        """
        print("Analyzing sentiment for " + self.title)
        # Buffer each text with a space
        if text is None:
            # Get a copy from s3
            text = self.getArticleText()

        # Only use the first 10,000 chars limit for now
        # Will aggregate later
        if len(text) > 10000:
            text = text[:10000]

        try:
            response = requests.post(
                "https://sentinelprojects-skyttle20.p.mashape.com/",
                headers={
                    "X-Mashape-Key": "aT640lneftmshsi5erOiJq4hxgQIp1Tdrimjsn4NpRuAEJcPzy",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "annotate": 1,
                    "keywords": 1,
                    "lang": "en",
                    "sentiment": 1,
                    "text": text
                },
                timeout=5
            )
        except SSLError as ex:
            print(str(ex))
            # Must break out if we cannot get a response :(
            return

        # Break into terms and sentiment
        if response.ok:
            data = response.json()
            warnings = data['warnings']
            # The meat of the response
            sentimentData = data['docs'][0]
            for term in sentimentData['terms']:
                del term['id']  # No one wants yo id CT

            analysis = TextAnalysis(
                pos=float(sentimentData['sentiment_scores']['pos']),
                neutral=float(sentimentData['sentiment_scores']['neu']),
                neg=float(sentimentData['sentiment_scores']['neg']),
                terms=sentimentData['terms'],
                warnings=warnings
            )
            try:
                analysis.validate()
                self.textAnalysis = analysis
                self.textIsAnalyzed = True

                if saveOnFinish:
                    self.save()
            except db.ValidationError:
                print("Validation error")
        else:
            print("Error w/ Sentiment Analysis request.")
            print(response.status_code)
            print(response.content)

    def analyzeFacebook(self, saveOnFinish=False):
        """
        Uses http://api.facebook.com/restserver.php?method=links.getStats&format=json&urls={articleUrl}
        Assumes the Article is unique in the database
        :return:
        """
        print("Analyzing facebook for " + self.title)
        try:
            graph = facebook.GraphAPI(access_token='333900273640148|2PBC4LMBuWk4jDNyrP5a5JIRH-A', version='2.7')
            data = graph.get_object(id=self.url)

            # Graph API deprecated :(
            fbStats = FacebookStats()
            fbStats.fromGraphData(data)
            fbStats.validate()
            self.fbStats.append(fbStats)
            self.fbIsAnalyzed = True

            if saveOnFinish:
                self.save()
        except db.ValidationError:
            print("Validation error")
        except facebook.GraphAPIError as ex:
            print('Graph API Error!')
            print(ex)
