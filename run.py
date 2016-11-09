"""

Starts the scraper and the server in threads

"""
import argparse
import threading
from server import app as flask_server
import sentiment_scraper
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


def run_server(port):
    http_server = HTTPServer(WSGIContainer(flask_server))
    http_server.listen(port)
    server_thread = threading.Thread(target=IOLoop.instance().start, args=())
    server_thread.start()
    print("Running server on port " + str(port))


def run_scraper(sleep_time):
    """

    :param sleep_time: seconds to wait between each scraping
    :return:
    """
    # Run every hour
    scrape_thread = threading.Thread(target=sentiment_scraper.run, args=(sleep_time,), kwargs={})
    scrape_thread.start()
    print("Scrapper running every " + str(sleep_time) + " seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape and serve google news sentiment and relations.')
    parser.add_argument('-p', '--port', type=int,
                        default=5000,
                        help='specify the port to run the server on.')

    parser.add_argument('-t', '--time', type=int,
                        default=3600,
                        help='specify the number of seconds between scrapings.')

    parser.add_argument('--server', action='store_true',
                        help='specify to only run the server.')

    parser.add_argument('--scraper', action='store_true',
                        help='specify to only run the scraper.')

    args = parser.parse_args()

    if args.server:
        run_server(args.port)
    elif args.scraper:
        run_scraper(args.time)
    else:
        run_server(args.port)
        run_scraper(args.time)

