"""Tests for ntelebot.deeplink."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


def test_encode():
    """Verify the deeplink encoder handles different types of strings reaonably."""

    assert ntelebot.deeplink.encode(b'') == u''
    assert ntelebot.deeplink.encode(u'') == u''
    assert ntelebot.deeplink.encode(b'test') == u'dGVzdA'
    assert ntelebot.deeplink.encode(u'test') == u'dGVzdA'
    assert ntelebot.deeplink.encode(u'\u2022') == u'4oCi'


def test_decode():
    """Verify the deeplink decoder handles different types of strings reaonably."""

    assert ntelebot.deeplink.decode(b'') == u''
    assert ntelebot.deeplink.decode(u'') == u''
    assert ntelebot.deeplink.decode(b'dGVzdA') == u'test'
    assert ntelebot.deeplink.decode(u'dGVzdA') == u'test'
    assert ntelebot.deeplink.decode(u'4oCi') == u'\u2022'
    assert ntelebot.deeplink.decode(u'\u2022') == u''

    # Gibberish, triggering TypeError in Python 2.7 and binascii.Error (which derives from
    # ValueError) in Python 3.6 for incorrect padding.
    assert ntelebot.deeplink.decode(b'a') == u''

    # b'\xff', triggering UnicodeDecodeError.
    assert ntelebot.deeplink.decode(b'/w') == u''
