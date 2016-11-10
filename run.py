"""

Starts the scraper and the server in threads

"""
import os
import signal
import sys
import argparse
import threading
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

server_thread = None
scraper_thread = None


def run_server(env, port):
    """

    :param env:
    :param port:
    :return:
    """
    global server_thread
    os.environ['NEWS_SENTIMENT_ENV'] = env
    # Load the app here so it uses the env variable
    from server import app as flask_server
    http_server = HTTPServer(WSGIContainer(flask_server))
    http_server.listen(port)
    server_thread = threading.Thread(target=IOLoop.instance().start, args=())
    server_thread.start()
    print("Running server on port " + str(port) + " in " + env + " mode")


def run_scraper(sleep_time):
    """

    :param sleep_time: seconds to wait between each scraping
    :return:
    """
    global scraper_thread
    # A hack to get around the env key's \r bugs
    os.environ['AWS_ACCESS_KEY_ID'] = os.environ['AWS_ACCESS_KEY_ID'].replace('\r', '')
    os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_SECRET_ACCESS_KEY'].replace('\r', '')
    import sentiment_scraper
    scraper_thread = threading.Thread(target=sentiment_scraper.run, args=(sleep_time,), kwargs={})
    scraper_thread.start()
    print("Scrapper running every " + str(sleep_time) + " seconds")


def exit_sig_handler(signal, frame):
    global server_thread
    global scraper_thread

    #  No great way to stop threads
    if server_thread is not None:
        # server_thread.set()
        print("Stopping the server.")
    if scraper_thread is not None:
        # scraper_thread.set()
        print("Stopping the scraper.")

    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape and serve google news sentiment and relations.')
    parser.add_argument('-p', '--port', type=int,
                        default=5000,
                        help="specify the port to run the server on.")

    parser.add_argument('-t', '--time', type=int,
                        default=3600,
                        help="specify the number of seconds between scrapings.")

    parser.add_argument('-e', '--env', type=str,
                        default='development',
                        help="specify the environment to run the server in. "
                             "'prod' or 'production' will load more secure settings.")

    parser.add_argument('--server', action='store_true',
                        help='specify to only run the server.')

    parser.add_argument('--scraper', action='store_true',
                        help="specify to only run the scraper.")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, exit_sig_handler)
    signal.signal(signal.SIGTERM, exit_sig_handler)

    if args.server:
        run_server(args.env, args.port)
    elif args.scraper:
        run_scraper(args.time)
    else:
        run_server(args.env, args.port)
        run_scraper(args.time)

