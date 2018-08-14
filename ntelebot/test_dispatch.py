"""Tests for ntelebot.dispatch."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


class MockBot(object):
    # pylint: disable=missing-docstring,too-few-public-methods

    token = 'test:test'

    @staticmethod
    def get_me():
        return {'username': 'username'}


class MockContext(object):  # pylint: disable=missing-docstring,too-few-public-methods
    type = command = None


def test_empty():
    """Verify a dispatcher with no callbacks registered handles (ignores) contexts."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    ctx = MockContext()
    assert dispatcher(ctx) is False


def test_catchall():
    """Verify a dispatcher with a callback with no filter dispatches all contexts."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add(lambda ctx: 'DISPATCHED')
    ctx = MockContext()
    assert dispatcher(ctx) == 'DISPATCHED'


def test_command():
    """Verify the basic /-command filter."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add_command('command', lambda ctx: 'DISPATCHED')
    ctx = MockContext()
    ctx.type = 'message'
    ctx.command = None
    assert dispatcher(ctx) is False
    ctx.command = 'command'
    assert dispatcher(ctx) == 'DISPATCHED'
    ctx.type = 'callback_query'
    assert dispatcher(ctx) == 'DISPATCHED'
    ctx.type = 'inline_query'
    assert dispatcher(ctx) is False


def test_nested_dispatchers():
    """Verify DispatchGroup's basic functionality."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add_command('command', lambda ctx: 'COMMAND')

    subdispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add(subdispatcher)
    subdispatcher.add_command('subcommand', lambda ctx: 'SUBCOMMAND')

    subsubdispatcher = ntelebot.dispatch.Dispatcher()
    subdispatcher.add(subsubdispatcher)
    subsubdispatcher.add_command('subsubcommand', lambda ctx: 'SUBSUBCOMMAND')

    dispatcher.add_command('last', lambda ctx: 'LAST')

    ctx = MockContext()
    ctx.type = 'message'
    assert dispatcher(ctx) is False
    ctx.command = 'command'
    assert dispatcher(ctx) == 'COMMAND'
    ctx.command = 'subcommand'
    assert dispatcher(ctx) == 'SUBCOMMAND'
    ctx.command = 'subsubcommand'
    assert dispatcher(ctx) == 'SUBSUBCOMMAND'
    ctx.command = 'last'
    assert dispatcher(ctx) == 'LAST'


def test_loop_dispatcher():
    """Verify LoopDispatcher works."""

    dispatcher = ntelebot.dispatch.LoopDispatcher()
    bot = MockBot()
    assert dispatcher(bot, {}) is False
    user = {'id': 1000}
    chat = {'id': 1000, 'type': 'private'}
    text = '/command'
    message = {'message_id': 2000, 'chat': chat, 'from': user, 'text': text}
    assert dispatcher(bot, {'message': message}) is False
