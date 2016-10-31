"""

Starts the scraper and the server in threads

"""
import threading
from server import app
import sentiment_scraper
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

httpServer = HTTPServer(WSGIContainer(app))
httpServer.listen(5000)

serverThread = threading.Thread(target=IOLoop.instance().start, args=())
# Run every hour
scrapeThread = threading.Thread(target=sentiment_scraper.run, args=(3600,), kwargs={})

if __name__ == "__main__":
    print("Running")
    serverThread.start()
    scrapeThread.start()
