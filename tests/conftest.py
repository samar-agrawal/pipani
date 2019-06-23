import pytest

@pytest.fixture(scope="function")
def app():
    from app.feeds import app
    test_client = app.test_client()
    test_client.testing = True
    yield app
