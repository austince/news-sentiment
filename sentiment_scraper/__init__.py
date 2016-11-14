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
    articles_scraped = 0
    for edition in editions:
        edition_start_time = datetime.utcnow()
        articles = article_scraper.scrape_google_news(edition)
        articles_scraped += len(articles)
        print("Scrapped: " + str(len(articles)) + " articles from " + edition + " Google News")
        print("Time to scrape Google " + edition + " news: " + str(datetime.utcnow() - edition_start_time))

    print("Scrapped " + str(articles_scraped) + " total.")
    print("Total new article crawl time: " + str(datetime.utcnow() - start_time))


def run(sleep_time=None, mode='both'):
    try:
        db.connect('newsSentiment')
    except errors.ConnectionFailure:
        print("Connection failure")

    while True:
        update_thread = None
        scrape_thread = None

        print("Running in mode: " + mode)

        if mode == 'both' or mode == 'update':
            update_thread = threading.Thread(target=update)
            update_thread.start()
        if mode == 'both' or mode == 'scrape':
            scrape_thread = threading.Thread(target=scrape)
            scrape_thread.start()

        if update_thread is not None:
            update_thread.join()
        if scrape_thread is not None:
            scrape_thread.join()

        if sleep_time is None or sleep_time < 0:
            print("All done for now!")
            break
        else:
            time.sleep(sleep_time)
