import requests
from urllib.error import URLError
from bs4 import BeautifulSoup
from termcolor import colored
from sentiment_scraper import db
from sentiment_scraper.models.article import Article
import time


def find_matches(article, is_saved=False):
    """
    Tries to find connecting articles from the related links provided by google
    :param is_saved: bool
    :param article: Article
    :return:
    """
    print("Trying to match " + str(len(article.relatedLinks)) + " articles for " + article.title)
    for link in article.relatedLinks:
        try:
            article_resp = requests.get(link)
        except URLError as ex:
            print("Error in getting related link: " + str(ex))
            continue

        if article_resp.ok:
            source = article_resp.content
            soup = BeautifulSoup(source, 'html.parser')
            article_list_soup = soup.findAll('div', attrs={'class': 'blended-wrapper'})
            for relatedArticleSoup in article_list_soup:
                related_article_title = relatedArticleSoup.find('span', 'titletext').text
                try:
                    related_article = Article.objects.get(title=related_article_title)
                except db.DoesNotExist:
                    # Onto the next article
                    # should we then scrape this article and then add it to the database?
                    continue

                if related_article not in article.relatedArticles:
                    print("Found a new related article: " + related_article_title + " for " + article.title)
                    if is_saved:
                        # The preferred method but can only be used on a saved doc
                        article.update(push__relatedArticles=related_article)
                    else:
                        article.relatedArticles.append(related_article)

            article.relatedAnalyzed = True
        else:
            print("Couldn't make a request for the related article url ")
            print("Error code: " + str(article_resp.status_code))
            if article_resp.status_code == 503:
                print(colored("Google is probably mad. Stop for 5 secs.", 'red'))
                time.sleep(5)
