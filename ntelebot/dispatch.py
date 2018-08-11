"""Non-universal, but fairly versatile update dispatcher."""

from __future__ import absolute_import, division, print_function, unicode_literals

import ntelebot


class Dispatcher(object):
    """Non-universal, but fairly versatile update dispatcher."""

    def __init__(self, preprocessor=None):
        self.preprocessor = preprocessor or ntelebot.preprocess.Preprocessor()
        self.callbacks = []

    def __call__(self, bot, update):
        """Preprocess a Telegram Update and dispatch it to a registered handler."""

        ctx = self.preprocessor(bot, update)
        if ctx:
            return self.dispatch(ctx)

    def dispatch(self, ctx):
        """Dispatch a context to a registered handler."""

        for callback, filters in self.callbacks:
            if not filters or filters(ctx):
                return callback(ctx)

    def add(self, callback, filters=None):
        """Add the given callback and set of filters to the dispatch list."""

        self.callbacks.append((callback, filters))

    def add_command(self, name, callback):
        """Catch messages that start with /name."""

        self.add(callback,
                 lambda ctx: ctx.type in ('message', 'callback_query') and ctx.command == name)
