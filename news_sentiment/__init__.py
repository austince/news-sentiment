"""

"""

import time
import mongoengine as db
from pymongo import errors
from models.article import Article
from datetime import datetime, timedelta

import articleMatcher
import articleScraper


def updateMatches(articles, analyzeAll=False):
    """
    Updates the matching related articles for all articles. Mainly used to update the database.
    :param articles: articles, a list of Articles
    :return:
    """
    print "Updating matches for " + str(len(articles)) + " articles"
    for article in articles:
        if analyzeAll or not article.relatedAnalyzed:
            # Only update if the article hasn't been processed so far, or if we want to overrided that
            articleMatcher.match(article)
            article.save()
        else:
            # print "Already processed!"
            pass


def updateAnalysisArticles(articles):
    """
        Reanalyzes articles with time dependencies or if they have not already been analyzed
        Aka: Facebook
        :param: articles, a list of Articles
    """
    print "Updating " + str(len(articles)) + " articles"
    for article in articles:
        if not article.textIsAnalyzed:
            # Try to analyze the text again if the first time failed
            article.analyzeSentiment()
        article.analyzeFacebook()
        article.save()


def run(sleepTime):
    startTime = datetime.utcnow()
    try:
        db.connect('newsSentiment')
    except errors.ConnectionFailure:
        print "Connection failure"

    articles = Article.objects()
    updateAnalysisArticles(articles)
    updateMatches(articles)
    print "Time to update articles: " + str(datetime.utcnow() - startTime)

    googleNewsScrapeStartTime = datetime.utcnow()
    articles = articleScraper.scrapeGoogleNews('us')
    print "Time to scrape Google news: " + str(datetime.utcnow() - googleNewsScrapeStartTime)
    for article in articles:
        articleProcessingStartTime = datetime.utcnow()
        try:
            # Try to save it before analyzing in case of a duplicate error
            article.save()
        except db.NotUniqueError as ex:
            print "Duplicate article already in db: " + article.title
            print "     " + ex.message
            continue

        article.analyzeSentiment()
        article.analyzeFacebook()
        article.save()
        print "Time to process article: " + str(datetime.utcnow() - articleProcessingStartTime)

    print "Total new article crawl time: " + str(datetime.utcnow() - googleNewsScrapeStartTime)

    print "\n Total time: " + str(datetime.utcnow() - startTime)

    print "All done for today!"
    # Scrape on the daily
    time.sleep(sleepTime)


if __name__ == "__main__":
    run(60 * 60 * 24)

