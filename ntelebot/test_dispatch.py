"""Tests for ntelebot.dispatch."""

import types

import ntelebot


class MockBot(ntelebot.bot.Bot):
    # pylint: disable=missing-docstring,too-few-public-methods

    def __init__(self):
        super(MockBot, self).__init__('1234:test')

    @staticmethod
    def __getattr__(k):  # pragma: no cover
        raise AttributeError(k)

    @staticmethod
    def get_me():
        return {'username': 'username'}


class MockContext(object):  # pylint: disable=missing-docstring,too-few-public-methods
    type = prefix = command = None


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


def test_inline():
    """Verify the basic @-inline filter."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add_inline('prefix', lambda ctx: 'PREFIX')
    dispatcher.add_inline(None, lambda ctx: 'DEFAULT')
    ctx = MockContext()
    assert dispatcher(ctx) is False
    ctx.type = 'inline_query'
    assert dispatcher(ctx) == 'DEFAULT'
    ctx.prefix = 'prefix'
    assert dispatcher(ctx) == 'PREFIX'


def test_prefix():
    """Verify the basic prefix filter."""

    dispatcher = ntelebot.dispatch.Dispatcher()
    dispatcher.add_prefix('prefix', lambda ctx: 'PREFIX')
    ctx = MockContext()
    ctx.type = 'message'
    assert dispatcher(ctx) is False
    ctx.prefix = 'prefix'
    assert dispatcher(ctx) == 'PREFIX'


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


def test_dispatch_module():
    """Verify the magic in ntelebot.dispatch.get_callback."""

    def dummy_function():  # pylint: disable=missing-docstring
        pass  # pragma: no cover

    assert ntelebot.dispatch.get_callback(dummy_function) is None

    def dispatch_function(ctx):  # pylint: disable=missing-docstring,unused-argument
        pass  # pragma: no cover

    assert ntelebot.dispatch.get_callback(dispatch_function) is dispatch_function

    class EmptyModule(object):  # pylint: disable=missing-docstring,too-few-public-methods
        pass

    assert ntelebot.dispatch.get_callback(EmptyModule) is None

    class PerUpdateModule(object):  # pylint: disable=missing-docstring,too-few-public-methods

        def __init__(self, ctx):  # pragma: no cover
            pass

    assert ntelebot.dispatch.get_callback(PerUpdateModule) is PerUpdateModule

    class PerDispatcherModule(object):
        # pylint: disable=missing-docstring

        def dispatch(self, ctx):  # pragma: no cover
            pass

        def dummy(self):  # pragma: no cover
            pass

    dispatch_method = PerDispatcherModule().dispatch
    assert ntelebot.dispatch.get_callback(dispatch_method) is dispatch_method
    assert ntelebot.dispatch.get_callback(PerDispatcherModule().dummy) is None

    # In Python 2.7, the module path must be a bytes object, while on 3.6 it must be a unicode.
    # Luckily, __future__.unicode_literals leaves __builtins__.str alone.
    dummy_module = types.ModuleType(str('ntelebot.dummy_module'))
    assert ntelebot.dispatch.get_callback(dummy_module) is None

    dummy_module.dispatch = ntelebot.dispatch.Dispatcher()
    assert ntelebot.dispatch.get_callback(dummy_module) is dummy_module.dispatch  # pylint: disable=no-member
