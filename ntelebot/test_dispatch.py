"""Tests for ntelebot.dispatch."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


class MockContext(object):  # pylint: disable=missing-docstring,too-few-public-methods
    type = command = None


def test_empty():
    """Verify a dispatcher with no callbacks registered handles (ignores) contexts."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    ctx = MockContext()
    assert dispatcher.dispatch(ctx) is None


def test_catchall():
    """Verify a dispatcher with a callback with no filter dispatches all contexts."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add(lambda ctx: 'DISPATCHED')
    ctx = MockContext()
    assert dispatcher.dispatch(ctx) == 'DISPATCHED'


def test_command():
    """Verify the basic /-command filter."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add_command('command', lambda ctx: 'DISPATCHED')
    ctx = MockContext()
    ctx.type = 'message'
    ctx.command = None
    assert dispatcher.dispatch(ctx) is None
    ctx.command = 'command'
    assert dispatcher.dispatch(ctx) == 'DISPATCHED'
    ctx.type = 'callback_query'
    assert dispatcher.dispatch(ctx) == 'DISPATCHED'
    ctx.type = 'inline_query'
    assert dispatcher.dispatch(ctx) is None
