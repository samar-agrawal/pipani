'''
    APP to fetch data from Twitter for given user and convert to ATOM feed
'''

import os
import tempfile
import urllib
from collections import defaultdict

import requests
from flask import Flask, request, send_from_directory
from feedgen.feed import FeedGenerator

app = Flask(__name__)
BASE_URL = 'https://api.twitter.com'
DEFAULT_TWEET_LIMIT = 30

@app.route("/public/hc", methods=['GET'])
def healthcheck():
    return "OK", 200

@app.errorhandler(AssertionError)
def handle_assertion(error):
    from flask import jsonify
    import traceback
    ret = {'code': 400, 'error': error.args[0], 'traceback': traceback.format_exc()}
    return jsonify(**ret), ret['code']

@app.route("/dashboard.xml")
def dashboard():
    user = request.args.get('user')
    limit = request.args.get('limit', DEFAULT_TWEET_LIMIT)
    print("getting data for", user)
    assert user, "No user handle found in get param"

    tw_obj = TwitterAtomFeedGenerator(user=user)
    tweets = tw_obj.get_tweets(limit=limit)
    assert tweets, f"{user} has no tweets"

    min_id, max_id = tw_obj.get_min_max_id(tweets)
    comments = tw_obj.get_comments(min_id, max_id)
    tw_obj.tweets = list(tw_obj.add_comments_to_tweets(tweets, comments))

    path_to_feed = tw_obj.generate_feeds()
    #TODO stream via flask
    return send_from_directory(path_to_feed, 'dashboard.xml')

class TwitterAtomFeedGenerator:
    '''
        Constructs and sends a class for processing twitter data for user
        :param user: twitter user handle
    '''

    def __init__(self, user: str):
        self.user = user
        self.bearer_token = None
        self.session = requests.session()
        self.base_url = BASE_URL
        self.path = None
        self.feedgen = None
        self._get_auth_token()

    def _get_auth_token(self):
        '''
            Get a authenticated bearer_token for processing twitter requests
            (https://developer.twitter.com/en/docs/basics/authentication/guides/bearer-tokens)
            :params CONSUMER_KEY: to be set in environment variable
            :params CONSUMER_SECRET: to be set in environment variable
        '''

        if self.bearer_token:
            return
        data = {'grant_type': 'client_credentials'}

        try:
            auth = (os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
        except KeyError:
            assert False, "CONSUMER_KEY / CONSUMER_SECRET key not found"

        response = self.session.post(
            f'{self.base_url}/oauth2/token', data=data, auth=auth, timeout=10)
        if response.status_code == 403:
            assert False, "Invalid API Keys"
        response.raise_for_status()

        token = response.json()['access_token']
        self.bearer_token = token

    def get(self, url: str):
        '''
            Fetch data from Twitter API
            :params url: url path with request params
        '''

        headers = {'Authorization': f'Bearer {self.bearer_token}'}
        response = self.session.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            assert False, f"No data found for {self.user}"
        response.raise_for_status()

        return response.json()

    def init_feedgen(self):
        '''
            Initializing Atom feed generator and creating tempdir for storage
        '''

        dirname = tempfile.mkdtemp()
        self.path = dirname
        feed_gen = FeedGenerator()
        feed_gen.title(f'Tweets for {self.user}')
        feed_gen.link(href='https://twitter.com')
        feed_gen.description('List of tweets and replies for the user')
        self.feedgen = feed_gen

    @staticmethod
    def get_min_max_id(tweets: list):
        '''
            Get min/max tweet id from list of tweets
            :params tweets: list of tweet objects
        '''

        min_id = min([a['id'] for a in tweets])
        max_id = max([a['id'] for a in tweets])
        return min_id, max_id

    def get_tweets(self, limit=5):
        '''
            Fetch most recent tweets of the user
            (https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline.html)
            :params limit: number of tweets to be retrieved
        '''

        fields = ['id', 'created_at', 'text', 'lang']
        q = urllib.parse.urlencode({
            "screen_name": self.user,
            "count": limit,
            "trim_user":1,
            "exclude_replies":0})

        tweets = self.get(f'{self.base_url}/1.1/statuses/user_timeline.json?{q}')
        tweets = [{k: tweet[k] for k in tweet if k in fields} for tweet in tweets]

        return tweets

    def get_comments(self, tweet_min_id: int, tweet_max_id: int):
        '''
            Get comments related to tweets.
            :tweet_min_id :min id to fetch data from
            :tweet_max_id: max id to fetch data upto
        '''

        #TODO: unable to find a better way to fetch comments / replies, if the
        # first couple of tweets have more then 100 comments
        # then its possible the other tweets might not list any comments,
        # one way was to fetch comments for each tweet
        # but that would make repeative calls to twitter api, and if there
        # are limited set of comments, then would possibly
        # show same set of data for diff tweets
        q = urllib.parse.urlencode({
            "q": "to:%s" % self.user,
            "since_id": tweet_min_id,
            "max_id": tweet_max_id,
            "count":100})

        comments = self.get(f'{self.base_url}/1.1/search/tweets.json?{q}')
        comment_dict = defaultdict(list)
        for comment in comments['statuses']:
            comment_dict[comment['in_reply_to_status_id']].append(comment['text'])

        return dict(comment_dict)

    def add_comments_to_tweets(self, tweets: list, comments: dict):
        '''
            Merge comments in the respective tweets based on in_reply_to_status_id
            :params tweets: list of tweet objects
            :params comments: object of tweet id and comments
        '''
        for tweet in tweets:
            tweet['link'] = f'https://twitter.com/{self.user}/status/{tweet["id"]}'
            if tweet['id'] in comments:
                #TODO figure out a better way to show comments in feeds
                tweet['comments'] = " ,".join(comments[tweet['id']])
            yield tweet

    def generate_feeds(self):
        '''
            Write tweet data to atom feed file locally and send file path
            :rtype path: file path to generated atom feed file
        '''
        self.init_feedgen()

        for tweet in self.tweets:
            feed_entry = self.feedgen.add_entry()
            feed_entry.title(tweet['text'])
            feed_entry.link(href=tweet['link'])
            if tweet.get('comments'):
                feed_entry.comments(tweet['comments'])
            feed_entry.updated(tweet['created_at'])
            feed_entry.id(str(tweet['id']))

        self.feedgen.rss_file(f'{self.path}/dashboard.xml')
        return self.path
