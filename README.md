# Pipani
> Twitter feeds to Atom feed format

Simple Application to convert information from [Twitter API](https://developer.twitter.com/en/docs) dasboard for a user to [ATOM](https://en.wikipedia.org/wiki/Atom_(Web_standard)) xml file format.

### Pre-Requisties
- May not work properly under python 2.7
- Might need to generate CONSUMER_KEY and CONSUMER_SECRET from [twitter developer portal](https://developer.twitter.com/en/apply)

### Run via docker
```
docker build -t="pipani" .
docker run -it -e "CONSUMER_KEY=consumer_key" -e "CONSUMER_SECRET=consumer_secret" -p 8080:8080 pipani
```

### Run via python
Environment variables can alternatively be set in .bashrc file
```
export CONSUMER_KEY="consumer key"
export CONSUMER_SECRET="consumer secret"
pip3 install -r requirements.txt
export FLASK_APP=fees.py
flask run
```

### Sample usage
```
from app.feeds import TwitterAtomFeedGenerator
tw_obj = TwitterAtomFeedGenerator(user=user)
tweets = tw_obj.get_tweets(limit=limit)
print(tweets)
```

#### Features
- Get user tweets
- Get comments on tweets
- Generate xml atom feed file

### Tests
Refer to [testing guide](https://github.com/samar-agrawal/pipani/tree/master/tests)
```
docker run -it -e "CONSUMER_KEY=CONSUMER_KEY" -e "CONSUMER_SECRET=CONSUMER_SECRET" pipani pytest
```
