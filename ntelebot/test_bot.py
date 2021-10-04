"""Tests for ntelebot.bot."""

import io

import pytest
import requests

import ntelebot


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


def test_request(bot_token):
    """Verify simple live echo requests return the appropriate response."""

    # From https://core.telegram.org/bots/api#authorizing-your-bot.
    bot = ntelebot.bot.Bot('123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11')
    bot.get_me.respond(real_http=True)
    with pytest.raises(ntelebot.errors.Unauthorized):
        bot.get_me()

    assert bot_token, 'Set TEST_BOT_TOKEN in your environment before running this test.'

    bot = ntelebot.bot.Bot(bot_token)
    bot.get_dummy.respond(real_http=True)
    with pytest.raises(ntelebot.errors.NotFound):
        bot.get_dummy()

    bot.get_me.respond(real_http=True)
    assert bot.get_me() == {
        'can_join_groups': False,
        'can_read_all_group_messages': False,
        'first_name': 'ntelebot',
        'id': int(bot_token.split(':', 1)[0]),
        'is_bot': True,
        'supports_inline_queries': False,
        'username': 'ntelebot',
    }

    bot = ntelebot.bot.Bot(bot_token, timeout=2)
    bot.get_updates.respond(real_http=True)
    offset = None
    updates = bot.get_updates(timeout=0)
    if updates:
        offset = updates[-1]['update_id'] + 1
    with pytest.raises(ntelebot.errors.Timeout):
        bot.get_updates(offset=offset, timeout=3)


def test_prepare(monkeypatch):
    """Verify the request builder handles files and complex types properly."""

    def prep(params):
        prep_params = ntelebot.bot._prepare(params)  # pylint: disable=protected-access
        req = requests.Request('POST', 'https://example.com/', **prep_params).prepare()
        transcript = [b'']
        for header, value in req.headers.items():
            transcript.append(f'{header}: {value}'.encode('ascii'))
        transcript.append(b'')
        body = req.body
        if isinstance(body, str):
            body = body.encode('ascii')
        transcript.append(body.replace(b'\r\n', b'\n').strip())
        transcript.append(b'')
        return b'\n'.join(transcript)

    assert prep({}) == b"""
Content-Length: 2
Content-Type: application/json

{}
"""

    assert prep({
        'chat_id': 1234,
        'text': 'my \u2022 text',
    }) == b"""
Content-Length: 43
Content-Type: application/json

{"chat_id": 1234, "text": "my \\u2022 text"}
"""

    assert prep({
        'chat_id': 1234,
        'text': 'my \u2022 text',
        'entities': [{
            'type': 'italic',
            'offset': 0,
            'length': 2,
        }],
        'disable_notification': True,
    }) == b"""
Content-Length: 133
Content-Type: application/json

{"chat_id": 1234, "text": "my \\u2022 text", "entities": [{"type": "italic", "offset": 0, "length": 2}], "disable_notification": true}
"""

    monkeypatch.setattr('urllib3.filepost.choose_boundary', lambda: 'BoUnDaRy')
    assert '\u2022'.encode('utf8') == b'\xe2\x80\xa2'

    assert prep({
        'chat_id': 1234,
        'photo': io.StringIO('CoNtEnTs'),
        'caption': 'my \u2022 text',
        'caption_entities': [{
            'type': 'italic',
            'offset': 0,
            'length': 2,
        }],
        'disable_notification': True,
    }) == b"""
Content-Length: 516
Content-Type: multipart/form-data; boundary=BoUnDaRy

--BoUnDaRy
Content-Disposition: form-data; name="chat_id"

1234
--BoUnDaRy
Content-Disposition: form-data; name="photo"

attach://file0
--BoUnDaRy
Content-Disposition: form-data; name="caption"

my \xe2\x80\xa2 text
--BoUnDaRy
Content-Disposition: form-data; name="caption_entities"

[{"type": "italic", "offset": 0, "length": 2}]
--BoUnDaRy
Content-Disposition: form-data; name="disable_notification"

true
--BoUnDaRy
Content-Disposition: form-data; name="file0"; filename=""

CoNtEnTs
--BoUnDaRy--
"""
