"""Tests for ntelebot.keyboardutil."""

import base64

import ntelebot


def test_decode():
    """Run through ntelebot.keyboardutil.decode."""

    assert ntelebot.keyboardutil.decode({}, 'unencoded text') == 'unencoded text'

    assert base64.urlsafe_b64encode(b'first string\x00second string') == (
        b'Zmlyc3Qgc3RyaW5nAHNlY29uZCBzdHJpbmc=')
    message = {
        'entities': [
            {
                'type': 'bogus',
            },
            {
                'type': 'text_link',
                'url': 'tg://btn/Zmlyc3Qgc3RyaW5nAHNlY29uZCBzdHJpbmc=',
            },
        ],
    }

    assert ntelebot.keyboardutil.decode(message, 'unencoded text') == 'unencoded text'
    assert ntelebot.keyboardutil.decode(message, '\x000\x00suffix') == 'first stringsuffix'
    assert ntelebot.keyboardutil.decode(message, '\x001\x00suffix') == 'second stringsuffix'
    assert ntelebot.keyboardutil.decode(message, '\x002\x00suffix') == '\x002\x00suffix'
    assert ntelebot.keyboardutil.decode(message, '\x00bogus\x00suffix') == '\x00bogus\x00suffix'


def test_shorten_lines():
    """Run through ntelebot.keyboardutil.shorten_lines."""

    assert ntelebot.keyboardutil.shorten_lines([], 0) == ([], {})
    assert ntelebot.keyboardutil.shorten_lines(['short'], 5) == ([], {})
    assert ntelebot.keyboardutil.shorten_lines(['long line'], 5) == (
        ['long li'],
        {'long line': '\x000\x00ne'})  # yapf: disable
    assert ntelebot.keyboardutil.shorten_lines(['long line', 'long link'], 5) == (
        ['long li'],
        {'long line': '\x000\x00ne', 'long link': '\x000\x00nk'})  # yapf: disable
    assert ntelebot.keyboardutil.shorten_lines(['long line', 'longer line'], 5) == (
        ['longer li', 'long li'],
        {'long line': '\x001\x00ne', 'longer line': '\x000\x00ne'})  # yapf: disable


def test_fix():
    """Run through ntelebot.keyboardutil.fix."""

    keyboard = [
        [{'callback_data': 'short'}],
    ]  # yapf: disable
    assert ntelebot.keyboardutil.fix(keyboard, 5) is None
    assert keyboard == [
        [{'callback_data': 'short'}],
    ]  # yapf: disable

    keyboard = [
        [{'callback_data': 'short'}],
        [{'callback_data': 'long line'}],
        [{'callback_data': 'long link'}],
        [{'callback_data': 'longer line'}],
    ]  # yapf: disable
    assert base64.urlsafe_b64encode(b'longer li\x00long li') == b'bG9uZ2VyIGxpAGxvbmcgbGk='
    assert ntelebot.keyboardutil.fix(keyboard,
                                     5) == '<a href="tg://btn/bG9uZ2VyIGxpAGxvbmcgbGk=">\u200b</a>'
    assert keyboard == [
        [{'callback_data': 'short'}],
        [{'callback_data': '\x001\x00ne'}],
        [{'callback_data': '\x001\x00nk'}],
        [{'callback_data': '\x000\x00ne'}],
    ]  # yapf: disable
