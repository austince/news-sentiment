# News Sentiment 

<p align="center">
    <img src="https://i.imgur.com/oOrLKCx.png"/>
</p>


A Google News scraper and slim server to analyze the sentiment of our news.  
For HST 325, Visualizing Society.  
Yet another project with Flask and Mongo. 

A visualization of the scraped data lives [here](http://personal.stevens.edu/~acawleye/final/)!

## Running

### Keys
Keys are in bash scripts that simply export them to the environment.  
They are loaded through the install.sh script.

- Need a Facebook application access token for interacting with the Graph API
- Need a Mashape Key to analyze Sentiment
- Need an AWS Key + Secret, and a bucket named news-sentiment, for storing the 
article text outside of Mongo
- To run in production mode: need a secret key for the Flask Server, stored in a .txt file

File structure should look like:
```
sentiment_scraper/
server/
    secret-key.private.txt
    ...
install.sh
...
aws-account.private.sh
facebook-access-token.private.sh
mashape-key.private.sh
...
```

To install and load:
```bash
source ./install.sh
```

### Run.py
Running options:
```bash
python run.py --help
```

