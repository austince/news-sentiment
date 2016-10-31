"""

"""

import time
import mongoengine as db
from pymongo import errors
from sentiment_scraper.models.article import Article
from datetime import datetime, timedelta

from sentiment_scraper.utils import articleMatcher
from sentiment_scraper.utils import articleScraper


def updateMatches(articles, analyzeAll=False):
    """
    Updates the matching related articles for all articles. Mainly used to update the database.
    :param articles: articles, a list of Articles
    :return:
    """
    print("Updating matches for " + str(len(articles)) + " articles")
    for article in articles:
        if analyzeAll or not article.relatedAnalyzed:
            # Only update if the article hasn't been processed so far, or if we want to overrided that
            articleMatcher.findMatches(article)
            article.save()
        else:
            # print("Already processed!")
            pass


def updateAnalysisArticles(articles):
    """
        Reanalyzes articles with time dependencies or if they have not already been analyzed
        Aka: Facebook
        :param: articles, a list of Articles
    """
    print("Updating " + str(len(articles)) + " articles")
    for article in articles:
        if not article.textIsAnalyzed:
            # Try to analyze the text again if the first time failed
            article.analyzeSentiment()
        article.analyzeFacebook()
        article.save()


def run(sleepTime=None):
    startTime = datetime.utcnow()
    try:
        db.connect('newsSentiment')
    except errors.ConnectionFailure:
        print("Connection failure")

    articles = Article.objects()
    updateAnalysisArticles(articles)
    updateMatches(articles)
    print("Time to update articles: " + str(datetime.utcnow() - startTime))

    googleNewsScrapeStartTime = datetime.utcnow()
    articles = articleScraper.scrapeGoogleNews('us')
    print("Time to scrape Google us news: " + str(datetime.utcnow() - googleNewsScrapeStartTime))

    print("Total new article crawl time: " + str(datetime.utcnow() - googleNewsScrapeStartTime))

    print("\n Total time: " + str(datetime.utcnow() - startTime))

    print("All done for today!")
    if sleepTime is not None:
        time.sleep(sleepTime)


if __name__ == "__main__":
    run()
    # run(86400)  # 60 * 60 * 24

