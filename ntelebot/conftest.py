"""Test environment defaults."""

import os

import pytest


@pytest.fixture
def bot_token():
    """A genuine token from https://core.telegram.org/bots#3-how-do-i-create-a-bot."""

    return os.getenv('TEST_BOT_TOKEN')
