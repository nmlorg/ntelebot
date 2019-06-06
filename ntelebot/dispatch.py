"""Non-universal, but fairly versatile update dispatcher."""

import inspect

import ntelebot


class Dispatcher(object):
    """A collection of callbacks that can be added together."""

    def __init__(self):
        self.callbacks = []

    def __call__(self, ctx):
        """Dispatch a context to a registered handler."""

        for callback in self.callbacks:
            ret = callback(ctx)
            if ret is not False:
                return ret
        return False

    def _add(self, callback):
        self.callbacks.append(callback)

    def add(self, callback):
        """Add the given callback to the dispatch list."""

        callback = get_callback(callback)
        assert callback
        self._add(callback)

    def add_command(self, name, callback):
        """Catch messages that start with /name."""

        callback = get_callback(callback)
        assert callback
        self._add(lambda ctx: (ctx.type in ('message', 'callback_query') and ctx.command == name and
                               callback(ctx)))  # yapf: disable

    def add_inline(self, prefix, callback):
        """Catch messages sent via inline callbacks (@username) that start with prefix."""

        callback = get_callback(callback)
        assert callback
        if not prefix:
            self._add(lambda ctx: ctx.type == 'inline_query' and callback(ctx))
        else:
            self._add(lambda ctx: (ctx.type == 'inline_query' and ctx.prefix == prefix and
                                   callback(ctx)))  # yapf: disable

    def add_prefix(self, prefix, callback):
        """Catch messages that start with prefix."""

        callback = get_callback(callback)
        assert callback
        self._add(lambda ctx: (ctx.type in ('message', 'callback_query') and
                               ctx.prefix == prefix and callback(ctx)))  # yapf: disable


class LoopDispatcher(Dispatcher):
    """Non-universal, but fairly versatile update dispatcher."""

    def __init__(self, preprocessor=None):
        super(LoopDispatcher, self).__init__()
        self.preprocessor = preprocessor or ntelebot.preprocess.Preprocessor()

    def __call__(self, bot, update):
        """Preprocess a Telegram Update and dispatch it to a registered handler."""

        ctx = self.preprocessor(bot, update)
        if ctx:
            return super(LoopDispatcher, self).__call__(ctx)
        return False


def getargspec(func):  # pylint: disable=missing-docstring
    argspec = inspect.getfullargspec(func)
    return argspec.args, argspec.varargs, argspec.varkw, argspec.defaults, argspec.kwonlyargs


def get_callback(module, recurse=True):  # pylint: disable=too-many-branches,too-many-return-statements
    """Return module if it can be used as a dispatch callback, otherwise try to build one."""

    if not module:
        return

    if isinstance(module, Dispatcher):
        return module

    if inspect.isfunction(module):
        if getargspec(module) == (['ctx'], None, None, None, []):
            return module
        return

    if inspect.ismethod(module):
        if getargspec(module) == (['self', 'ctx'], None, None, None, []):
            return module
        return

    if inspect.isclass(module):
        # In Python 2.7, Class.__init__ is a method, while in 3.6 it is a function.
        if ((inspect.isfunction(module.__init__) or inspect.ismethod(module.__init__)) and
                getargspec(module.__init__) == (['self', 'ctx'], None, None, None, [])):
            return module
        return

    if recurse and inspect.ismodule(module):
        dispatcher = get_callback(getattr(module, 'dispatch', None), recurse=False)
        if dispatcher:
            return dispatcher
        return
