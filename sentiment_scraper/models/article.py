"""

"""
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from sentiment_scraper import db
from sentiment_scraper.models.facebook_stats import FacebookStats
from sentiment_scraper.models.text_analysis import TextAnalysis

ARTICLE_BUCKET_NAME = 'scraped-articles'
ARTICLE_RAW_PREFIX = 'raw/'
ARTICLE_TEXTS_PREFIX = 'texts/'
TEXT_SEPARATOR = ' % '


class ArticleQuerySet(db.QuerySet):
    """

    """
    def get_linked(self, num_links=1):
        return self.filter(slice__relatedArticles=num_links)

    def get_returnable(self):
        return self.exclude('relatedLinks')

    def get_between(self, start_date=datetime.min, end_date=datetime.max):
        if start_date is None:
            start_date = datetime.min
        if end_date is None:
            end_date = datetime.max
        return self.filter(date__gte=start_date, date__lte=end_date)

    def get_before(self, date):
        return self.filter(date__lte=date)

    def get_after(self, date):
        return self.filter(date__gte=date)


class Article(db.DynamicDocument):
    meta = {
        'queryset_class': ArticleQuerySet,
        'indexes': [
            'title',
            'site',
            'newsEdition',
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
    # articleText = db.ListField(db.StringField())
    # rawPage = db.StringField()

    textAnalysis = db.EmbeddedDocumentField(TextAnalysis, default=None)
    fbStats = db.EmbeddedDocumentListField(FacebookStats, default=[])
    textIsAnalyzed = db.BooleanField(default=False)
    fbIsAnalyzed = db.BooleanField(default=False)
    relatedAnalyzed = db.BooleanField(default=False)

    def save_raw_page(self, raw_page):
        """
        Saves to s3 storage
        :param raw_page:
        :return:
        """
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(ARTICLE_BUCKET_NAME)
        bucket.put_object(
            Body=str(raw_page),
            Key=str(ARTICLE_RAW_PREFIX + str(self.id))
        )

    def load_text(self):
        self.articleText = self.get_article_text()

    def get_article_text(self):
        """
        Get's the text content from S3 storage
        :return:
        """
        s3 = boto3.resource('s3')
        file_obj = s3.Object(ARTICLE_BUCKET_NAME, ARTICLE_TEXTS_PREFIX + str(self.id))
        file_req = file_obj.get()
        return file_req['Body'].read().decode("utf-8")

    def save_article_text(self, article_texts):
        """
        Saves to S3 storage
        :param article_texts: list of strings
        :return:
        """
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(ARTICLE_BUCKET_NAME)
        # Join the article text with a delimiter so we can parse it later if need be
        bucket.put_object(
            Body=str(TEXT_SEPARATOR.join(article_texts)),
            Key=str(ARTICLE_TEXTS_PREFIX + str(self.id))
        )

    @staticmethod
    def by_date():
        articles = list(Article.objects())
        articles.sort(key=lambda x: x.date)
        return articles

    def analyze_sentiment(self, text=None, save_on_finish=False):
        """
        -- Uses https://market.mashape.com/japerk/text-processing for sentiment.
            45000 / mo --
        Uses https://market.mashape.com/sentinelprojects/skyttle2-0 for tags.
            500 / day LIMIT
        :param text: str | [None]
        :param save_on_finish: bool | [False]
        :return:
        """
        print("Analyzing sentiment for " + str(self.title))
        # Buffer each text with a space
        try:
            if text is None:
                # Get a copy from s3
                text = self.get_article_text()

            analysis = TextAnalysis.from_text(text)

            if analysis is not None:
                analysis.validate()
                self.textAnalysis = analysis
                self.textIsAnalyzed = True

            if save_on_finish:
                self.save()
        except db.ValidationError:
            print("Validation error")
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                # If this was improperly stored, delete it from the database
                # Could rescrape, but don't want to get here in the first place
                print("Can't find the texts for: " + str(self.title))
                print("Key: " + ex.response['Error']['Key'])
                self.delete()
            else:
                print(ex)

    def analyze_facebook(self, save_on_finish=False):
        """
        Uses http://api.facebook.com/restserver.php?method=links.getStats&format=json&urls={articleUrl}
        Assumes the Article is unique in the database
        :param save_on_finish: bool | [False]
        :return:
        """
        print("Analyzing facebook for " + str(self.title))
        fb_stat = FacebookStats.from_url(self.url)
        try:
            if fb_stat is not None:
                fb_stat.validate()
                self.fbStats.append(fb_stat)
                self.fbIsAnalyzed = True

            if save_on_finish:
                self.save()
        except db.ValidationError:
            print("Validation error")
