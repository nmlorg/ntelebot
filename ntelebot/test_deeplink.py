"""Tests for ntelebot.deeplink."""

import ntelebot


def test_encode():
    """Verify the deeplink encoder handles different types of strings reaonably."""

    assert ntelebot.deeplink.encode(b'') == ''
    assert ntelebot.deeplink.encode('') == ''
    assert ntelebot.deeplink.encode(b'test') == 'dGVzdA'
    assert ntelebot.deeplink.encode('test') == 'dGVzdA'
    assert ntelebot.deeplink.encode('\u2022') == '4oCi'


def test_decode():
    """Verify the deeplink decoder handles different types of strings reaonably."""

    assert ntelebot.deeplink.decode(b'') == ''
    assert ntelebot.deeplink.decode('') == ''
    assert ntelebot.deeplink.decode(b'dGVzdA') == 'test'
    assert ntelebot.deeplink.decode('dGVzdA') == 'test'
    assert ntelebot.deeplink.decode('4oCi') == '\u2022'
    assert ntelebot.deeplink.decode('\u2022') == ''

    # Gibberish, triggering TypeError in Python 2.7 and binascii.Error (which derives from
    # ValueError) in Python 3.6 for incorrect padding.
    assert ntelebot.deeplink.decode(b'a') == ''

    # b'\xff', triggering UnicodeDecodeError.
    assert ntelebot.deeplink.decode(b'/w') == ''
