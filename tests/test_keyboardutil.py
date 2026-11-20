"""Tests for ntelebot.keyboardutil."""

import ntelebot


def test_decode():
    """Run through ntelebot.keyboardutil.combine."""

    assert ntelebot.keyboardutil.combine([], 'unencoded text') == 'unencoded text'

    prefixes = ['first string', 'second string']
    assert ntelebot.keyboardutil.combine(prefixes, 'unencoded text') == 'unencoded text'
    assert ntelebot.keyboardutil.combine(prefixes, '\x000\x00suffix') == 'first stringsuffix'
    assert ntelebot.keyboardutil.combine(prefixes, '\x001\x00suffix') == 'second stringsuffix'
    assert ntelebot.keyboardutil.combine(prefixes, '\x002\x00suffix') == '\x002\x00suffix'
    assert ntelebot.keyboardutil.combine(prefixes, '\x00bogus\x00suffix') == '\x00bogus\x00suffix'


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
    assert ntelebot.keyboardutil.fix(keyboard, 5) == ['longer li', 'long li']
    assert keyboard == [
        [{'callback_data': 'short'}],
        [{'callback_data': '\x001\x00ne'}],
        [{'callback_data': '\x001\x00nk'}],
        [{'callback_data': '\x000\x00ne'}],
    ]  # yapf: disable
