"""Tests for ntelebot.loop."""

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
    """Verify the basic Loop.add -> Bot.get_updates -> Loop.run -> dispatcher flow."""

    updates = [
        {'update_id': 0, 'message': {'text': 'first'}},
        {'update_id': 1, 'message': {'text': 'second'}},
    ]  # yapf: disable

    class MockBot(object):
        # pylint: disable=missing-docstring,too-few-public-methods

        timeout = 3
        token = 'mock:bot'

        @staticmethod
        def get_updates(offset=None, timeout=None):
            _ = timeout
            return [updates[offset or 0]]

    received = []

    def _dispatch(unused_bot, update):
        received.append(update)

    loop = ntelebot.loop.Loop()
    loop.add(MockBot(), _dispatch)
    threading.Timer(.1, loop.stop).start()
    loop.run()
    assert received == updates


def test_remove():
    """Verify a bot added to a loop stops dispatching updates once its token is removed."""

    updates = [
        {'update_id': 0, 'message': {'text': 'first'}},
        {'update_id': 1, 'message': {'text': 'second'}},
    ]  # yapf: disable

    class MockBot(object):
        # pylint: disable=missing-docstring,too-few-public-methods

        timeout = 3
        token = 'mock:bot'

        @staticmethod
        def get_updates(offset=None, timeout=None):
            _ = timeout
            time.sleep(.1)
            return [updates[offset or 0]]

    received = []

    def _dispatch(unused_bot, update):
        received.append(update)

    loop = ntelebot.loop.Loop()
    bot = MockBot()
    loop.add(bot, _dispatch)

    def _shutdown():
        loop.remove(bot.token)
        time.sleep(.1)
        loop.stop()

    threading.Timer(.15, _shutdown).start()
    loop.run()
    assert received == updates[:1]
