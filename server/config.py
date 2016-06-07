class Config:
    DEBUG = False
    TESTING = False
    MONGODB_SETTINGS = {
        'host': 'localhost',
        'port': 27017,
        'db': 'newsSentiment'
    }
    SECRET_KEY = 'secretssecrests'