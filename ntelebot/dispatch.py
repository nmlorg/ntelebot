"""Non-universal, but fairly versatile update dispatcher."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


class Dispatcher(object):
    """A collection of callbacks that can be added, enabled, and disabled together."""

    enabled = True

    def __init__(self):
        self.callbacks = []

    def __call__(self, ctx):
        """Dispatch a context to a registered handler."""

        if not self.enabled:
            return False
        for callback in self.callbacks:
            ret = callback(ctx)
            if ret is not False:
                return ret
        return False

    def add(self, callback):
        """Add the given callback to the dispatch list."""

        self.callbacks.append(callback)

    def add_command(self, name, callback):
        """Catch messages that start with /name."""

        self.add(lambda ctx: (ctx.type in ('message', 'callback_query') and ctx.command == name and
                              callback(ctx)))  # yapf: disable


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
