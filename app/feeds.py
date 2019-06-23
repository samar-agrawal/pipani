import os
import requests
import tempfile
import pathlib
import urllib
from flask import Flask, request, send_from_directory
from functools import lru_cache
from feedgen.feed import FeedGenerator

app = Flask(__name__)
base_url = 'https://api.twitter.com'
TWEET_LIMIT = 5

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']

#TODO: cache session, using code 89
auth_dict = {}
def get_auth_token(token):
    import requests
    data = {
       'grant_type': 'client_credentials'
    }
    if token not in auth_dict:
        response = requests.post(f'{base_url}/oauth2/token', data=data, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        auth_dict[token] = response.json()
    return auth_dict[token]

@lru_cache(maxsize=32)
def get_tweets(user):
    fields = ['id', 'created_at', 'text', 'lang']
    auth = get_auth_token('twitter')
    assert auth, "Unable to authenticate"
    bearer_token = auth['access_token']
    user_timeline = requests.get(f'{base_url}/1.1/statuses/user_timeline.json?screen_name={user}&count={TWEET_LIMIT}&trim_user=1&exclude_replies=0',
        headers={'Authorization': f'Bearer {bearer_token}'})
    tweets = user_timeline.json()

    for tweet in tweets:
        # tweet = {k: tweet[k] for k in tweet if k in fields}
        print("processing tweet", tweet['id'])
        tweet['comments'] = get_comments(user, tweet['id'], bearer_token)
        print("received comments", tweet['id'])
        tweet['link'] = f'https://twitter.com/{user}/status/{tweet["id"]}'
        # t['user'] = {'name': user}

    return tweets

def get_comments(user, tweet_id, bearer_token):#generator
    #TODO: refactor
    replies = []
    q = urllib.parse.urlencode({"q": "to:%s" % user, "since_id": tweet_id, "count":100})
    comments = requests.get(f'{base_url}/1.1/search/tweets.json?{q}', headers={'Authorization': f'Bearer {bearer_token}'})
    for reply in comments.json()['statuses']:
        if reply['in_reply_to_status_id'] == tweet_id:
            replies.append(reply['text'])
    return " ,".join(replies)

def generate_atom_feed(tweets, user):
    dirname = tempfile.mkdtemp()
    path = pathlib.Path(dirname)
    print(tweets)
    fg = FeedGenerator()
    fg.title(f'Tweets for {user}')
    fg.link(href='https://twitter.com')
    fg.description('List of tweets and replies for the user')
    for tweet in tweets: #enumerate #stream
        te = fg.add_entry()
        print("tweet", tweet)
        te.title(tweet['text'])
        te.link(href=tweet['link'])
        # te.description(tweet['text'])
        te.comments(tweet['comments'])
        te.updated(tweet['created_at'])
        te.id(str(tweet['id']))
        # for reply in tweet['comments']:
        #     entry = te.add_entry()
        #     entry.title(reply)
    fg.rss_file(f'{path}/dashboard.xml')
    return path

@app.route("/dashboard.xml")
def dashboard():
    user = request.args.get('user')
    print("getting data for", user)
    tweets = get_tweets(user)

    path = generate_atom_feed(tweets, user)
    return send_from_directory(path, 'dashboard.xml')

#TODO:
# update docker file
# write tests
# write readme
# write comments/docfunc
# stream xml
# use generator / class
# add asserts
#configure env
#update limit to 30
