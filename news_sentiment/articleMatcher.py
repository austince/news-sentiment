import unirest
from urllib2 import URLError
from bs4 import BeautifulSoup
from termcolor import colored
from news_sentiment import db
from models.article import Article
import time


def match(article, isSaved=False):
    """
    Tries to find connecting articles from the related links provided by google
    :param article:
    :return:
    """
    print "Trying to match " + str(len(article.relatedLinks)) + " articles for " + article.title
    for link in article.relatedLinks:
        try:
            articleResp = unirest.get(link)
        except URLError as ex:
            print "Error in getting related link: " + str(ex)
            continue

        if articleResp.code == 200:
            source = articleResp.body
            soup = BeautifulSoup(source, 'html.parser')
            articleListSoup = soup.findAll('div', attrs={'class': 'blended-wrapper'})
            for relatedArticleSoup in articleListSoup:
                relatedArticleTitle = relatedArticleSoup.find('span', 'titletext').text
                try:
                    relatedArticle = Article.objects.get(title=relatedArticleTitle)
                except db.DoesNotExist as ex:
                    # Onto the next article
                    # should we then scrape this article and then add it to the database?
                    continue

                if relatedArticle not in article.relatedArticles:
                    print "Found a new related article: " + relatedArticleTitle + " for " + article.title
                    if isSaved:
                        # The preferred method but can only be used on a saved doc
                        article.update(push__relatedArticles=relatedArticle)
                    else:
                        article.relatedArticles.append(relatedArticle)


            article.relatedAnalyzed = True
        else:
            print "Couldn't make a request for the related article url "
            print "Error code: " + str(articleResp.code)
            if articleResp.code == 503:
                print colored("Google is probably mad. Stop for 5 secs.", 'red')
                time.sleep(5)
