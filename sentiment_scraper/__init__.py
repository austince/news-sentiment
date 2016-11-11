"""

"""

import time
from datetime import datetime
import threading
import mongoengine as db
from pymongo import errors
from sentiment_scraper.models.article import Article

from sentiment_scraper.utils import article_matcher
from sentiment_scraper.utils import article_scraper


def update_matches(articles, analyze_all=False):
    """
    Updates the matching related articles for all articles. Mainly used to update the database.
    :param analyze_all: bool
    :param articles: articles, a list of Articles
    :return:
    """
    print("Updating matches for " + str(len(articles)) + " articles")
    for article in articles:
        if analyze_all or not article.relatedAnalyzed:
            # Only update if the article hasn't been processed so far, or if we want to overrided that
            article_matcher.find_matches(article)
            article.save()
        else:
            # print("Already processed!")
            pass


def update_articles_analysis(articles):
    """
        Reanalyzes articles with time dependencies or if they have not already been analyzed
        Aka: Facebook
        :param: articles, a list of Articles
    """
    print("Updating " + str(len(articles)) + " articles")
    for article in articles:
        if not article.textIsAnalyzed:
            # Try to analyze the text again if the first time failed
            article.analyze_sentiment()
        article.analyze_facebook()
        article.save()


def update():
    start_time = datetime.utcnow()
    # Get a snapshot of the current articles
    # Can't get overwritten by the scraper
    articles = Article.objects()
    update_articles_analysis(articles)
    update_matches(articles)
    print("Time to update articles: " + str(datetime.utcnow() - start_time))


def scrape():
    editions = ['us', 'uk']
    start_time = datetime.utcnow()
    for edition in editions:
        articles = article_scraper.scrape_google_news(edition)
        print("Scrapped: " + str(len(articles)) + " articles from " + edition + " Google News")
        print("Time to scrape Google " + edition + " news: " + str(datetime.utcnow() - start_time))

    print("Total new article crawl time: " + str(datetime.utcnow() - start_time))


def run(sleep_time=None, mode='both'):
    while True:
        start_time = datetime.utcnow()
        try:
            db.connect('newsSentiment')
        except errors.ConnectionFailure:
            print("Connection failure")

        update_thread = None
        scrape_thread = None

        print("Running in mode: " + mode)

        if mode == 'both' or mode == 'update':
            update_thread = threading.Thread(target=update)
            update_thread.start()
        if mode == 'both' or mode == 'scrape':
            scrape_thread = threading.Thread(target=scrape)
            scrape_thread.start()

        # Wait at most 60 seconds for the threads to end
        if update_thread is not None:
            update_thread.join(60)
        if scrape_thread is not None:
            scrape_thread.join(60)

        print("\n Total time: " + str(datetime.utcnow() - start_time))

        print("All done for now!")

        if sleep_time is not None:
            time.sleep(sleep_time)
        else:
            break
