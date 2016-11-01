from bs4 import BeautifulSoup, Comment, Declaration
import requests
import re
from datetime import datetime, timedelta
from ssl import SSLError
from sentiment_scraper import db
from sentiment_scraper.models.article import Article
from sentiment_scraper.utils.article_matcher import findMatches


def isArticleText(element):
    """
    Found @
    http://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text

    Given an html text element
    returns if the element is user visible
    """

    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    elif type(element) is Comment or type(element) is Declaration:
        # BeautifulSoup wraps some elements in nicer data structures, gotta check tho
        return False
    elif len(str(element)) < 250:
        # Try to figure out if an article or not. This is purely by length. No shorties.
        return False
    return True


def scrapeGoogleArticle(articleSoup, edition):
    relatedLinkSoup = articleSoup.findAll('a', attrs={'class': 'esc-topic-link'})
    relatedLinks = []
    for link in relatedLinkSoup:
        # Can't figure out why I keep scraping 2 copies of every related link
        formattedLink = 'http://news.google.com' + link['href']
        if formattedLink not in relatedLinks:
            relatedLinks.append('http://news.google.com' + link['href'])

    articleUrl = articleSoup.find('a', attrs={'class': 'article'})['href']

    # Try to strip out just the name root source
    sourceSite = re.search('http://(.+?)\.(.+?)/(.+?)', articleUrl)
    if sourceSite:
        sourceSite = sourceSite.group(2)

    articleTitle = articleSoup.find('span', 'titletext').text

    # Try to strip out the date
    dateText = articleSoup.find('span', 'al-attribution-timestamp').text
    minsAgo = int(re.search(r'\d+', dateText).group())
    if dateText.lower().find('hour') != -1:
        minsAgo *= 60

    articleDate = datetime.utcnow() - timedelta(minutes=minsAgo)

    try:
        articleSourceResponse = requests.get(articleUrl)
        if articleSourceResponse.status_code == 303:
            # NY times really not playing nice with scraping
            # Could use the selenium headless browser to get around this. Humph.
            articleSourceResponse = requests.get(articleSourceResponse.headers.dict['location'])
            print("Ugh @ NYTimes redirect")
        articleSource = articleSourceResponse.text

        # Now we have to filter out all html on the page and just try to grab the visible text
        # Note: This is not as good as scraping just the article, but I do not have the time
        # to write a scraper for each website

        texts = BeautifulSoup(articleSource, 'html.parser').findAll(text=True)
        visibleTextList = list(filter(isArticleText, texts))

        article = Article(
            date=articleDate,
            title=articleTitle,
            site=sourceSite,
            url=articleUrl,
            relatedLinks=relatedLinks,
            newsEdition=edition
        )
        article.validate()
        findMatches(article)
        # Try to save it before analyzing in case of a duplicate error
        article.save()
        article.saveArticleText(visibleTextList)
        article.saveRawPage(articleSource)

        # Analyze!
        # Add a single space to buffer each text
        # Create one long string of all the visible text on the page for processing
        visibleTextStr = ' '.join(list(visibleTextList))
        article.analyzeSentiment(text=visibleTextStr)
        article.analyzeFacebook()
        article.save()

        return article
    except (SSLError, db.ValidationError, db.NotUniqueError) as ex:
        print("Failed to validate the article: " + article.title)
        print("Because of " + str(ex))
        return None


def scrapeGoogleNews(edition):
    """

    :return: list of models.Article.Article
    """
    articles = []
    url = 'https://news.google.com/news/section?cf=all&pz=1&topic=n'
    source = requests.get(url)
    soup = BeautifulSoup(source.text, 'html.parser')
    articleListSoup = soup.findAll('div', attrs={'class': 'blended-wrapper'})

    print("Scraping Google News: " + edition)
    print(str(len(articleListSoup)) + " articles to scrape.")
    articleCount = 1

    for articleSoup in articleListSoup:
        print("Scraping article #" + str(articleCount))
        articleCount += 1

        article = scrapeGoogleArticle(articleSoup, edition)

        if article is not None:
            articles.append(article)

    print("Done scraping")
    return articles