import pkg_resources


class Config:
    DEBUG = False
    TESTING = False
    MONGODB_SETTINGS = {
        'host': 'localhost',
        'port': 27017,
        'db': 'newsSentiment'
    }
    SECRET_KEY = 'secretssecrets'


class DevConfig(Config):
    DEBUG = True
    TESTING = True


class ProdConfig(Config):
    SECRET_KEY = pkg_resources.resource_string(__name__, '/secret-key.private.txt')
