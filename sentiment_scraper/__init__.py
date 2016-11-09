"""

"""

import time
import mongoengine as db
from pymongo import errors
from sentiment_scraper.models.article import Article
from datetime import datetime

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


def run(sleep_time=None):
    start_time = datetime.utcnow()
    try:
        db.connect('newsSentiment')
    except errors.ConnectionFailure:
        print("Connection failure")

    articles = Article.objects()
    update_articles_analysis(articles)
    update_matches(articles)
    print("Time to update articles: " + str(datetime.utcnow() - start_time))

    google_news_scrape_start_time = datetime.utcnow()
    articles = article_scraper.scrape_google_news('us')
    print("Scrapped: " + str(len(articles)) + " articles from US Google News")
    print("Time to scrape Google us news: " + str(datetime.utcnow() - google_news_scrape_start_time))

    print("Total new article crawl time: " + str(datetime.utcnow() - google_news_scrape_start_time))

    print("\n Total time: " + str(datetime.utcnow() - start_time))

    print("All done for today!")
    if sleep_time is not None:
        time.sleep(sleep_time)


if __name__ == "__main__":
    run()
    # run(86400)  # 60 * 60 * 24
