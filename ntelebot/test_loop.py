"""Tests for ntelebot.loop."""

from __future__ import absolute_import, division, print_function, unicode_literals

import threading
import time

import ntelebot


def test_stop():
    """Verify the looper shuts down in a timely manner."""

    start = time.time()
    loop = ntelebot.loop.Loop()
    threading.Timer(1, loop.stop).start()
    loop.run()
    assert round(time.time() - start) == 1


def test_add():
    """Verify the basic Loop.add -> Bot.get_updates -> Loop.run -> Dispatcher.dispatch flow."""

    updates = [
        {'update_id': 0, 'message': {'text': 'first'}},
        {'update_id': 1, 'message': {'text': 'second'}},
    ]  # yapf: disable

    # pylint: disable=missing-docstring,too-few-public-methods
    class MockBot(object):
        timeout = 3

        @staticmethod
        def get_updates(offset=None, timeout=None):
            _ = timeout
            return [updates[offset or 0]]

    received = []

    class MockDispatcher(object):

        @staticmethod
        def dispatch(unused_bot, update):
            received.append(update)

    loop = ntelebot.loop.Loop()
    loop.add(MockBot(), MockDispatcher())
    threading.Timer(.1, loop.stop).start()
    loop.run()
    assert updates == received
