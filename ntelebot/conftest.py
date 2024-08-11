"""Test environment defaults."""

import os

import pytest

import ntelebot


@pytest.fixture(autouse=True)
def _bot_mock(monkeypatch, requests_mock):
    requests_mock.case_sensitive = True

    class MockRequest(ntelebot.bot._Request):
        # pylint: disable=missing-docstring,protected-access,too-few-public-methods

        def respond(self, **response):
            requests_mock.post(self.url, **response)

    monkeypatch.setattr('ntelebot.bot._Request', MockRequest)


@pytest.fixture
def bot_test_chat():
    """The chat_id of a person or group the bot can send messages to."""

    return os.getenv('TEST_BOT_CHAT_ID')


@pytest.fixture
def bot_token():
    """A genuine token from https://core.telegram.org/bots#3-how-do-i-create-a-bot."""

    return os.getenv('TEST_BOT_TOKEN')
