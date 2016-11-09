from bs4 import BeautifulSoup, Comment, Declaration
import requests
import re
from datetime import datetime, timedelta
from ssl import SSLError
from sentiment_scraper import db
from sentiment_scraper.models.article import Article
from sentiment_scraper.utils.article_matcher import find_matches


def is_article_text(element):
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


def scrape_google_article(article_soup, edition):
    related_link_soup = article_soup.findAll('a', attrs={'class': 'esc-topic-link'})
    related_links = []
    for link in related_link_soup:
        # Can't figure out why I keep scraping 2 copies of every related link
        formatted_link = 'http://news.google.com' + link['href']
        if formatted_link not in related_links:
            related_links.append('http://news.google.com' + link['href'])

    article_url = article_soup.find('a', attrs={'class': 'article'})['href']

    # Try to strip out just the name root source
    source_site = re.search('http://(.+?)\.(.+?)/(.+?)', article_url)
    if source_site:
        source_site = source_site.group(2)

    article_title = article_soup.find('span', 'titletext').text

    # Try to strip out the date
    date_text = article_soup.find('span', 'al-attribution-timestamp').text
    mins_ago = int(re.search(r'\d+', date_text).group())
    if date_text.lower().find('hour') != -1:
        mins_ago *= 60

    article_date = datetime.utcnow() - timedelta(minutes=mins_ago)

    try:
        article_source_response = requests.get(article_url)
        if article_source_response.status_code == 303:
            # NY times really not playing nice with scraping
            # Could use the selenium headless browser to get around this. Humph.
            article_source_response = requests.get(article_source_response.headers.dict['location'])
            print("Ugh @ NYTimes redirect")
        article_source = article_source_response.text

        # Now we have to filter out all html on the page and just try to grab the visible text
        # Note: This is not as good as scraping just the article, but I do not have the time
        # to write a scraper for each website

        texts = BeautifulSoup(article_source, 'html.parser').findAll(text=True)
        visible_text_list = list(filter(is_article_text, texts))

        article = Article(
            date=article_date,
            title=article_title,
            site=source_site,
            url=article_url,
            relatedLinks=related_links,
            newsEdition=edition
        )
        article.validate()
        find_matches(article)
        # Try to save it before analyzing in case of a duplicate error
        article.save()
        article.save_article_text(visible_text_list)
        article.save_raw_page(article_source)

        # Analyze!
        # Add a single space to buffer each text
        # Create one long string of all the visible text on the page for processing
        visible_text_str = ' '.join(list(visible_text_list))
        article.analyze_sentiment(text=visible_text_str)
        article.analyze_facebook()
        article.save()

        return article
    except (SSLError, db.ValidationError, db.NotUniqueError) as ex:
        print("Failed to validate the article: " + article.title)
        print("Because of " + str(ex))
        return None


def scrape_google_news(edition):
    """
    TODO: Should probably use the RSS feed instead of scraping HTML
    Wouldn't have to deal with ads
    Would have a measure for rate limiting
    :return: list of models.Article.Article
    """
    articles = []
    url = 'https://news.google.com/news/section?cf=all&pz=1&topic=n'
    source = requests.get(url)
    soup = BeautifulSoup(source.text, 'html.parser')
    article_list_soup = soup.findAll('div', attrs={'class': 'blended-wrapper'})

    print("Scraping Google News: " + edition)
    print(str(len(article_list_soup)) + " articles to scrape.")
    article_count = 1

    for articleSoup in article_list_soup:
        print("Scraping article #" + str(article_count))
        article_count += 1

        article = scrape_google_article(articleSoup, edition)

        if article is not None:
            articles.append(article)

    print("Done scraping")
    return articles
