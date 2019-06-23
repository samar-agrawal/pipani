import pytest
from app.feeds import app, TwitterAtomFeedGenerator

def test_hc():
    rv = app.test_client().get('/public/hc')
    assert rv.status_code == 200, "URL not set correctly"

def test_get_dashboard_without_user():
    with pytest.raises(AssertionError):
        rv = app.test_client().get('/dashboard.xml')
        assert rv.status_code == 200, rv.json['error']

def test_get_dashboard():
    rv = app.test_client().get('/dashboard.xml?user=benedictevans')
    assert rv.status_code == 200, "No data found"

def test_twitter_auth():
    tw_obj = TwitterAtomFeedGenerator(user='foobar')
    assert tw_obj.bearer_token, "No token found / key invalid"

def test_get_tweets():
    tw_obj = TwitterAtomFeedGenerator(user='enstino_')
    tweets = tw_obj.get_tweets()
    assert tweets, "No tweets found"

def test_get_tweets_invalid_user():
    tw_obj = TwitterAtomFeedGenerator(user='spnifdsvew')
    with pytest.raises(AssertionError):
        tweets = tw_obj.get_tweets()
        assert tweets, "No tweets found"

def test_no_comments_for_tweet():
    tw_obj = TwitterAtomFeedGenerator(user='enstino_')
    tweets = tw_obj.get_tweets()
    min_id, max_id = tw_obj.get_min_max_id(tweets)
    with pytest.raises(AssertionError):
        comments = tw_obj.get_comments(min_id, max_id)
        assert comments, "No comments found"
