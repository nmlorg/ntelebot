"""Tests for ntelebot.bot."""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

import ntelebot


def test_token():
    """Verify the token is used correctly to construct the base URL."""

    assert ntelebot.bot.Bot('test:test').url == 'https://api.telegram.org/bottest:test/'


def test_getattr_magic():
    """Verify Bot().methodName returns a _Request instance with a normalized URL."""

    # pylint: disable=protected-access
    assert isinstance(ntelebot.bot.Bot('test:test').getMe, ntelebot.bot._Request)
    assert ntelebot.bot.Bot('test:test').get_me.url == 'https://api.telegram.org/bottest:test/getme'


def test_request():
    """Verify simple live echo requests return the appropriate response."""

    bot = ntelebot.bot.Bot('test:test')
    bot.get_me.respond(real_http=True)
    with pytest.raises(ntelebot.errors.NotFound):
        bot.get_me()

    # From https://core.telegram.org/bots/api#authorizing-your-bot.
    bot = ntelebot.bot.Bot('123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
    bot.get_me.respond(real_http=True)
    with pytest.raises(ntelebot.errors.Unauthorized):
        bot.get_me()

    # From https://github.com/python-telegram-bot/python-telegram-bot/blob/master/tests/bots.py.

    bot = ntelebot.bot.Bot('133505823:AAHZFMHno3mzVLErU5b5jJvaeG--qUyLyG0')
    bot.get_me.respond(real_http=True)
    assert bot.get_me() == {
        'first_name': 'PythonTelegramBot',
        'id': 133505823,
        'is_bot': True,
        'username': 'PythonTelegramBot',
    }

    bot = ntelebot.bot.Bot('133505823:AAHZFMHno3mzVLErU5b5jJvaeG--qUyLyG0', timeout=2)
    bot.get_updates.respond(real_http=True)
    with pytest.raises(ntelebot.errors.Timeout):
        bot.get_updates(timeout=3)
