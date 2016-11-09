"""

"""
import os
import requests
from ssl import SSLError
from sentiment_scraper import db

MASHAPE_KEY = os.environ.get('MASHAPE_KEY', '')


class TextAnalysis(db.EmbeddedDocument):
    neg = db.FloatField()
    neutral = db.FloatField()
    pos = db.FloatField()
    terms = db.ListField(db.DictField())
    warnings = db.ListField(db.StringField())

    @staticmethod
    def from_text(text):
        analysis = None

        # Only use the first 10,000 chars limit for now
        # Will aggregate later
        if len(text) > 10000:
            text = text[:10000]

        try:
            response = requests.post(
                "https://sentinelprojects-skyttle20.p.mashape.com/",
                headers={
                    "X-Mashape-Key": MASHAPE_KEY,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                data={
                    "annotate": 1,
                    "keywords": 1,
                    "lang": "en",
                    "sentiment": 1,
                    "text": text
                },
                timeout=5
            )
        except SSLError as ex:
            print(str(ex))
            # Must break out if we cannot get a response :(
            return None

        # Break into terms and sentiment
        if response.ok:
            data = response.json()
            warnings = data['warnings']
            # The meat of the response
            sentiment_data = data['docs'][0]
            for term in sentiment_data['terms']:
                del term['id']  # No one wants yo id CT

            analysis = TextAnalysis(
                pos=float(sentiment_data['sentiment_scores']['pos']),
                neutral=float(sentiment_data['sentiment_scores']['neu']),
                neg=float(sentiment_data['sentiment_scores']['neg']),
                terms=sentiment_data['terms'],
                warnings=warnings
            )

        else:
            print("Error w/ Sentiment Analysis request.")
            print(response.status_code)
            print(response.content)

        return analysis
