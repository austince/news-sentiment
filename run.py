"""

Starts the scraper and the server in threads

"""
import os
import signal
import sys
import argparse
import threading
# from multiprocessing import Process
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

server_process = None
scraper_process = None


def run_server(env, port):
    """

    :param env:
    :param port:
    :return:
    """
    global server_process
    os.environ['NEWS_SENTIMENT_ENV'] = env
    # Load the app here so it uses the env variable
    from server import app as flask_server
    http_server = HTTPServer(WSGIContainer(flask_server))
    http_server.listen(port)
    server_process = threading.Thread(target=IOLoop.instance().start, args=())
    # server_process = Process(target=IOLoop.instance().start)
    server_process.start()
    print("Running server on port " + str(port) + " in " + env + " mode")


def run_scraper(sleep_time, mode):
    """

    :param sleep_time: seconds to wait between each scraping
    :return:
    """
    global scraper_process
    import sentiment_scraper
    scraper_process = threading.Thread(target=sentiment_scraper.run, args=(sleep_time, mode,), kwargs={})
    # scraper_process = Process(target=sentiment_scraper.run, args=(sleep_time,))
    scraper_process.start()
    print("Scrapper running every " + str(sleep_time) + " seconds")


def exit_sig_handler(signal, frame):
    global server_process
    global scraper_process

    #  No great way to stop threads
    if server_process is not None:
        print("Stopping the server.")
        # server_process.terminate()
        # server_process.join()
    if scraper_process is not None:
        print("Stopping the scraper.")
        # scraper_process.terminate()
        # scraper_process.join()

    sys.exit(0)

if __name__ == "__main__":
    # A hack to get around the env key's \r bugs
    os.environ['AWS_ACCESS_KEY_ID'] = os.environ['AWS_ACCESS_KEY_ID'].replace('\r', '')
    os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_SECRET_ACCESS_KEY'].replace('\r', '')

    parser = argparse.ArgumentParser(description='Scrape and serve google news sentiment and relations.')
    parser.add_argument('-p', '--port', type=int,
                        default=5000,
                        help="specify the port to run the server on.")

    parser.add_argument('-t', '--time', type=int,
                        default=3600,
                        help="specify the number of seconds between scrapings.")

    parser.add_argument('-e', '--env', type=str,
                        default='development',
                        help="specify the environment to run the server in.\n"
                             "'prod' or 'production' will load more secure settings.")

    parser.add_argument('--server', action='store_true',
                        help='specify to only run the server.')

    parser.add_argument('--scraper', action='store_true',
                        help="specify to only run the scraper.")

    parser.add_argument('-m', '--mode', type=str,
                        default='both',
                        help="specify the mode to run the scraper in.\n"
                             "'scrape' to only run scraper for new articles\n"
                             "'update' to only update the existing articles\n"
                             "'both' to run both.\n"
                             "Default is 'both'")

    args = parser.parse_args()

    signal.signal(signal.SIGINT, exit_sig_handler)
    signal.signal(signal.SIGTERM, exit_sig_handler)

    if args.server:
        run_server(args.env, args.port)
    elif args.scraper:
        run_scraper(args.time, args.mode)
    else:
        run_server(args.env, args.port)
        run_scraper(args.time, args.mode)

