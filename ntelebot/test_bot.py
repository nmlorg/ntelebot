"""Tests for ntelebot.bot."""

import pytest

import ntelebot

TEST_BOT_TOKEN = '1824972844:AAFKcZlNoyGnA2rkdemlHCrJ5432fXYm9dE'


def test_token():
    """Verify the token is used correctly to construct the base URL."""

    assert ntelebot.bot.Bot('1234:test').url == 'https://api.telegram.org/bot1234:test/'

    with pytest.raises(AssertionError):
        ntelebot.bot.Bot('test:test')
    with pytest.raises(AssertionError):
        ntelebot.bot.Bot('1234:test/getme?')


def test_getattr_magic():
    """Verify Bot().methodName returns a _Request instance with a normalized URL."""

    # pylint: disable=protected-access
    assert isinstance(ntelebot.bot.Bot('1234:test').getMe, ntelebot.bot._Request)
    assert ntelebot.bot.Bot('1234:test').get_me.url == 'https://api.telegram.org/bot1234:test/getme'


def test_request():
    """Verify simple live echo requests return the appropriate response."""

    # From https://core.telegram.org/bots/api#authorizing-your-bot.
    bot = ntelebot.bot.Bot('123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
    bot.get_me.respond(real_http=True)
    with pytest.raises(ntelebot.errors.Unauthorized):
        bot.get_me()

    # From https://github.com/python-telegram-bot/python-telegram-bot/blob/master/tests/bots.py.

    bot = ntelebot.bot.Bot(TEST_BOT_TOKEN)
    bot.get_dummy.respond(real_http=True)
    with pytest.raises(ntelebot.errors.NotFound):
        bot.get_dummy()

    bot.get_me.respond(real_http=True)
    assert bot.get_me() == {
        'can_join_groups': False,
        'can_read_all_group_messages': False,
        'first_name': 'ntelebot',
        'id': int(TEST_BOT_TOKEN.split(':', 1)[0]),
        'is_bot': True,
        'supports_inline_queries': False,
        'username': 'ntelebot',
    }

    bot = ntelebot.bot.Bot(TEST_BOT_TOKEN, timeout=2)
    bot.get_updates.respond(real_http=True)
    offset = None
    updates = bot.get_updates(timeout=0)
    if updates:
        offset = updates[-1]['update_id'] + 1
    with pytest.raises(ntelebot.errors.Timeout):
        bot.get_updates(offset=offset, timeout=3)
