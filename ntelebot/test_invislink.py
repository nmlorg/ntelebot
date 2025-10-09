"""Tests for ntelebot.invislink."""

import base64
import json

import ntelebot


def test_decode():
    """Run through ntelebot.invislink.decode."""

    entities = [
        {
            'type': 'bogus',
        },
    ]
    assert ntelebot.invislink.decode(entities) == (None, None)

    entities.append({'type': 'text_link', 'url': 'tg://btn/bogus'})
    assert ntelebot.invislink.decode(entities) == (None, None)

    entities[-1]['url'] = 'tg://btn/\u2022'
    assert ntelebot.invislink.decode(entities) == (None, None)

    assert base64.urlsafe_b64encode(b'first string\x00second string') == (
        b'Zmlyc3Qgc3RyaW5nAHNlY29uZCBzdHJpbmc=')
    entities[-1]['url'] = 'tg://btn/Zmlyc3Qgc3RyaW5nAHNlY29uZCBzdHJpbmc='
    assert ntelebot.invislink.decode(entities) == (['first string', 'second string'], None)

    # Malformed.
    entities[-1]['url'] = 'tg://meta/Zmlyc3Qgc3RyaW5nAHNlY29uZCBzdHJpbmc='
    assert ntelebot.invislink.decode(entities) == (None, None)

    # Only dicts are allowed.
    assert base64.urlsafe_b64encode(json.dumps(['aa', 'bb']).encode('ascii')) == b'WyJhYSIsICJiYiJd'
    entities[-1]['url'] = 'tg://meta/WyJhYSIsICJiYiJd'
    assert ntelebot.invislink.decode(entities) == (None, None)

    assert base64.urlsafe_b64encode(json.dumps({
        'aa': 'bb',
    }).encode('ascii')) == b'eyJhYSI6ICJiYiJ9'
    entities[-1]['url'] = 'tg://meta/eyJhYSI6ICJiYiJ9'
    assert ntelebot.invislink.decode(entities) == (None, {'aa': 'bb'})
